import os
import fmrest
from dotenv import load_dotenv
from rich.console import Console

c = Console()

load_dotenv()


def filemaker_get_records(auth: bool = False, fields: list = None) -> list:
    """Gets records in FileMaker Server.

    Parameters
    ----------
    None

    Returns
    -------
    list
        a list of dictionaries, one for each record in FileMaker
    """
    # TODO add option to pass a switch to turn on getpass.getuser() and getpass() instead of using the built-in .env
    # Could also use getpass.getuser() if we wanted.
    # Prompt for FileMaker api password
    # fmpassword = getpass()

    fms = fmrest.Server(os.getenv("FMS_URL"),
        user=os.getenv("FMS_USERNAME"),
        password=os.getenv("FMS_PASSWORD"),
        database=os.getenv("FMS_DATABASE"),
        layout=os.getenv("FMS_LAYOUT"),
        api_version='vLatest')

    try:
        fms.login()

        # Get all records
        foundset = fms.get_records(limit=500)

        activecadets = []

        for record in foundset:
            cadet = {}

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