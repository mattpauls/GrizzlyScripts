# Disable AD account
# Remove student from email groups in Google Admin
# Run GSuite Cloud Sync (on remote2.gya.local)
# Update Clever with students.csv

import os
import ldap
from ldap import modlist
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
console = Console()

# Location of GAM
gam = "/Users/mpauls/bin/gam/gam"

# TODO add feature to search Filemaker for student,
# return username/plt/group/StatusActive to reference or choose to disable


def bindAD():
    Scope = ldap.SCOPE_SUBTREE

    ad = ldap.initialize(os.getenv("AD_SERVER"))
    ad.simple_bind_s(os.getenv("AD_USERNAME"), os.getenv("AD_PASSWORD"))
    ad.set_option(ldap.OPT_REFERRALS, 0)
    # result = l.search_s("dc=GYA, dc=local", ldap.SCOPE_SUBTREE, 'userPrincipalName=mpauls@mygya.com', ['memberOf'])
    # print(result[0][1]['description']) # this will pull out just the description
    # print(result)
    return ad


ad = bindAD()

student_username = input("Enter cadet username or email to disable:")
student_username = student_username.split("@")[0]

samaccountname = "samaccountname=" + student_username
# Get account object in AD
result = ad.search_s("dc=GYA, dc=local", ldap.SCOPE_SUBTREE,
                     samaccountname)  # TODO move base to .env
# console.print(result[0][1]["userAccountControl"][0])
if result[0][0] is not None:
    print("student was found in AD")
    # returns b'512' for active user
    userAccountControl = result[0][1]["userAccountControl"][0]
    print(userAccountControl)

    dn = result[0][0]
    print(dn)

    # Setup modlist
    mod = modlist.modifyModlist({'userAccountControl': [b'512']}, {
                                'userAccountControl': [b'514']})

    # TODO then, modify the userAccountControl to be 514 for disabled, if not already disabled
    # as outlined here https://stackoverflow.com/questions/13597345/enable-disable-account-programmatically-using-python-ldap-module
    # probably use the LDAPObject.modify(dn, modlist) https://www.python-ldap.org/en/python-ldap-3.4.3/reference/ldap.html#ldapobject-classes

    # add try: catch: for insufficient permissions
    ad.modify_s(dn, mod)

    # Remove Google Groups
    remove_groups_cmd = gam + " user " + student_username + " delete groups"
    # print uploadcommand
    os.system(remove_groups_cmd)


else:
    print("student was not found in AD")

# Close connection
ad.unbind_s()
