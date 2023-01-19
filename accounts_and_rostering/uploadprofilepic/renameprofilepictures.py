import os, sys
import pathlib

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records


#TODO figure out a better way of handling the input of this path.
picturePath = "/Users/mpauls/Desktop/C50 - Intake Photos ORIGINAL"


# Assumes pictures are located in a folder like: /users/matt/desktop/class36intake/1/cropped/...
def renamePictures():

    students = filemaker_get_records(fields=["Platoon", "SchoolEmail", "PhotoPath_calc"])
    for student in students:

        origPicturePath = os.path.join(picturePath, student["Platoon"], "cropped", student["PhotoPath_calc"])

        if student["PhotoPath_calc"] and os.path.isfile(origPicturePath):
            newPlatoonPath = os.path.join(picturePath, "email", student["Platoon"])
            newPicturePath = os.path.join(newPlatoonPath, student["SchoolEmail"] + ".jpg")

            if not os.path.exists(newPlatoonPath):
                print(f"Creating new directory { newPlatoonPath }")
                path = pathlib.Path(newPlatoonPath)
                path.mkdir(parents=True)

            print("Renaming: " + origPicturePath)
            print("to: " + newPicturePath)
            os.rename(origPicturePath, newPicturePath)
    return

if __name__ == "__main__":
    renamePictures()