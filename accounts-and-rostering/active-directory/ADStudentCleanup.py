import os
import fmrest
import ldap
from dotenv import load_dotenv
from rich.console import Console

c = Console()

load_dotenv()

def filemakerGetAll():
    """
    Returns list of dictionaries, one for each cadet in FileMaker.
    """
    # Could also use getpass.getuser() if we wanted.
    # Prompt for FileMaker api password
    # fmpassword = getpass()

    fms = fmrest.Server(os.getenv("FMS_URL"), 
    user=os.getenv("FMS_USERNAME"), 
    password=os.getenv("FMS_PASSWORD"), 
    database=os.getenv("FMS_DATABASE"), 
    layout=os.getenv("FMS_LAYOUT"),
    api_version='vLatest')

    fms.login()

    # Get all records
    foundset = fms.get_records(limit=500)

    activecadets = []

    for record in foundset:
        cadet = {
        "NameLast": "",
        "NameFirst": "",
        "TABEID": "",
        "Group": "",
        "Platoon": ""
        }

        cadet["StatusActive"] =  record.StatusActive
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
        cadet["Gender"] = record.Gender
        cadet["Birthday"] = record.Birthday
        cadet["SpecialEducationIEP"] = record.SpecialEducationIEP

        activecadets.append(cadet)

    fms.logout()

    print(f"{ len(activecadets) } students found.")

    return activecadets



def bindAD():
    """"
    Binds to Active Directory and returns LDAP Object.
    """
    Scope = ldap.SCOPE_SUBTREE

    l = ldap.initialize(os.getenv("AD_SERVER"))
    l.simple_bind_s(os.getenv("AD_USERNAME"), os.getenv("AD_PASSWORD"))
    l.set_option(ldap.OPT_REFERRALS, 0)
    # result = l.search_s("dc=GYA, dc=local", ldap.SCOPE_SUBTREE, 'userPrincipalName=mpauls@mygya.com', ['memberOf'])
    # print(result[0][1]['description']) # this will pull out just the description
    # print(result)
    return l

# THIS WORKS (BELOW)
# l.rename_s('cn=testreset,ou=test,dc=GYA,dc=local', 'cn=testreset', 'ou=Grizzly,dc=GYA,dc=local')

# need a function to move a user to a new OU
# ldap.rename_s('cn=UserName,ou=OldContainer,dc=example,dc=com', 'cn=UserName', 'ou=NewContainer,dc=example,dc=com')
def moveUser(ad, username, userCurrentDn, userNewDn):
    ad.rename_s()
    ad.rename_s('cn=testreset,ou=test,dc=GYA,dc=local', 'cn=testreset', 'ou=Grizzly,dc=GYA,dc=local')

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
        result = ad.search_s(f"ou={ ou }, dc=gya, dc=local", ldap.SCOPE_SUBTREE, "(&(objectClass=user))", ["employeeID", "samaccountname"])

        for r in result:
            samaccountname = r[1]['sAMAccountName'][0].decode('UTF-8')
            try:
                TABEID = r[1]['employeeID'][0].decode('UTF-8')
            except:
                TABEID = None
            if samaccountname not in serviceAccounts:
                students[samaccountname] = {
                    'location': ou,
                    'correct_location': None,
                    'TABEID': TABEID,
                    'dn': r[0]
                    }

    # ad.unbind_s() # uncomment for testing purposes, normally ad would be passed to this function and the unbinding would be handled outside of it.
    # c.print(students) # uncomment for testing

    return students

def processStudents():
    students = filemakerGetAll()
    ad = bindAD()

    ad_students = searchAD(ad)

    for student in students:
        print("student is: ", student)

        # Check if student has a username assigned.
        if student['SchoolUsername']:

            # Check if student exists in Active Directory (search for account)
            samaccountname = "samaccountname=" + student['SchoolUsername']
            result = ad.search_s("dc=GYA, dc=local", ldap.SCOPE_SUBTREE, samaccountname)
            print(result)

            if result is None:
                print("student not found in AD")
            # elif len(result) > 1:
            #     print(len(result))
            #     print("somehow we found more than one account with the same samaccountname")
            else:
                print("student was found in AD")
                userCurrentDn = result[0][0]
                print(result[0][1]['cn'][0].decode('UTF-8'))
                userRdn = "cn=" + result[0][1]['cn'][0].decode('UTF-8')
                
                # Process the student

                # Check if the student is assigned to ISP in FileMaker
                if student["StatusActive"] == "isp":
                    print("%s, %s is in independent study" % (student['NameLast'], student['NameFirst']))
                    # Check if student is currently in the ISP OU
                    if "OU=isp" in userCurrentDn:
                        print("student is in ISP in AD, no need to move")
                        # existingAdStudents[student] = {'correct_location': True}
                    # If student is not in the ISP OU, move to the ISP OU
                    else:
                        print("student is not in ISP in AD, need to move student to ISP OU")
                        
                        # Move the student to the ISP OU in Active Directory
                        print("moving student with info: ", userCurrentDn, userRdn, "OU=ISP,DC=GYA,Dc=local")
                        # ad.rename_s(userCurrentDn, userRdn, "OU=ISP,DC=GYA,Dc=local") # uncomment to move students
                
                # Check if the student is an independent study drop
                elif student["StatusActive"] == "ind st drop":
                    print("student is an independent study drop")
                    # Check if student is in correct alumni OU
                    # If student is not in alumni OU, Move student to correct alumni OU
                
                # Check if the student has been dropped from the residential program
                elif student["StatusActive"] == "No":
                    print("Student is inactive")
                    # Disable student, if not already disabled in AD
                    # use userAccountControl property https://stackoverflow.com/questions/13597345/enable-disable-account-programmatically-using-python-ldap-module
                
                # Check if the student is actively in the residential program
                elif student["StatusActive"] == "Yes" or student["StatusActive"] == "yes":
                    print("student is active")
                    # Check if student is disabled, and enable.
                else:
                    print("%s StatusActive has not been coded properly" % student['NameLast'])

                
        # If no username, no use continuing. Can't do much with that.
        else:
            print(print(f"Student {student['NameLast']} does not have a username."))


        print(student)
        break
    # print(existingAdStudents)

    # TODO write logic to check isp and students OUs for student accounts. Build out a list or dictionary with the usernames and TABEIDs found (if any)
    # Load students from the ISP OU, after we've done all the processing above.
    existingAdStudents = searchAD(ad)

    """
    # Loop through found students in the ISP OU
    for ispstudent in existingAdStudents:
        print(ispstudent)
        found = False

        # Loop through the students that we have in FileMaker.
        for student in students:
            # print(student["SchoolUsername"])
            if student["SchoolUsername"] == ispstudent:
                found = True
        
        # If the student in the ISP OU is not found in FileMaker, move them to the correct Alumni OU
        if not found:
            print("didn't find student in ISP OU! Need to move them to the correct alumni OU")
            
            alumniClass = ispstudent[-2:] # get the class number from the student's username
            
            if alumniClass.isdigit(): # Check if what we got was a number, if so continue, otherwise skip
                samaccountname = "samaccountname=" + ispstudent
                # Get account object in AD
                result = ad.search_s("dc=GYA, dc=local", ldap.SCOPE_SUBTREE, samaccountname)
                print("student was found in AD")
                userCurrentDn = result[0][0]
                print(result[0][1]['cn'][0].decode('UTF-8'))
                userRdn = "cn=" + result[0][1]['cn'][0].decode('UTF-8')

                alumniOU = "OU=class" + alumniClass + ",OU=alumni,DC=gya,DC=local"

                print("Moving student %s to %s " % (ispstudent, alumniOU))
                print(userCurrentDn, userRdn, alumniOU)
                ad.rename_s(userCurrentDn, userRdn, alumniOU)
    """

    # Close connection
    ad.unbind_s()

processStudents()