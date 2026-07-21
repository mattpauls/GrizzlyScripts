"""Push cadet intake photos from GrizzlyDB's S3 bucket to FileMaker.

Uploads the TABEID-keyed photos in S3 (cadets/{tabeid}.jpg, produced by
GrizzlyDB's /admin/photos crop pipeline — key convention defined in
grizzly-db-remix/app/utils/photoKeys.ts) into the CADET::PhotoIntake
container field of a class's FileMaker file. Only fills empty containers —
records that already have a PhotoIntake are left untouched.

Uses the FileMaker Data API (not OData) because it addresses records by
internal recordId, so no SSN-containing compound keys appear in URLs, and
container upload is a documented first-class endpoint. The service account
needs the fmrest extended privilege, and the layout (default CADETAPI) must
include the TABEID, NameFirst, NameLast, and PhotoIntake fields.

Setup: copy .env.example to .env and fill in the values (same FM_* and S3_*
values as grizzly-db-remix). Uses the repo-root .venv; deps are in
requirements.txt.

Usage (from the GrizzlyScripts root):
    .venv/bin/python accounts_and_rostering/push_photos_filemaker/push_photos_to_filemaker.py 56 --dry-run
    .venv/bin/python accounts_and_rostering/push_photos_filemaker/push_photos_to_filemaker.py 56
"""

import argparse
import io
import os
import re
import sys
from pathlib import Path

import boto3
import fmrest
from dotenv import load_dotenv

PHOTO_KEY_RE = re.compile(r"^cadets/(\d+)\.jpg$")


def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(f"Missing required environment variable: {name}")
    return value


def list_s3_photo_tabeids(s3, bucket: str) -> set[int]:
    """Returns the TABEIDs that have a photo at cadets/{tabeid}.jpg."""
    tabeids: set[int] = set()
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix="cadets/"):
        for obj in page.get("Contents", []):
            match = PHOTO_KEY_RE.match(obj["Key"])
            if match:
                tabeids.add(int(match.group(1)))
    return tabeids


def parse_tabeid(value) -> int | None:
    """FM number fields come back as int, float, or '' when empty."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push S3 cadet photos into FileMaker CADET::PhotoIntake"
    )
    parser.add_argument("class_number", type=int, help="Class number, e.g. 56")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be pushed without uploading anything",
    )
    parser.add_argument(
        "--layout",
        default="CADETAPI",
        help="FileMaker layout with TABEID and PhotoIntake (default: CADETAPI)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=int(os.getenv("FM_QUERY_LIMIT", "500")),
        help="Max FileMaker records to fetch (default: FM_QUERY_LIMIT or 500)",
    )
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parent / ".env")

    s3 = boto3.client(
        "s3",
        endpoint_url=get_env("S3_ENDPOINT"),
        aws_access_key_id=get_env("S3_ACCESS_KEY"),
        aws_secret_access_key=get_env("S3_SECRET_KEY"),
        region_name=get_env("S3_REGION"),
    )
    bucket = get_env("S3_BUCKET")

    print("Listing photos in S3...")
    s3_tabeids = list_s3_photo_tabeids(s3, bucket)
    print(f"  {len(s3_tabeids)} photos found under cadets/")

    database = f"edu class {args.class_number}"
    fms = fmrest.Server(
        get_env("FM_BASE_URL"),
        user=get_env("FM_SERVICE_USERNAME"),
        password=get_env("FM_SERVICE_PASSWORD"),
        database=database,
        layout=args.layout,
        api_version="vLatest",
        timeout=60,
    )

    print(f'Logging in to FileMaker ("{database}", layout {args.layout})...')
    fms.login()

    pushed: list[str] = []
    already_has_photo = 0
    no_s3_photo: list[str] = []
    no_tabeid: list[str] = []
    errors: list[str] = []

    try:
        records = list(fms.get_records(limit=args.limit))
        print(f"  {len(records)} FileMaker records fetched")

        # The Data API only returns fields placed on the layout
        required = ("TABEID", "NameLast", "NameFirst", "PhotoIntake")
        missing = [f for f in required if f not in records[0].keys()]
        if missing:
            sys.exit(
                f"Layout {args.layout} is missing field(s) {', '.join(missing)} — "
                "add them to the layout in FileMaker and rerun."
            )

        # A TABEID appearing on multiple records is ambiguous — push to none.
        seen: dict[int, int] = {}
        for record in records:
            tabeid = parse_tabeid(record.TABEID)
            if tabeid is not None:
                seen[tabeid] = seen.get(tabeid, 0) + 1
        duplicates = {t for t, n in seen.items() if n > 1}
        for tabeid in sorted(duplicates):
            errors.append(f"TABEID {tabeid}: on multiple FM records, skipped")

        for record in records:
            name = f"{record.NameLast}, {record.NameFirst}"
            tabeid = parse_tabeid(record.TABEID)

            if tabeid is None:
                no_tabeid.append(name)
                continue
            if tabeid in duplicates:
                continue
            # Populated containers come back as a streaming URL, empty as ""
            if str(record.PhotoIntake or "").strip():
                already_has_photo += 1
                continue
            if tabeid not in s3_tabeids:
                no_s3_photo.append(f"{name} ({tabeid})")
                continue

            label = f"{name} ({tabeid})"
            if args.dry_run:
                print(f"  would push: {label}")
                pushed.append(label)
                continue

            try:
                body = s3.get_object(Bucket=bucket, Key=f"cadets/{tabeid}.jpg")[
                    "Body"
                ].read()
                photo = io.BytesIO(body)
                photo.name = f"{tabeid}.jpg"
                fms.upload_container(record.record_id, "PhotoIntake", photo)
                print(f"  pushed: {label}")
                pushed.append(label)
            except Exception as error:
                errors.append(f"{label}: {error}")
                print(f"  FAILED: {label}: {error}")
    finally:
        fms.logout()

    verb = "Would push" if args.dry_run else "Pushed"
    print("\nSummary")
    print(f"  {verb}: {len(pushed)}")
    print(f"  Already have a photo in FM: {already_has_photo}")
    print(f"  No photo in S3: {len(no_s3_photo)}")
    for entry in sorted(no_s3_photo):
        print(f"    {entry}")
    if no_tabeid:
        print(f"  No TABEID in FM: {len(no_tabeid)}")
        for entry in sorted(no_tabeid):
            print(f"    {entry}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for entry in errors:
            print(f"    {entry}")
        sys.exit(1)


if __name__ == "__main__":
    main()
