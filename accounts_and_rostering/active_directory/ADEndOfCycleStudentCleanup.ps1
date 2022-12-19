param(
	[string]$currentClass = $( Read-Host "Enter exiting class number"),
	[string]$SchoolUsernames = $(throw "-SchoolUsernames is required.")
)

# param from https://ss64.com/ps/syntax-args.html

# 
# Grab all users in ISP and move to respective OUs
# https://community.spiceworks.com/topic/1826636-listing-all-users-from-a-specific-ou-using-powershell

Get-ADUser -SearchBase "OU=isp,DC=gya,DC=local" -Filter * | foreach-Object {
    $LastTwo = $_.samaccountname
    $LastTwo = $LastTwo.Substring($LastTwo.Length-2)
    # https://stackoverflow.com/questions/51171410/check-if-string-contains-numeric-value-in-powershell
    if($LastTwo -match "\d\d" -and $LastTwo -ne $currentClass) {
        $alumniOU = "class" + $LastTwo.ToString()
        $alumniOU = "OU=" + $alumniOU + ",OU=alumni,DC=gya,DC=local"
        Move-ADObject -Verbose -Identity $_.ObjectGUID -TargetPath $alumniOU
        Write-Host "Moving object $_ to $alumniOU"
    }
}



# Make sure to exclude the ispstudent user

#Move current class students to alumni OU. Creates OU if not created already.


$classOU = "class" + $currentClass
$alumniOU = "OU=" + $classOU + ",OU=alumni,DC=gya,DC=local"

if (Get-ADOrganizationalUnit -Filter "distinguishedName -eq '$alumniOU'") {
    Write-Host "$alumniOU already exists."
} else {
    Write-Host "Creating OU $alumniOU"
    # Uncomment line below to actally make changes
    New-ADOrganizationalUnit -Name $classOU -Path "OU=alumni,DC=gya,DC=local"
}

Get-ADUser -SearchBase "OU=students,DC=gya,DC=local" -Filter * | foreach-Object {
    $LastTwo = $_.samaccountname
    $LastTwo = $LastTwo.Substring($LastTwo.Length-2)

    if($LastTwo -eq $currentClass) {
        Write-Host "Moving $_ to $alumniOU"
        # Uncomment line below to actally make changes
        Move-ADObject -Verbose -Identity $_.ObjectGUID -TargetPath $alumniOU
    }    
}

# From an export from FileMaker of school usernames (NOT email addresses), move current ISP students to ISP OU

import-csv -Path $SchoolUsernames | ForEach-Object { 
    Write-Host "Processing $_"
    Move-ADObject -Verbose (Get-ADUser -Identity $_.SchoolUsername).distinguishedName -TargetPath 'OU=isp,DC=gya,Dc=local' 
}


write-output "The current class is $currentClass"
write-output "The SchoolUsernames file path is $SchoolUsernames"

Write-Output "IMPORTANT: Be sure to update Google Directory Sync BEFORE running a sync if a new class OU was created!!"