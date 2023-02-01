__author__ = 'mattpauls'

import sys
import os
import csv
import re
from fabric import Connection
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
    file_path = os.path.join(outputfolder, filename)

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

    c.print("\n")
    c.print(f"Creating file {filename} in {outputfolder}")
    stu_csv_creator_dict(file_path, header, students)


def add_enrollment(e: list, period, stu_id, course) -> list:
    d = {}

    d["School_id"] = 6
    d["Period"] = period
    d["Student_id"] = stu_id
    d["Section_id"] = course

    e.append(d)

    return e

def enrollmentsgen() -> None:
    """
    Generates a file enrollments.csv in the output folder, properly formatted for importing to Clever.
    """

    # Set up enrollments.csv file
    filename = "enrollments.csv"
    file_path = os.path.join(outputfolder, filename)
    header = ["School_id", "Student_id", "Section_id"]

    # Load sections file into memory for processing
    reader = csv.DictReader(open(sectionsFile))
    # Convert read CSV to a list of dictionaries.
    sections = list(reader)

    enrollments = []

    # Load contract class list into memory for processing, if it exists
    with open(contractClassList) as contract_class_reader:
        reader = csv.DictReader(contract_class_reader)
        contract_class_list = list(reader)

    # Get current students from FileMaker
    students = filemaker_get_records(query=[{'StatusActive': 'Yes'}])

    # set up enrollments_list
    e = []

    for s in students:
        # Loop over our list of contract classes, and add any that we found that match student TABEIDs
        for contract_class in contract_class_list:
            if (int(s["TABEID"]) == int(contract_class["TABEID"])):
                c.print(f"Adding student {s['NameLast']}, {s['NameFirst']} with TABEID {s['TABEID']} to contract course {contract_class['Section_id']}")
                e = add_enrollment(e, contract_class["Period"], s["TABEID"], contract_class["Section_id"])

        # Loop over the sections that we loaded from the sections.csv file, and add any that we found that match student TABEIDs
        for section in sections:
            # Grab the first two characters from the section name (formatted like D5English)
            sectionAndPeriod = re.search("(?<=C\d\dS\d)[A-J][1-9]", section["Section_id"])

            # If Section_id is formatted as A1, B3, etc (not Contract1) AND If student group matches this section's group
            if (sectionAndPeriod) and (s["Group"] == section["Section_id"][5:6]):
                # This adds the remainder of the classes the student is enrolled in with their school group to the sections they're enrolled in
                # with the exception of the periods they're already enrolled in a contract class
                if not any(int(d["Student_id"]) == int(s["TABEID"]) and int(d["Period"]) == int(section["Period"]) for d in e):
                    c.print(f"Adding student {s['NameLast']}, {s['NameFirst']} with TABEID {s['TABEID']} to course {section['Section_id']}")
                    e = add_enrollment(e, section["Period"], s["TABEID"], section["Section_id"])

    c.print("\n")
    c.print(f"Creating file {filename} in {outputfolder}")
    stu_csv_creator_dict(file_path, header, e)


def upload_clever():
    c.print("Uploading to Clever...")
    clever_sftp_url = os.getenv("CLEVER_SFTP_URL")
    clever_sftp_username = os.getenv("CLEVER_SFTP_USERNAME")
    clever_sftp_password = os.getenv("CLEVER_SFTP_PASSWORD")

    c = Connection(clever_sftp_url, clever_sftp_username, connect_kwargs={"password": clever_sftp_password})
    #TODO pass file paths and upload
    #TODO move generated files to the correct storage location (rather than just Downloads) and rename previous file as a backup
    c.put('filepathhere')



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
            upload_clever()
        elif option == "4":
            exit()

if __name__ == "__main__":
    main()