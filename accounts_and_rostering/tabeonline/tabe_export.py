__author__ = 'mattpauls'

import sys
import os
import csv
import re
from pathlib import Path
import time
# from fabric import Connection
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records  # noqa

c = Console()

load_dotenv()

# Set variables
classNo = str(os.getenv("CLASS_NUMBER"))
outputfolder = os.getenv("OUTPUT_FOLDER")
district_code = os.getenv("DISTRICT_CODE")
school_code = os.getenv("SCHOOL_CODE")
print("Output folder is:", outputfolder)


def stu_csv_creator_dict(file_path, header, d):
    with open(file_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        writer.writeheader()

        for row in d:
            writer.writerow(row)


def export() -> None:
    """
    Generates a file students.csv in the output folder, properly formatted for importing to DRC Insight.
    """
    filename = "TABE_students.csv"
    header = [
    "District Code", "School Code", "Student ID", "Student Last Name", 
    "Student First Name", "Student Middle Initial", "Gender", "Date of Birth", 
    "Ethnicity", "Race - American Indian or Alaskan Native", "Race - Asian", 
    "Race - Black or African American", "Race - Native Hawaiian or Other Pacific Islander", 
    "Race - Caucasian", "Race - Other", "Public Assistance Status", "IEP", "504", 
    "LEP/ELL", "Program", "Additional Program", "ESL Status", "Labor Force Status", 
    "HSE Certificate", "HS Diploma", "Classified Accommodation - Reading", 
    "Classified Accommodation - Mathematics", "Classified Accommodation - Language"
]
    file_path = os.path.join(outputfolder, filename)

    students = filemaker_get_records(query=[{'StatusActive': 'Yes'}])

    # Modify dictionary with new keys
    for s in students:
        c.print(f"Configuring row for {s['NameLast']}, {s['NameFirst']}")
        s["District Code"] = district_code
        s["School Code"] = school_code
        s["Student ID"] = s["TABEID"]
        s["Student Last Name"] = classNo + s["Platoon"] + " " + s.pop("NameLast")
        s["Student First Name"] = s.pop("NameFirst")
        s["Gender"] = s.pop("Gender")
        s["Date of Birth"] = s.pop("Birthday")
        s["Grade"] = s.pop("GradeLevel")
        s["Student_email"] = s.pop("SchoolEmail")

        if s["SpecialEducationIEP"] in ["Yes", "yes"]:
            s["IEP"] = "Y"
        else:
            s["IEP"] = "N"

        # if s["SpecialEducation504"] in ["Yes", "yes"]:
        #     s["504"] = "Y"
        # else:
        #     s["504"] = "N"

    c.print("\n")
    c.print(f"Creating file {filename} in {outputfolder}")
    stu_csv_creator_dict(file_path, header, students)


def main():
    while (True):
        c.print("\n")
        c.rule(title="TABE Online Export")
        c.print("1: Generate TABE export file")
        c.print("2: Exit")

        option = Prompt.ask("Enter your choice:", choices=["1", "2"])

        if option == "1":
            export()
        elif option == "2":
            exit()


if __name__ == "__main__":
    main()
