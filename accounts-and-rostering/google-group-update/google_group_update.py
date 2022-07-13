import fmrest
import subprocess
import time
import os
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

        activecadets.append(cadet)

    fms.logout()

    print("%s students found." % len(activecadets)) # number in found set

    return activecadets

def addToGroup(cadetEmail, groupEmail):
    print(cadetEmail, groupEmail)

    # capture_output = True
    process = subprocess.run(
        ['/Users/mpauls/bin/gam/gam', 'update', 'group', groupEmail, 'add', 'member', 'allmail', 'user', cadetEmail]
    )

    # input("Press Enter to continue...")
    time.sleep(1) # wait a bit before moving on, don't want to run into API limitations

    return

def updateGroups(activecadets):
#     gam update group <group email> add owner|member|manager [allmail|nomail|daily|digest] [notsuspended]
#   {user <email address> | group <group address> | ou|ou_and_children <org name> | file <file name> | all users}

    for cadet in activecadets:
        if '1' in cadet['Platoon']:
            addToGroup(cadet['SchoolEmail'], '1-platoon@mygya.com')
        elif '2' in cadet['Platoon']:
            addToGroup(cadet['SchoolEmail'], '2-platoon@mygya.com')
        elif '3' in cadet['Platoon']:
            addToGroup(cadet['SchoolEmail'], '3-platoon@mygya.com')
        elif '4' in cadet['Platoon']:
            addToGroup(cadet['SchoolEmail'], '4-platoon@mygya.com')

    for cadet in activecadets:
        if 'A' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'a-group@mygya.com')
        elif 'B' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'b-group@mygya.com')
        elif 'C' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'c-group@mygya.com')
        elif 'D' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'd-group@mygya.com')
        elif 'E' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'e-group@mygya.com')
        elif 'F' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'f-group@mygya.com')
        elif 'G' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'g-group@mygya.com')
        elif 'H' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'h-group@mygya.com')
        elif 'I' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'i-group@mygya.com')
        elif 'J' in cadet['Group']:
            addToGroup(cadet['SchoolEmail'], 'j-group@mygya.com')

updateGroups(filemakerGetActive())