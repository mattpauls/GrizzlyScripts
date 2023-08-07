import sys
import os
from rich.console import Console
from rich.prompt import Prompt
import yagmail
import time

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records  # noqa

c = Console()


def generate_body(NameLast, SchoolEmail, SchoolEmailPassword, AeriesVPCCode, AeriesID, Guardian1PhoneHome) -> str:
    return (
        f"<p>Cadet {NameLast},</p>"
        "<p>You can now check your grades online! <a href=""https://drive.google.com/file/d/1Ax2pZyh0-zxkxqM54rIsl9zzQjHZ0zZc/view"">Click here</a> for instructions on how to setup your Aeries account to check your grades. Use the information below to setup your account, but <b>please wait until you are directed by your teacher in Life Skills</b> to follow these directions.</p>"
        "<p>Use this email and password:\n"
        f"email: {SchoolEmail}\n"
        f"password: {SchoolEmailPassword}</p>"
        "<p>Copy/Paste the following into the Student Verification fields when needed:\n"
        f"Student Permanent ID Number: {AeriesID}\n"
        f"Student Home Telephone Number: {Guardian1PhoneHome}\n"
        f"Verification Code: {AeriesVPCCode}</p>"
        "<p>Mr. Pauls & Ms. Mauch</p>"
    )


def send_emails() -> None:
    """
    Gets specified fields from FileMaker for each student record.
    Sends an email to address contained in the SchoolEmail field for each student record found, formatted with generate_body().
    """

    search_fields = ["NameLast", "NameFirst", "SchoolEmail", "SchoolEmailPassword",
                     "AeriesVPCCode", "AeriesID", "Guardian1PhoneHome", "Group"]
    students = filemaker_get_records(
        query=[{'StatusActive': 'Yes'}], fields=search_fields)

    with yagmail.SMTP("noreply@mygya.com") as yag:
        for s in students:
            c.print(
                f"Sending email for {s['SchoolEmail']} in Group {s['Group']}")

            contents = generate_body(
                s["NameLast"],
                s["SchoolEmail"],
                s["SchoolEmailPassword"],
                s["AeriesVPCCode"],
                s["AeriesID"],
                s["Guardian1PhoneHome"]
            )

            yag.send(
                to=s["SchoolEmail"],
                subject="Aeries Setup Instructions - How to check your grades",
                contents=contents
            )

            # Just to be safe, wait a second between executions
            time.sleep(1.5)


def main():
    while (True):
        c.print("\n")
        c.rule(title="Student Aeries Setup Email Merge")
        c.print("1: Send student Aeries login emails")
        c.print("2: Exit")

        option = Prompt.ask("Enter your choice:", choices=["1", "2"])

        if option == "1":
            send_emails()
        elif option == "2":
            exit()


if __name__ == "__main__":
    main()
