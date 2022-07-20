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
        addToGroup(cadet['SchoolEmail'], str(cadet['Platoon'])[:1] + '-platoon@mygya.com')
        if cadet['Group']:
            addToGroup(cadet['SchoolEmail'], cadet['Group'][:1].lower() + '-group@mygya.com')

updateGroups(filemakerGetActive())