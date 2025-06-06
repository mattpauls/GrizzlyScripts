import os

# Location of GAM
gam = "/Users/mpauls/bin/gam7/gam"

# Ask for directory where we want to upload pictures from
folder = "/Users/mpauls/Downloads/C54 - Intake Candidate Portraits original/email/4"

# Scan through the directory, pick up all images in it, and upload them to Google Apps.
# Assumes pictures are named with the email address of the student, e.g. doejohn@mygya.com.jpg
for profilepic in os.listdir(folder):
    if profilepic.endswith('.jpg') or profilepic.endswith('.JPG'):
        emailaddr = profilepic[:-4]
        uploadcommand = gam + " user " + emailaddr + " update photo \"" + \
            os.path.realpath(folder) + os.path.sep + profilepic + "\""
        # print uploadcommand
        os.system(uploadcommand)
        print("Uploading profile picture for " + emailaddr)
