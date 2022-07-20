import os
import fmrest
from dotenv import load_dotenv

load_dotenv()

def filemakerGetActive():
    """
    Returns a dictionary of cadets in FileMaker.
    """

    fms = fmrest.Server(os.getenv("FMS_URL"), 
    user=os.getenv("FMS_USERNAME"), 
    password=os.getenv("FMS_PASSWORD"), 
    database=os.getenv("FMS_DATABASE"), 
    layout=os.getenv("FMS_LAYOUT"))

    fms.login()

    find_query = [{'StatusActive': 'Yes'}]
    foundset = fms.find(find_query, limit=500)

    global activecadets # oooh why did I use global!?
    activecadets = []

    for record in foundset:
        cadet = {
        "NameLast": "",
        "NameFirst": "",
        "TABEID": "",
        "Group": "",
        "Platoon": ""
        }
        
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
        cadet["PhotoPath_calc"] = record.PhotoPath_calc

        activecadets.append(cadet)

    fms.logout()

    print("%s students found." % len(activecadets)) # number in found set

    return activecadets

#TODO figure out a better way of handling the input of this path.
picturePath = "/Users/mpauls/Desktop/C49 - Intake Portraits"


# Assumes pictures are located in a folder like: /users/matt/desktop/class36intake/1/cropped/...
def renamePictures():

    students = filemakerGetActive()

    for student in students:

        origPicturePath = os.path.join(picturePath, student["Platoon"], "cropped", student["PhotoPath_calc"])

        if student["PhotoPath_calc"] and os.path.isfile(origPicturePath):

            #TODO check if directory "email" exists and create it if it does not.
            newPicturePath = os.path.join(picturePath, "email", student["Platoon"], student["SchoolEmail"] + ".jpg")

            print("Renaming: " + origPicturePath)
            print("to: " + newPicturePath)
            os.rename(origPicturePath, newPicturePath)
    return


renamePictures()