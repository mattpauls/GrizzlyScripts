import os
import sys
# sys.path.append('/usr/local/lib/python3.7/site-packages')
import time
import click  # https://click.palletsprojects.com/en/7.x/
import ldap
import ldap.modlist as modlist

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

load_dotenv()
c = Console()

gam = os.getenv("GAM_PATH")
default_password = os.getenv("DEFAULT_PASSWORD")
school_staff_calendar_email = os.getenv("STAFF_CALENDAR_EMAIL")


def bindAD():
    """"
    Binds to Active Directory and returns LDAP Object.
    """
    Scope = ldap.SCOPE_SUBTREE

    l = ldap.initialize(os.getenv("AD_SERVER"))
    l.simple_bind_s(os.getenv("AD_USERNAME"), os.getenv("AD_PASSWORD"))
    l.set_option(ldap.OPT_REFERRALS, 0)

    return l


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
        result = ad.search_s(f"ou={ ou }, dc=gya, dc=local", ldap.SCOPE_SUBTREE, "(&(objectClass=user))", [
                             "employeeID", "samaccountname", "cn"])

        for r in result:
            samaccountname = r[1]['sAMAccountName'][0].decode('UTF-8')
            userRdn = "cn=" + r[1]['cn'][0].decode('UTF-8')

            try:
                TABEID = r[1]['employeeID'][0].decode('UTF-8')
            except:
                TABEID = None
            if samaccountname not in serviceAccounts:
                students[samaccountname] = {
                    'location': ou,
                    'correct_location': None,
                    'TABEID': TABEID,
                    'dn': r[0],
                    'userRdn': userRdn,
                    'samAccountName': samaccountname
                }

    # ad.unbind_s() # uncomment for testing purposes, normally ad would be passed to this function and the unbinding would be handled outside of it.
    # c.print(students) # uncomment for testing

    return students


def processStudents():
    c.print("Processing students...")

    ad = bindAD()

    ad_students = searchAD(ad)

    ad.unbind_s()


def newmilitaryaccount():
    # enter name
    # generate username, verify that the username is what you want
    # ask what department is a part of

    name_first = Prompt.ask("Enter in first name")
    name_last = Prompt.ask("Enter in last name")
    username = Prompt.ask("Enter desired username (Enter to accept generated username)",
                          default=name_first[:1].lower() + name_last.lower())
    print("\n")
    print("Please verify the information below:")
    print("First Name: " + name_first)
    print("Last Name: " + name_last)
    print("Username: " + username)
    print("\n")
    input("Press Enter to continue...")

    department = Prompt.ask("Department", choices=[
        "School", "Headquarters", "Cadre", "Medical", "Logistics", "OAR", "Counseling"])
    input("Press Enter to continue...")

    # create user in correct OU (as disabled and with no password)
    print("Creating user...")

    match department:
        case "School":
            BASE_DN = "OU=teachers,DC=gya,DC=local"
            ad_groups = "CN=teachers," + BASE_DN
        case "Medical":
            BASE_DN = "OU=TMC,OU=Military,OU=Staff,OU=Users,OU=Grizzly,DC=gya,DC=local"
            ad_groups = "CN=TMCgroup," + BASE_DN
        case "Counseling":
            BASE_DN = "OU=counseling,DC=gya,DC=local"
            ad_groups = "CN=counselors," + BASE_DN
        case "OAR":
            BASE_DN = "OU=RPM,DC=gya,DC=local"
            ad_groups = "CN=RPMgroup," + BASE_DN
        case "Headquarters" | "Cadre" | "Logistics":
            BASE_DN = "OU=military,DC=gya,DC=local"
            ad_groups = "CN=militarygroup," + BASE_DN
            # ["MILdb_RW"]

    ad = bindAD()

    # set up password
    # unicode_pass = unicode('\"' + password + '\"', 'iso-8859-1')
    # password_value = unicode_pass.encode('utf-16-le')
    password_value = default_password.encode('utf-16-le')

    # https://gist.github.com/leosouzadias/0f5acd0b70e86f811e25a8fd327db7dc
    # another helpful link http://marcitland.blogspot.com/2011/02/python-active-directory-linux.html
    principal = str(username)+"@mygya.com"

    dn = 'CN='+str(name_first + " " + name_last)+','+str(BASE_DN)
    attrs = {}

    attrs['objectclass'] = [b'top', b'person',
                            b'organizationalPerson', b'user']
    attrs['cn'] = [(name_first + " " + name_last).encode("utf-8")]
    attrs['displayName'] = [(name_first + " " + name_last).encode("utf-8")]
    attrs['name'] = [(name_first + " " + name_last).encode("utf-8")]
    attrs['sn'] = [name_last.encode("utf-8")]
    attrs['givenName'] = [name_first.encode("utf-8")]
    # attrs['userPassword'] = [default_password.encode("utf-8")]

    # attrs['unicodePwd'] = [password_value]
    attrs['userPrincipalName'] = [principal.encode("utf-8")]
    # attrs['userAccountControl'] = [b'512']
    attrs['samaccountname'] = [username.encode("utf-8")]
    attrs['mail'] = [(username + "@mygya.com").encode("utf-8")]
    # attrs['memberOf'] = [ad_groups.encode("utf-8")]

    ldif = modlist.addModlist(attrs)
    ad.add_s(dn, ldif)
    print("User "+str(username)+" added\n Principal="+str(principal))
    time.sleep(10)

    # Set password
    # https://gist.github.com/artschwagerb/35130c93b276d6aa2b05#file-gistfile1-py-L4
    # Probably requires using TLS
    # May want to use passwd_s https://stackoverflow.com/questions/38058966/change-password-with-python-ldap
    new_password = [('\"' + default_password + '\"').encode('utf-16-le')]
    add_pass = [(ldap.MOD_REPLACE, 'unicodePwd', [new_password])]
    ad.modify_s(dn, add_pass)

    # Activate User
    print('Activating user...')
    mod_acct = [(ldap.MOD_REPLACE, 'userAccountControl', '512'.encode('utf-8'))]
    ad.modify_s(dn, mod_acct)
    print('Successfully activated user.')

    # Add user to correct AD group
    # https://stackoverflow.com/questions/51328279/how-to-add-user-to-ldap-group-using-python
    # TODO

    # # gam create user jdoe firstname John lastname Doe password default_password changepassword on org military
    # createuser = gam + " create user " + username + " firstname " + name_first + \
    #     " lastname " + name_last + " password " + \
    #     default_password + " changepassword on org military"
    # os.system(createuser)

    # Add to All Military Staff group in Google Workspace
    print("Adding user to military group...")
    # addmilitarygroup = gam + " update group military add member user " + username
    # os.system(addmilitarygroup)

    ad.unbind_s()
    print("Done!!")


def newteacheraccount():
    print("do teacher stuff here")
    # May want to do this: https://stackoverflow.com/questions/4784775/ldap-query-in-python


def updateteacheraccount():
    username = input("Enter username: ")
    teacher = click.confirm('Is this a teacher?', default=True)

    print('Adding to staff@mygya.com group...')
    os.system(" ".join([gam, 'update group staff add member user', username]))
    if teacher:
        print('Adding to teachers@mygya.com group...')
        os.system(
            " ".join([gam, 'update group teachers add member user', username]))
        print('Adding to Google Classroom group...')
        os.system(
            " ".join([gam, 'update group classroom_teachers add member user', username]))
    print('Adding shared Academic Calendar...')
    os.system(" ".join([gam, 'user', username,
              'add calendar', school_staff_calendar_email, 'selected true']))

    print('Done!')


def main():
    while (True):
        c.print("\n")
        c.rule(title="New User")
        c.print("1. Create military account")
        c.print("2. Create teacher account")
        c.print(
            "3. Update teacher account. (Already created in AD and ran Google Directory Sync)")
        c.print("4. Exit")

        option = Prompt.ask("Enter your choice:", choices=["1", "2", "3", "4"])

        if option == "1":
            newmilitaryaccount()
        elif option == "2":
            newteacheraccount()
        elif option == "3":
            updateteacheraccount()
        elif option == "4":
            exit()


if __name__ == "__main__":
    main()
