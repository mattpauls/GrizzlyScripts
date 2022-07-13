#from Tkinter import Tk
#from tkFileDialog import askopenfilename
#from tkFileDialog import askdirectory
import os

# Location of GAM
gam = "/Users/mattpauls/bin/gam/gam"

# Ask for directory where we want to upload pictures from
#Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
#folder = askdirectory()
folder = "/Users/mattpauls/Desktop/C47 - Intake Photos RAW/email/4"

# Scan through the directory, pick up all images in it, and upload them to Google Apps.
# Assumes pictures are named with the email address of the student, e.g. doejohn@mygya.com.jpg
for profilepic in os.listdir(folder):
    if profilepic.endswith('.jpg'):
        emailaddr = profilepic[:-4]
        uploadcommand = gam + " user " + emailaddr + " update photo \"" + os.path.realpath(folder) + os.path.sep + profilepic + "\""
        #print uploadcommand
        os.system(uploadcommand)
        print("Uploading profile picture for " + emailaddr)