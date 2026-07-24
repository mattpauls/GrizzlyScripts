"""Upload cadet intake photos from GrizzlyDB's S3 bucket straight to Google.

Reads the TABEID-keyed photos in S3 (cadets/{tabeid}.jpg, produced by
GrizzlyDB's /admin/photos crop pipeline) and, for each one, looks up the
matching cadet's SchoolEmail in FileMaker and runs `gam user <email> update
photo` against the downloaded image. There's no local folder of pre-renamed
files to manage — S3 + FileMaker's TABEID<->SchoolEmail mapping replace the
old rename step entirely (see renameprofilepictures.py / uploadprofilepic.py
for the previous two-step flow).

Setup: uses the same .env as push_photos_filemaker (../push_photos_filemaker/.env)
for FM_* and S3_* values. Uses the repo-root .venv; deps are in
push_photos_filemaker/requirements.txt.

Usage (from the GrizzlyScripts root):
    .venv/bin/python accounts_and_rostering/uploadprofilepic/upload_photos_to_google.py 56 --dry-run
    .venv/bin/python accounts_and_rostering/uploadprofilepic/upload_photos_to_google.py 56
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import boto3
import fmrest
from dotenv import load_dotenv

# Location of GAM
GAM = "/Users/mpauls@mygya.com/bin/gam7/gam"

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
        description="Upload S3 cadet photos to Google profile photos via GAM"
    )
    parser.add_argument("class_number", type=int, help="Class number, e.g. 56")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be uploaded without calling GAM",
    )
    parser.add_argument(
        "--layout",
        default="CADETAPI",
        help="FileMaker layout with TABEID and SchoolEmail (default: CADETAPI)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=int(os.getenv("FM_QUERY_LIMIT", "500")),
        help="Max FileMaker records to fetch (default: FM_QUERY_LIMIT or 500)",
    )
    args = parser.parse_args()

    load_dotenv(
        Path(__file__).resolve().parent.parent / "push_photos_filemaker" / ".env"
    )

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

    uploaded: list[str] = []
    no_s3_photo: list[str] = []
    no_tabeid: list[str] = []
    no_email: list[str] = []
    errors: list[str] = []

    try:
        records = list(fms.get_records(limit=args.limit))
        print(f"  {len(records)} FileMaker records fetched")

        required = ("TABEID", "NameLast", "NameFirst", "SchoolEmail")
        missing = [f for f in required if f not in records[0].keys()]
        if missing:
            sys.exit(
                f"Layout {args.layout} is missing field(s) {', '.join(missing)} — "
                "add them to the layout in FileMaker and rerun."
            )

        # A TABEID appearing on multiple records is ambiguous — upload for none.
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
            if tabeid not in s3_tabeids:
                no_s3_photo.append(f"{name} ({tabeid})")
                continue

            email = str(record.SchoolEmail or "").strip()
            if not email:
                no_email.append(f"{name} ({tabeid})")
                continue

            label = f"{name} ({tabeid}, {email})"
            if args.dry_run:
                print(f"  would upload: {label}")
                uploaded.append(label)
                continue

            try:
                body = s3.get_object(Bucket=bucket, Key=f"cadets/{tabeid}.jpg")[
                    "Body"
                ].read()
                with tempfile.NamedTemporaryFile(suffix=".jpg") as photo_file:
                    photo_file.write(body)
                    photo_file.flush()
                    subprocess.run(
                        [GAM, "user", email, "update", "photo", photo_file.name],
                        check=True,
                    )
                print(f"  uploaded: {label}")
                uploaded.append(label)
            except Exception as error:
                errors.append(f"{label}: {error}")
                print(f"  FAILED: {label}: {error}")
    finally:
        # A long run (many GAM uploads) can outlast the FM Data API token,
        # which only needs to be alive for the initial get_records() above —
        # nothing after that touches FileMaker again. Don't let an expired
        # token on logout hide the summary below.
        try:
            fms.logout()
        except fmrest.exceptions.FileMakerError as error:
            print(f"  (FileMaker logout failed, likely an expired token: {error})")

    verb = "Would upload" if args.dry_run else "Uploaded"
    print("\nSummary")
    print(f"  {verb}: {len(uploaded)}")
    print(f"  No photo in S3: {len(no_s3_photo)}")
    for entry in sorted(no_s3_photo):
        print(f"    {entry}")
    if no_email:
        print(f"  No SchoolEmail in FM: {len(no_email)}")
        for entry in sorted(no_email):
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
