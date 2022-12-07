__author__ = 'mattpauls'

import os
import csv
import fmrest
import re
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

c = Console()

load_dotenv()

# Set variables
classNo = str(os.getenv("CLASS_NUMBER"))
outputfolder = os.getenv("DOWNLOADS_FOLDER")
print("Output folder is:", outputfolder)

contractClassList = os.getenv("CONTRACT_CLASS_SOURCE")
sectionsFile = os.getenv("SECTIONS_SOURCE")
enrollmentsFile = os.getenv("ENROLLMENTS_SOURCE")


def filemakerGetActive() -> dict:
    """
    Returns a dictionary of cadets in FileMaker.
    """

    fms = fmrest.Server(os.getenv("FMS_URL"), 
        user=os.getenv("FMS_USERNAME"), 
        password=os.getenv("FMS_PASSWORD"), 
        database=os.getenv("FMS_DATABASE"), 
        layout=os.getenv("FMS_LAYOUT"),
        api_version="vLatest")

    fms.login()

    find_query = [{'StatusActive': 'Yes'}]
    foundset = fms.find(find_query, limit=os.getenv("FMS_LIMIT"))

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
        cadet["Gender"] = record.Gender
        cadet["Birthday"] = record.Birthday
        cadet["SpecialEducationIEP"] = record.SpecialEducationIEP

        activecadets.append(cadet)

    fms.logout()

    c.print(f"Number of students found: {len(activecadets)}") # number in found set

    return activecadets


# Define CSV Reader for Filemaker raw export. Filemaker does not export headers with the CSV, so don't skip the first line.
def filemakerexportstucsvreader(filepath):
    stucsv = open(filepath, 'rU')
    csv_stucsv = csv.reader(stucsv)
    return csv_stucsv
# End CSV Reader definition


# Define CSV Reader
def stucsvreader(filepath):
    stucsv = open(filepath, 'rU')
    csv_stucsv = csv.reader(stucsv)
    next(csv_stucsv)
    return csv_stucsv
# End CSV Reader definition


def stucsvcreator(csvfilename, headers):
    csvfile = outputfolder + os.path.sep + csvfilename
    stucsv_out = open(csvfile, "w")
    stucsv_out.write(headers)
    stucsv_out.close()


def stucsvwriter(csvfilename, row):
    csvfile = outputfolder + os.path.sep + csvfilename
    stucsv_out = open(csvfile, "a")
    stucsv_out.write(row)
    stucsv_out.close()


def stucsvwriter2(csvfilename, row):
    csvfile = outputfolder + os.path.sep + csvfilename
    w = csv.writer(open(csvfile,"a"))
    w.writerow(row)


def printvalues():
    print("What is in Filemaker?")
    activecadets = filemakerGetActive()
    for cadet in activecadets:
        print(cadet["NameLast"])
    return


#Username Generator
def studentsgen():
    """
    Generates students.csv.
    """
    filename = "students.csv"
    header = "School_id,Student_id,Student_number,Last_name,First_name,Grade,Gender,DOB,IEP_status,Student_email\r\n"
    print("Creating file in output folder...")
    stucsvcreator(filename, header)

    print("Generating students.csv...")
    for student in filemakerGetActive():
        print("Generating row for student: %s, %s" % (student["NameLast"], student["NameFirst"]))

        #Set row to NULL, just in case something goes wrong:
        row = None

        School_id = "6"
        Student_id = str(student["TABEID"])
        Student_number = str(student["TABEID"])
        Last_name = student["NameLast"]
        First_name = student["NameFirst"]
        Grade = str(student["GradeLevel"])
        Gender = student["Gender"]
        DOB = student["Birthday"]
        if student["SpecialEducationIEP"] == "yes":
            IEP_status = "Y"
        else:
            IEP_status = "N"
        Student_email = student["SchoolEmail"]

        row = School_id + "," + Student_id + "," + Student_number + "," + Last_name + "," + First_name + "," + Grade + "," + Gender + "," + DOB + "," + IEP_status + "," + Student_email + "\r\n"
        stucsvwriter(filename, row)


def enrollmentsgen():
    """
    Generates enrollments.csv.
    """
    reader = csv.DictReader(open(sectionsFile))
    sections = list(reader) # Convert read CSV to a list of dictionaries to use later.
    enrollments = []

    with open(enrollmentsFile, 'w') as csvfile:
        fieldnames = ["School_id","Section_id","Student_id"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        students = filemakerGetActive() # get current students from FileMaker

        for student in students:
            print("Working on student: " + student["NameLast"])
            # Initialize a student dictionary object for temporary use
            stuDict = {"TABEID": student["TABEID"], "NameLast": student["NameLast"], "Group": student["Group"], "Sections": {}}
            # Open up the Contract Class CSV
            # TODO skip contract class if not configured in .env
            try:
                contractClassReader = csv.DictReader(open(contractClassList))

                # Contract classes during periods 1-6 take precedence over "regular" classes, so write those into the student dictionary first
                for contractClass in contractClassReader:
                    if (int(student["TABEID"]) == int(contractClass["TABEID"])): # If the student shows up in the contract class list, just add them.
                        stuDict["Sections"][contractClass["Period"]] = contractClass["Section_id"]
            except:
                print("Issue with the contract class reader or data")

            # Loop over the sections that we loaded from the sections.csv file
            for section in sections:
                # Grab the first two characters from the section name (formatted like D5English)
                sectionAndPeriod = re.search("(?<=C\d\dS\d)[A-J][1-9]", section["Section_id"])

                if (sectionAndPeriod) and (student["Group"] == section["Section_id"][5:6]): # If Section_id is formatted as A1, B3, etc (not Contract1) AND If student group matches this section's group
                    if section["Period"] not in stuDict["Sections"]:
                        # This adds the remainder of the classes the student is enrolled in with their school group to the sections they're enrolled in
                        # with the exception of the periods they're already enrolled in a contract class
                        stuDict["Sections"][section["Period"]] = section["Section_id"]
            # Append the temporary student dictionary to the enrollments list
            enrollments.append(stuDict)
        # print(enrollments)

        # Once all the students have been added to the enrollments list, loop over it
        for enrollment in enrollments:
            print(enrollment)
            # For each element in the "Sections" key for each student in the list, write a row to the students.csv file with the school id, student section id, and student id
            for stuSection in enrollment["Sections"]:
                print("Adding Cadet %s in Group %s to Section %s" % (enrollment["NameLast"],enrollment["Group"],enrollment["Sections"][stuSection]))
                writer.writerow({"School_id": 6, "Section_id": enrollment["Sections"][stuSection], "Student_id": enrollment["TABEID"]})


def main():
    while(True):
        c.print("\n")
        c.rule(title="Clever File Generation")
        c.print("1: Generate student file")
        c.print("2: Generate enrollments file")
        c.print("3: Exit")

        option = Prompt.ask("Enter your choice:", choices=["1", "2", "3"])

        if option == "1":
            studentsgen()
        elif option == "2":
            enrollmentsgen()
        elif option == "3":
            exit()

if __name__ == "__main__":
    main()