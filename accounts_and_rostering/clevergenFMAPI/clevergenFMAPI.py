__author__ = 'mattpauls'

import sys
import os
import csv
import fmrest
import re
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records

c = Console()

load_dotenv()

# Set variables
classNo = str(os.getenv("CLASS_NUMBER"))
outputfolder = os.getenv("DOWNLOADS_FOLDER")
print("Output folder is:", outputfolder)

contractClassList = os.getenv("CONTRACT_CLASS_SOURCE")
sectionsFile = os.getenv("SECTIONS_SOURCE")
enrollmentsFile = os.getenv("ENROLLMENTS_SOURCE")


def stucsvcreator(csvfilename, headers):
    csvfile = os.path.join(outputfolder, csvfilename)
    stucsv_out = open(csvfile, "w")
    stucsv_out.write(headers)
    stucsv_out.close()


def stucsvwriter(csvfilename, row):
    csvfile = os.path.join(outputfolder, csvfilename)
    stucsv_out = open(csvfile, "a")
    stucsv_out.write(row)
    stucsv_out.close()


def stucsvwriter2(csvfilename, row):
    csvfile = os.path.join(outputfolder, csvfilename)
    w = csv.writer(open(csvfile,"a"))
    w.writerow(row)

def stu_csv_creator_dict(file_path, header, d):
    with open(file_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        writer.writeheader()

        for row in d:
            writer.writerow(row)

#Username Generator
def studentsgen() -> None:
    """
    Generates a file students.csv in the output folder, properly formatted for importing to Clever.
    """
    filename = "students.csv"
    header = ["School_id","Student_id","Student_number","Last_name","First_name","Grade","Gender","DOB","IEP_status","Student_email"]

    students = filemaker_get_records(query=[{'StatusActive': 'Yes'}])

    # Modify dictionary with new keys
    for s in students:
        c.print(f"Configuring row for {s['NameLast']}, {s['NameFirst']}")
        s["School_id"] = 6
        s["Student_id"] = s["TABEID"]
        s["Student_number"] = s.pop("TABEID")
        s["Last_name"] = s.pop("NameLast")
        s["First_name"] = s.pop("NameFirst")
        s["Grade"] = s.pop("GradeLevel")
        s["DOB"] = s.pop("Birthday")
        s["Student_email"] = s.pop("SchoolEmail")

        if s["SpecialEducationIEP"] in ["Yes", "yes"]:
            s["IEP_status"] = "Y"
        else:
            s["IEP_status"] = "N"

    file_path = os.path.join(outputfolder, filename)

    c.print("\n")
    c.print(f"Creating file {filename} in {outputfolder}")
    stu_csv_creator_dict(file_path, header, students)


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

        students = filemaker_get_records(query=[{'StatusActive': 'Yes'}]) # get current students from FileMaker

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