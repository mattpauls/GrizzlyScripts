import os
import fmrest
import getpass
from dotenv import load_dotenv
from rich.console import Console

c = Console()

load_dotenv()


def filemaker_get_records(auth: bool = False, fields: list = None) -> list:
    """Gets records in FileMaker Server.

    Parameters
    ----------
    auth: bool, optional
        A flag used to use interactive login rather than the .env file.
    fields: list, optional
        A list of strings which correspond to records in the FileMaker database.

    Returns
    -------
    list
        a list of dictionaries, one for each record in FileMaker
    """
    # TODO add option to pass a switch to turn on getpass.getuser() and getpass() instead of using the built-in .env
    # Could also use getpass.getuser() if we wanted.
    # Prompt for FileMaker api password
    # fmpassword = getpass()

    if auth:
        fms_username = getpass.getuser()
        c.print(f'Username: {fms_username}')

        fms_password = getpass.getpass()
    else:
        fms_username = os.getenv("FMS_USERNAME")
        fms_password = os.getenv("FMS_PASSWORD")

    fms = fmrest.Server(os.getenv("FMS_URL"),
        user=fms_username,
        password=fms_password,
        database=os.getenv("FMS_DATABASE"),
        layout=os.getenv("FMS_LAYOUT"),
        api_version='vLatest')

    try:
        fms.login()

        # Get all records
        foundset = fms.get_records(limit=500)

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
            "ISPNextCycle"
        ]

        for record in foundset:
            cadet = {}

            # if fields:
            #     default_fields = fields

            # for field in default_fields:
            #     c.print(field)
            #     cadet[field] = record.field

            cadet["StatusActive"] =  record.StatusActive
            cadet["NameLast"] = record.NameLast
            cadet["NameFirst"] = record.NameFirst
            cadet["TABEID"] = record.TABEID
            cadet["Group"] = record.Group
            cadet["Platoon"] = record.Platoon
            cadet["SchoolUsername"] = record.SchoolUsername
            cadet["SchoolEmail"] = record.SchoolEmail
            cadet["SchoolEmailPassword"] = record.SchoolEmailPassword
            cadet["GradeLevel"] = record.GradeLevel
            cadet["ELClassification"] = record.ELClassification
            cadet["Gender"] = record.Gender
            cadet["Birthday"] = record.Birthday
            cadet["SpecialEducationIEP"] = record.SpecialEducationIEP
            cadet["ISPNextCycle"] = record.ISPNextCycle

            activecadets.append(cadet)

        c.print(f"{ len(activecadets) } students found in FileMaker.")

        return activecadets
    except:
        pass
    finally:
        fms.logout()


if __name__ == "__main__":
    c.print(filemaker_get_records())