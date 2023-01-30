import sys
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records

c = Console()

load_dotenv()

search_fields = ["NameLast", "NameFirst", "SchoolEmail", "SchoolEmailPassword", "AeriesVPC", "AeriesStuID", "HomePhone(?)"]

"""
Email template
To: <<email>>
Reply-to: 
Subject: Aeries Setup Instructions - How to check your grades
Body: 
"Cadet <<last>>,

You can now check your grades online! <a href=""https://drive.google.com/file/d/1Ax2pZyh0-zxkxqM54rIsl9zzQjHZ0zZc/view"">Click here</a> for instructions on how to setup your Aeries account to check your grades. Use the information below to setup your account, but <b>please wait until you are directed by your teacher in Life Skills</b> to follow these directions.

Use this email and password:
email: <<email>>
password: <<password>>

Copy/Paste the following into the Student Verification fields when needed:
Student Permanent ID Number: <<stuID>>
Student Home Telephone Number: <<phone>>
Verification Code: <<vpc>>

Mr. Pauls & Ms. Mauch"

"""



def main():
    while(True):
        c.print("\n")
        c.rule(title="Student Aeries Setup Email Merge")
        c.print("1: Send student Aeries login emails")
        c.print("2: Exit")

        option = Prompt.ask("Enter your choice:", choices=["1", "2"])

        if option == "1":
            print("option 1")
        elif option == "2":
            exit()


if __name__ == "__main__":
    main()