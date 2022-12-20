import os
import sys
import fmrest
import ldap
from dotenv import load_dotenv
from rich.console import Console

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records

c = Console()

load_dotenv()

def bindAD():
    """"
    Binds to Active Directory and returns LDAP Object.
    """
    Scope = ldap.SCOPE_SUBTREE

    l = ldap.initialize(os.getenv("AD_SERVER"))
    l.simple_bind_s(os.getenv("AD_USERNAME"), os.getenv("AD_PASSWORD"))
    l.set_option(ldap.OPT_REFERRALS, 0)

    return l


def moveUser(ad, user, newLocation):
    if newLocation == "students":
        print(f"Moving {user['samAccountName']} to students OU.")
        userNewDn = "OU=students,DC=GYA,Dc=local"
    elif newLocation == "alumni":
        # TODO possibly create OU if it doesn't exist.
        print(f"Moving {user['samAccountName']} to alumni OU.")
        userNewDn = getAlumniClass(user["samAccountName"])
    elif newLocation == "isp":
        print(f"Moving {user['samAccountName']} isp OU.")
        userNewDn = "OU=isp,DC=GYA,Dc=local"

    ad.rename_s(user["dn"], user["userRdn"], userNewDn) # uncomment to actually make the move.


def getAlumniClass(student: str) -> str:
    """
    Takes a string, expected in the format username49.

    Extracts the class number, and returns a string with where the account should be located in the alumni OU.
    """
    studentClass = student[-2:] # get the class number from the student's username

    if studentClass.isdigit(): # Check if what we got was a number, if so continue, otherwise skip
        alumniOU = "OU=class" + studentClass + ",OU=alumni,DC=gya,DC=local"
        return alumniOU
    else:
        raise ValueError


def searchAD(ad) -> dict:
    """"
    Searches AD isp OU for students and returns a dictionary with student samaccountnames as keys

    Example
    ---------
    {'username48': {'location': 'isp', 'correct_location': '', 'TABEID': '12345', 'dn': 'CN=Student Name,OU=isp,DC=gya,DC=local'}}
    """
    # ad = bindAD() # enable this for testing purposes, normally would be passed this as an argument

    students = {}
    ous_to_search = ["isp", "students"]

    # Handle service accounts, remove them from this list.
    serviceAccounts = [
        "testkid",
        "studentwifi",
        "studentwifi2",
        "ispstudent"
    ]

    for ou in ous_to_search:
        result = ad.search_s(f"ou={ ou }, dc=gya, dc=local", ldap.SCOPE_SUBTREE, "(&(objectClass=user))", ["employeeID", "samaccountname", "cn"])

        for r in result:
            samaccountname = r[1]['sAMAccountName'][0].decode('UTF-8')
            userRdn = "cn=" + r[1]['cn'][0].decode('UTF-8')

            try:
                TABEID = r[1]['employeeID'][0].decode('UTF-8')
            except:
                TABEID = None
            if samaccountname not in serviceAccounts:
                students[samaccountname] = {
                    'location': ou,
                    'correct_location': None,
                    'TABEID': TABEID,
                    'dn': r[0],
                    'userRdn': userRdn,
                    'samAccountName': samaccountname
                    }

    # ad.unbind_s() # uncomment for testing purposes, normally ad would be passed to this function and the unbinding would be handled outside of it.
    # c.print(students) # uncomment for testing

    return students


def find_student_in_ad(ad, student, ad_students):
    # print(student)

    # Check if student exists in Active Directory (search for account)
    samaccountname = "samaccountname=" + student['SchoolUsername']
    r = ad.search_s("dc=GYA, dc=local", ldap.SCOPE_SUBTREE, samaccountname)
    # c.print(samaccountname)
    # c.print(r)

    samaccountname = r[0][1]['sAMAccountName'][0].decode('UTF-8')
    userRdn = "cn=" + r[0][1]['cn'][0].decode('UTF-8')

    try:
        TABEID = r[0][1]['employeeID'][0].decode('UTF-8')
    except:
        TABEID = None

    ad_students[samaccountname] = {
        'location': None,
        'correct_location': None,
        'TABEID': TABEID,
        'dn': r[0][0],
        'userRdn': userRdn,
        'samAccountName': samaccountname
        }

    return ad_students


def processStudents():
    students = filemaker_get_records()
    ad = bindAD()

    ad_students = searchAD(ad)

    school_year_end = os.getenv("SCHOOL_YEAR_END")

    for student in students:
        # print("student is: ", student)
        fm_username = student["SchoolUsername"]

        # add student to ad_students if not already there
        if fm_username and fm_username not in ad_students:
            ad_students = find_student_in_ad(ad, student, ad_students)

        # Check if the student is found in ad_students after processing all students
        # TODO figure out if there are students in ad_students but not in FileMaker (aka orphaned) and move them to alumni as needed
        if fm_username in ad_students:
            # c.print(student)
            # c.print(ad_students[fm_username])

            stu_status = student["StatusActive"]

            if stu_status == "ind st drop" or stu_status in {"no", "No"}:
                # TODO Allow to change password
                # Check if currently in alumni OU
                if "alumni" not in ad_students[fm_username]["dn"]:
                    # move to alumni OU
                    print(f"{fm_username} is dropped and needs to move to alumni.")
                    moveUser(ad, ad_students[fm_username], "alumni")
                # TODO Check if student_status == "no" and if not disabled in AD, disable in AD
                # TODO remove from students group

            # If it's the end of school, and student is in isp or currently active (or inactive), move them to the alumni OU
            # The only exception is if a student is going to be attending ISP next cycle. In that case, move them to the ISP OU
            if school_year_end == "1" and stu_status in {"isp", "yes", "Yes", "no", "No"}:
                if stu_status in {"yes", "Yes"} and student["ISPNextCycle"] in {"yes", "Yes"}:
                    print(f"{fm_username} is in ISP next cycle and needs to be moved to the ISP OU.")
                    moveUser(ad, ad_students[fm_username], "isp")
                else:
                    print(f"{fm_username} needs to move to alumi OU.")
                    moveUser(ad, ad_students[fm_username], "alumni")

            # If it's still school, process students as needed.
            if school_year_end == "0":
                if stu_status in {"yes", "Yes"} and "students" not in ad_students[fm_username]["dn"]:
                    print(f"{fm_username} is an active student and should be in the students OU.")
                    moveUser(ad, ad_students[fm_username], "students")
                elif stu_status in {"isp"} and "isp" not in ad_students[fm_username]["dn"]:
                    print(f"{fm_username} is an active ISP student and should be in the isp OU.")
                    moveUser(ad, ad_students[fm_username], "isp")

    ad.unbind_s()


if __name__ == "__main__":
    processStudents()