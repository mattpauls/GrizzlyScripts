import os
import fmrest
import getpass
from dotenv import load_dotenv
from rich.console import Console

c = Console()

load_dotenv()


def filemaker_get_records(auth: bool = False, fields: list = None, limit: int = 500, query: dict = None) -> list:
    """Gets records in FileMaker Server.

    Parameters
    ----------
    auth: bool, optional
        A flag used to use interactive login rather than the .env file.
    fields: list, optional
        A list of strings which correspond to records in the FileMaker database.
    query: dict, optional
        An optional list of dicts with a query. Default is to find all records, a query will modify that. Example: [{'StatusActive': 'Yes'}]

    Returns
    -------
    list
        A list of dictionaries, one for each record in FileMaker.
    """

    if auth:
        fms_username = getpass.getuser()

        fms_password = getpass.getpass()
    else:
        fms_username = os.getenv("FMS_USERNAME")
        fms_password = os.getenv("FMS_PASSWORD")

    c.print("Using the following configuration:")
    c.print(f'Username: {fms_username}')
    c.print(f'URL: {os.getenv("FMS_URL")}')
    c.print(f'Database: {os.getenv("FMS_DATABASE")}')
    c.print(f'Layout: {os.getenv("FMS_LAYOUT")}')

    fms = fmrest.Server(os.getenv("FMS_URL"),
        user=fms_username,
        password=fms_password,
        database=os.getenv("FMS_DATABASE"),
        layout=os.getenv("FMS_LAYOUT"),
        api_version='vLatest',
        timeout=30)

    try:
        activecadets = []

        default_fields = [
            "StatusActive",
            "NameLast",
            "NameFirst",
            "TABEID",
            "Group",
            "Platoon",
            "SchoolUsername",
            "SchoolEmail",
            "SchoolEmailPassword",
            "GradeLevel",
            "Gender",
            "Birthday",
            "ISPNextCycle",
            "SpecialEducationIEP"
        ]

        c.print("=============")
        c.print("Attempting to sign in to FileMaker...")
        fms.login()

        # Get records
        if query:
            foundset = fms.find(query, limit=limit)
        else:
            foundset = fms.get_records(limit=limit)

        for record in foundset:
            cadet = {}

            if fields:
                default_fields = fields

            for field in default_fields:
                cadet[field] = getattr(record, field)

            activecadets.append(cadet)

        c.print(f"{ len(activecadets) } students found in FileMaker.")

        return activecadets
    except:
        raise
    finally:
        fms.logout()


if __name__ == "__main__":
    c.print(filemaker_get_records())