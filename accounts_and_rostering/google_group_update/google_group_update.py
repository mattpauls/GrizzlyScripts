import subprocess
import time
import os
import sys

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records


def addToGroup(cadetEmail, groupEmail):
    print(f"Adding { cadetEmail } to { groupEmail }")

    # capture_output = True
    process = subprocess.run(
        ['/Users/mpauls/bin/gam/gam', 'update', 'group', groupEmail, 'add', 'member', 'allmail', 'user', cadetEmail]
    )

    # input("Press Enter to continue...")
    time.sleep(1) # wait a bit before moving on, don't want to run into API limitations

    return


def updateGroups():
    students = filemaker_get_records(query=[{'StatusActive': 'Yes'}])

    for s in students:
        addToGroup(s['SchoolEmail'], str(s['Platoon'])[:1] + '-platoon@mygya.com')
        if s['Group']:
            addToGroup(s['SchoolEmail'], s['Group'][:1].lower() + '-group@mygya.com')


if __name__ == "__main__":
    updateGroups()