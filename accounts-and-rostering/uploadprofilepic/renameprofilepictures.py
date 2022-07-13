# from tkFileDialog import askdirectory
# import Tkinter, tkFileDialog
import os
import csv

# Define CSV Reader
def stucsvreader(filepath):
    stucsv = open(filepath, 'r')
    csv_stucsv = csv.reader(stucsv)
    #next(csv_stucsv) #skips header row
    return csv_stucsv
# End CSV Reader definition

#ask for profile picture name export
#inputcsv = tkFileDialog.askopenfilename(title="Choose the profile picture name export from Filemaker.", filetypes=[('CSV', '*.csv'), ('All files','.*')], message="Choose the profile picture name export from Filemaker.")
inputcsv = "/Users/mattpauls/Downloads/pictures.csv"
picturePath = "/Users/mattpauls/Desktop/C47 - Intake Photos RAW"
print("Filemaker export is: " + inputcsv)


def printvalues(): # for testing purposes
    print("What is in that CSV file:")
    for studentid, email, plt, grp, picName in stucsvreader(inputcsv):
        print(studentid, email, plt, grp, picName)
    return

# Generate 1st, etc based off of the plt the student is a member of.
def pltFolder(plt):
    if plt is "1":
        pltName = "1st"
    elif plt is "2":
        pltName = "2nd"
    elif plt is "3":
        pltName = "3rd"
    elif plt is "4":
        pltName = "4th"
    else:
        pltName = "ERROR"
    return pltName

# Assumes pictures are located in a folder like: /users/matt/desktop/class36intake/1st/cropped/...
# export from filemaker needs to be in order of ssn, email, plt, grp, picName
# for some reason my export didn't have headers. See the CSV reader above if that needs to change.
def renamePictures():
    # print "What is in that CSV file:"
    for studentid, email, plt, grp, picName in stucsvreader(inputcsv):
        # print ssn, email, plt, grp, picName

        # origPicturePath = "/Users/mattpauls/Desktop/C47 - Intake Photos RAW" + os.path.sep + plt + os.path.sep + "cropped" + os.path.sep + picName  # pltFolder(plt)
        origPicturePath = os.path.join(picturePath, plt, "cropped", picName)

        if picName and os.path.isfile(origPicturePath) :

            # origPicturePath = "/Users/mattpauls/Desktop/C40 - Formal Pictures" + os.path.sep + plt + os.path.sep + picName  # pltFolder(plt)
            # newPicturePath = "/Users/mattpauls/Desktop/C47 - Intake Photos RAW/email" + os.path.sep + plt + os.path.sep + email + ".jpg"
            newPicturePath = os.path.join(picturePath, "email", plt, email, ".jpg")

            print("Renaming: " + origPicturePath)
            print("to: " + newPicturePath)
            os.rename(origPicturePath, newPicturePath)
    return


renamePictures()