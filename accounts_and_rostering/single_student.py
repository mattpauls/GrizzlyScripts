# - student imported to FM
# 	- blocker: wait for Lita to verify names against birth certs
# - photo input into FM (facecrop.py)
# 	- blocker: wait for Karleskint to take/upload photos
# - generate usernames/passwords (CSVGenPreChallenge)
# 	- blocker: wait for Salcido to send preferred name sheet
# 	- verify against preferred name
# 	- scan passwords - make sure none are weird or inappropriate
# 	- import to FM
# - sync GrizzlyDB
# - rename cropped pics to emails (renameprofilepictures.py)
# - add pic to correct location in Minio for GrizzlyDB
# - create users in AD (powershell command)
# - sync Google users (Google Apps Directory Sync on remote2)
# - update google apps passwords (GAM command)
# - upload profile pic to Google (uploadprofilepic.py)
# - add students to relevant plt/edu Google groups (google_group_update.py)
# - add emails to Chromebook login restrictions
# - create Gmail Google Classroom label and filter for alls students
# - assign Chromebook # (export available CBs from inventory, import to FileMaker)
# - print out Chromebook insert
# - update CadetSharing sheet with current email


# Create user in AD
# Sync Google user
# update apps password


import subprocess
import time
import os
import sys
from google_classroom_label import classroomLabel
from google_group_update import addToGroup

classroomLabel()
addToGroup


# def classroomLabel(cadetEmail):
#     print(f"Setting up Google Classroom label for {cadetEmail}")
#     process = subprocess.run(
#         ['/Users/mpauls/bin/gam/gam', 'user', cadetEmail, 'label', 'Google Classroom']
#     )
#     time.sleep(.05)
#     process = subprocess.run(
#         ['/Users/mpauls/bin/gam/gam', 'user', cadetEmail, 'filter', 'from', 'classroom.google.com', 'label', 'Google Classroom', 'archive' ]
#     )
#     time.sleep(.05)
#     return