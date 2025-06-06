import subprocess
import time
import os
import sys

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records

def classroomLabel(cadetEmail):
    print(f"Setting up label for {cadetEmail}")
    process = subprocess.run(
        ['/Users/mpauls/bin/gam/gam', 'user', cadetEmail, 'label', 'Google Classroom']
    )
    time.sleep(.05)
    process = subprocess.run(
        ['/Users/mpauls/bin/gam/gam', 'user', cadetEmail, 'filter', 'from', 'classroom.google.com', 'label', 'Google Classroom', 'archive' ]
    )
    time.sleep(.05)
    return

def updateGroups():
    students = filemaker_get_records(query=[{'StatusActive': 'Yes'}])

    for s in students:
        classroomLabel(s['SchoolEmail'])

if __name__ == "__main__":
    updateGroups()