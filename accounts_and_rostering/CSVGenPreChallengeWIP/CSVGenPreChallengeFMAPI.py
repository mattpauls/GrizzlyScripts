__author__ = 'mattpauls'

import sys
import os
import csv
import random
from unidecode import unidecode
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
import requests

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records # noqa

load_dotenv()

c = Console()

# Set variables
# Update this to the current class number
classNo = str(os.getenv("CLASS_NUMBER"))
outputfolder = os.getenv("DOWNLOADS_FOLDER")
print("Output folder is: " + outputfolder)

# Get the current working directory of this python script
__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))


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


def stu_csv_creator_dict(file_path, header, d):
    with open(file_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        writer.writeheader()

        for row in d:
            writer.writerow(row)


def stucsvwriter(csvfilename, row):
    csvfile = outputfolder + os.path.sep + csvfilename
    stucsv_out = open(csvfile, "a")
    stucsv_out.write(row)
    stucsv_out.close()


def stucsvwriter2(csvfilename, row):
    csvfile = outputfolder + os.path.sep + csvfilename
    w = csv.writer(open(csvfile, "a"))
    w.writerow(row)


def printvalues():
    print("What is in Filemaker?")
    activecadets = filemaker_get_records(query=[{'StatusActive': 'Yes'}])
    for cadet in activecadets:
        print(cadet["NameLast"])
    return


def randNumber() -> int:
    """
    Returns a two-digit random integer that does not include gang-related or other inappropriate numbers.
    """
    exclude = [13, 14, 23, 69]  # exclude certain gang-related numbers etc
    rand = random.randint(10, 99)
    return randNumber() if rand in exclude else rand


def randWord() -> str:
    """
    Returns a random word from the wordlist file, with a minimum character count of 7 and stripped of any trailing whitespace/carriage returns.
    """
    with open(os.path.join(__location__, 'wordlist.txt')) as wordlist:
        word = random.choice(wordlist.readlines())
        word = word.rstrip() # remove any trailing whitespace or carriage returns

        if len(word) >= 7:
            return word
        else:
            return randWord()


def genpassword() -> str:
    """
    Returns a password made up of a random word and random number.
    """
    word = randWord()
    word = word.capitalize()
    password = word + str(randNumber()) + "!"

    return password


def dinopass():
    """
    Returns a password from Dinopass' API that does not include gang-related or other inappropriate numbers.
    As of July 2023, teachers opted to not use this one, the word combinations provided could have double meanings if read a certain way.
    """
    dinopass_url = "https://www.dinopass.com/password/simple"
    exclude = [13, 14, 23, 69]
    password = requests.get(dinopass_url).text
    return dinopass() if int(password[-2:]) in exclude else password


# /Users/mattpauls/Desktop/CSVGen/CSVGen/output/

# Username Generator
def usernamegen():
    """
    Creates a usernames.csv file in the output folder that contains columns needed for importing usernames and passwords into FileMaker.

    Generates usernames that are appropriately formatted for emails and 20 characters or less, and assigns each username with a randomly-generated password.
    """
    filename = "usernames.csv"
    header = "TABEID,last,first,SchoolEmail,SchoolUsername,SchoolEmailPassword,grp,plt\r\n"
    print("Creating file in output folder...")
    stucsvcreator(filename, header)

    print("Generating usernames and passwords...")
    for student in filemaker_get_records(query=[{'StatusActive': 'Yes'}]):
        print("Generating username/password for student: %s, %s" %
              (student["NameLast"], student["NameFirst"]))

        # Set row to NULL, just in case something goes wrong:
        row = None

        # Add stuff in here to strip out Jr. and the ~ stuff
        last = student["NameLast"].split(",")[0]
        lastMod = last.split("-")[0]
        # Split last name on spaces
        lastMod = lastMod.split(" ")
        # If the first part of the last name is 'De', join the rest of the last name together.
        if lastMod[0] == 'De':
            if lastMod[1] == 'La':
                lastMod = ''.join(lastMod)
            else:
                lastMod = ''.join(lastMod[:2])
        # Otherwise, just split on spaces and take the first of the last names
        else:
            lastMod = lastMod[0]

        lastMod = unidecode(lastMod)
        first = student["NameFirst"].split(",")[0]
        firstMod = first.replace("-", "")
        firstMod = firstMod.split(" ")[0]
        firstMod = unidecode(firstMod)

        # Set username equal to the last and first name
        username = lastMod.lower() + firstMod.lower()

        # truncate to 20 characters for AD import
        username = (username[:18]) if len(username) > 18 else username
        username = username + classNo
        email = username + "@mygya.com"
        password = genpassword()

        print(username, password)
        # create the row to write to the file
        row = str(student["TABEID"]) + "," + last + "," + first + "," + email + "," + username + \
            "," + password + "," + student["Group"] + \
            "," + str(student["Platoon"]) + "\r\n"
        stucsvwriter(filename, row)


def moodleimportgen(inputcsv):
    filename = "moodle.csv"
    header = "User ID,Username,Last Name,First Name,Email,Password\r\n"
    print("Creating file in output folder...")
    stucsvcreator(filename, header)

    userid = 1000
    print("Generating file...")
    for studentid, last, first, email, username, password, grp, plt in stucsvreader(inputcsv):

        print(username)
        row = studentid + "," + email + "," + last + "," + \
            first + "," + email + "," + password + "\r\n"
        stucsvwriter(filename, row)

        userid += 1


def pltEndGen(plt):
    if plt == "1":
        ending = "st"
    elif plt == "2":
        ending = "nd"
    elif plt == "3":
        ending = "rd"
    elif plt == "4":
        ending = "th"
    else:
        ending = "ERROR"
    return ending


def createStudentHaparaList(inputcsv):
    filename = "haparaStudentsPlatoons.csv"
    header = "email,class\r\n"
    print("Creating file in output folder...")
    stucsvcreator(filename, header)

    print("Generating file...")
    for studentid, last, first, email, username, password, grp, plt in filemakerexportstucsvreader(inputcsv):
        row = username + "," + plt + \
            pltEndGen(plt) + "-platoon-" + classNo + "\r\n"
        stucsvwriter(filename, row)


def fmpimportgen(inputcsv):
    filename = "fmpimport.csv"
    header = "id,last,first,username,email,password\r\n"
    print("Creating file in output folder...")
    stucsvcreator(filename, header)

    print("Generating file...")
    for studentid, last, first, email, username, password, grp, plt in stucsvreader(inputcsv):

        print(username)
        classname = grp + "group"
        row = studentid + "," + last + "," + first + "," + \
            username + "," + email + "," + password + "\r\n"
        stucsvwriter(filename, row)


def importAD():
    # filename = "adimport.csv"
    # header = "LastName,FirstName,AccountName,AccountPassword,Group,Platoon\r\n"
    # print("Creating file in output folder...")
    # stucsvcreator(filename, header)

    # TODO: add TABEID to employeeID
    print("Generating file...")

    header = ["NameLast", "NameFirst", "SchoolUsername",
              "SchoolEmailPassword", "Group", "Platoon", "TABEID"]
    with open(os.path.join(outputfolder, 'adimport.csv'), 'w') as output_file:
        dict_writer = csv.DictWriter(
            output_file, header, extrasaction='ignore')
        dict_writer.writeheader()
        dict_writer.writerows(filemaker_get_records(
            query=[{'StatusActive': 'Yes'}]))


def importLexia():
    # filename = "adimport.csv"
    # header = "LastName,FirstName,AccountName,AccountPassword,Group,Platoon\r\n"
    # print("Creating file in output folder...")
    # stucsvcreator(filename, header)

    lexia = []

    for student in filemaker_get_records(query=[{'StatusActive': 'Yes'}]):
        if (student["Group"] == "A") or (student["Group"] in "H1") or (student["ELClassification"] == "L"):
            # if student.Group is A or H1 or if ELClassification is "L"
            print(student)

            # have to use 'in' for some reason. Not sure why.
            if student["Group"] in 'H1':
                lexiaClass = "H1 Group"
                print("H1 Class: " + lexiaClass)
            elif student["Group"] == 'A':
                lexiaClass = "A Group"
                print("A Class: " + lexiaClass)
            elif student["ELClassification"] == 'L':
                lexiaClass = "EL Group"
                print("EL Class: " + lexiaClass)
            else:
                print("Something went wrong here.")

            lexiarow = {
                "First Name": "",
                "Last Name": "",
                "Username": "",
                "Password": "",
                "Grade": "",
                "Class": "",
                "School": "",
                "Student Number": ""
            }

            lexiarow["First Name"] = student["NameFirst"]
            lexiarow["Last Name"] = student["NameLast"]
            lexiarow["Username"] = student["SchoolUsername"]
            lexiarow["Password"] = student["SchoolEmailPassword"]
            lexiarow["Grade"] = student["GradeLevel"]
            lexiarow["Class"] = lexiaClass
            lexiarow["School"] = "Grizzly Challenge Charter Sch"
            lexiarow["Student Number"] = student["TABEID"]

            lexia.append(lexiarow)

    # TODO: add TABEID to employeeID
    print("Generating file...")

    # header = ["NameLast", "NameFirst", "SchoolUsername", "SchoolEmailPassword", "Group", "Platoon", "TABEID"]
    header = ["First Name", "Last Name", "Username", "Password",
              "Grade", "Class", "School", "Student Number"]
    # fieldnames = ["NameFirst", "NameLast", "SchoolUsername", "SchoolEmailPassword", "GradeLevel", "Group", ]
    # First Name, Last Name, Username, Password, Grade, Class, School
    with open(os.path.join(outputfolder, 'lexia.csv'), 'w') as output_file:
        dict_writer = csv.DictWriter(
            output_file, header, extrasaction='ignore')
        dict_writer.writeheader()
        dict_writer.writerows(lexia)


def importManga():
    filename = "manga.csv"
    header = "First Name,Last Name,Class Name,User Id,Password,School Id,Mangahigh Ref.\r\n"
    print("Creating file in output folder...")
    stucsvcreator(filename, header)

    print("Generating usernames and passwords...")
    for student in filemaker_get_records(query=[{'StatusActive': 'Yes'}]):
        print("Generating row for student: %s, %s" %
              (student["NameLast"], student["NameFirst"]))
        row = student["NameFirst"] + "," + student["NameLast"] + "," + str(
            classNo) + " - " + student["Group"] + " Group," + student["SchoolUsername"] + "," + student["SchoolEmailPassword"] + "," + "437494" + "," + "\r\n"

        stucsvwriter(filename, row)


def importGrizzlyApp():
    # stuff
    print("TODO")


def importGoGuardianPLT():
    # stuff
    print("TODO")


def importMathspace():
    header = "First name,Last name,Email (optional),Parent email (optional)\r\n"

    print("Generating mathspace...")
    for student in filemaker_get_records(query=[{'StatusActive': 'Yes'}]):
        print("Generating row for student: %s, %s" %
              (student["NameLast"], student["NameFirst"]))
        filename = student["Group"] + " Group Mathspace.csv"

        if Path(outputfolder + os.path.sep + filename).is_file():
            print(outputfolder + os.path.sep + filename)
        else:
            # create file
            print("Creating file in output folder...")
            stucsvcreator(filename, header)

        row = student["NameFirst"] + "," + student["NameLast"] + \
            "," + student["SchoolEmail"] + ",\r\n"

        stucsvwriter(filename, row)


def importGoGuardianPLT():
    header = "email\r\n"

    print("Generating GoGuardian...")
    for student in filemaker_get_records(query=[{'StatusActive': 'Yes'}]):
        print("Generating row for student: %s, %s" %
              (student["NameLast"], student["NameFirst"]))
        filename = student["Platoon"] + "PLT GoGuardian.csv"

        if Path(outputfolder + os.path.sep + filename).is_file():
            print(outputfolder + os.path.sep + filename)
        else:
            # create file
            print("Creating file in output folder...")
            stucsvcreator(filename, header)

        row = student["SchoolEmail"] + "\r\n"

        stucsvwriter(filename, row)


def import_edmentum():
    # First Name,Middle Name,Last Name,User Name,Password,Role,Status,Grade,SIS ID,Federal ID,Email Address,State ID,Gender,Date of Birth,Location,Target Graduation Year,Socio Economic Status,Special Needs,Ethnic Origin,Migrant,Foster Care,Homeless,Armed Forces,Primary Language,Educational Program,AYP Reporting Category,Labor Force,Public Assistance,Disability Status,Rural Residency Status,Primary Learning Reason or Goal for Attending,Secondary Learning Reason or Goal for Attending,Post Secondary Program Enrollment Type,Educator Permissions
    header = ["First Name", "Last Name", "User Name", "Password", "Role",
              "Status", "Grade", "SIS ID", "Email Address", "Gender", "Date of Birth"]

    print("Generating Edmentum...")

    students = filemaker_get_records(query=[{'StatusActive': 'Yes'}])

    # Modify dictionary with new keys:
    for s in students:
        s["First Name"] = s.pop("NameFirst")
        s["Last Name"] = s.pop("NameLast")
        s["User Name"] = s.pop("SchoolUsername")
        s["Password"] = s.pop("SchoolEmailPassword")
        s["Role"] = "learner"
        s["Status"] = "InActive"
        s["Grade"] = s.pop("GradeLevel")
        s["SIS ID"] = s.pop("TABEID")
        s["Email Address"] = s.pop("SchoolEmail")
        s["Gender"] = s.pop("Gender")
        s["Date of Birth"] = s.pop("Birthday")

    # c.print(students)

    filename = "edmentum.csv"
    file_path = os.path.join(outputfolder, filename)

    c.print(f"Creating file {filename} in {outputfolder}")
    stu_csv_creator_dict(file_path, header, students)


def main():
    print("====== CSVGEN ======")
    print("1. Create usernames.csv from Filemaker export. Only do this once!")
    print("2. Create Moodle file.")
    print("3. Create AD import CSV.")
    print("4. Create Student Hapara list (only platoons as classes).")
    print("5. Create FMP import file. NOT USED")
    print("6. Create Lexia import file. NOT USED 1/2023")
    print("7. Create Mangahigh import file. NOT USED 1/2023")
    print("8. Create Mathspace import files. NOT USED 1/2023")
    print("9. Create GoGuardian PLT import files.")
    print("10. Create Edmentum import files. NOT USED AS OF CLASS 51")
    print("0. Exit.")
    print("====================")
    print("\n")
    choice = input(" Choose option: ")

    if choice == "0":
        exit()
    elif choice == "1":
        # inputcsv = tkFileDialog.askopenfilename(title="Choose the export from Filemaker.", filetypes=[('CSV', '*.csv'), ('All files','.*')], message="Choose the export from Filemaker.")
        # inputcsv = easygui.fileopenbox(msg="Choose file", title="Choose", filetypes=["*.csv", "*.mer"], multiple=False)
        # print("Filemaker export is: " + inputcsv)

        usernamegen()
        print("Make sure to modify username CSV so usernames are accurate.")
        main()
    elif choice == "2":
        # inputcsv = tkFileDialog.askopenfilename(title="Choose the generated usernames CSV.", filetypes=[('CSV', '*.csv'), ('All files','.*')], message="Choose the export from Filemaker.")
        inputcsv = easygui.fileopenbox(msg="Choose file", title="Choose", filetypes=[
                                       "*.csv", "*.mer"], multiple=False)
        print("Usernames CSV is: " + inputcsv)

        moodleimportgen(inputcsv)
        main()
    elif choice == "3":
        # inputcsv = tkFileDialog.askopenfilename(title="Choose the generated usernames CSV.", filetypes=[('CSV', '*.csv'), ('All files','.*')], message="Choose the export from Filemaker.")
        # inputcsv = easygui.fileopenbox(msg="Choose file", title="Choose", filetypes=["*.csv", "*.mer"], multiple=False)
        # print("Usernames CSV is: " + inputcsv)

        importAD()
        main()
    elif choice == "4":
        # inputcsv = tkFileDialog.askopenfilename(title="Choose the generated usernames CSV.", filetypes=[('CSV', '*.csv'), ('All files','.*')], message="Choose the export from Filemaker.")
        inputcsv = easygui.fileopenbox(msg="Choose file", title="Choose", filetypes=[
                                       "*.csv", "*.mer"], multiple=False)
        print("Usernames CSV is: " + inputcsv)

        createStudentHaparaList(inputcsv)
        main()
    elif choice == "5":
        # inputcsv = tkFileDialog.askopenfilename(title="Choose the generated usernames CSV.", filetypes=[('CSV', '*.csv'), ('All files','.*')], message="Choose the export from Filemaker.")
        inputcsv = easygui.fileopenbox(msg="Choose file", title="Choose", filetypes=[
                                       "*.csv", "*.mer"], multiple=False)
        print("Usernames CSV is: " + inputcsv)

        fmpimportgen(inputcsv)
        main()
    elif choice == "6":
        # inputcsv = tkFileDialog.askopenfilename(title="Choose the generated usernames CSV.", filetypes=[('CSV', '*.csv'), ('All files','.*')], message="Choose the export from Filemaker.")
        # inputcsv = easygui.fileopenbox(msg="Choose file", title="Choose", filetypes=["*.csv", "*.mer"], multiple=False)
        # print("Usernames CSV is: " + inputcsv)

        importLexia()
        main()
    elif choice == "7":
        importManga()
        main()
    elif choice == "8":
        importMathspace()
        main()
    elif choice == "9":
        importGoGuardianPLT()
        main()
    elif choice == "10":
        import_edmentum()
        main()
    else:
        print("Oops, please try again!")
        main()


# printvalues()
main()
