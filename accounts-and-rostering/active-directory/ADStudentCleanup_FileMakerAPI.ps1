param(
	[string]$currentClass = $( Read-Host "Enter current class number")
	#[string]$SchoolUsernames = $(throw "-SchoolUsernames is required.")
)

Import-Module ActiveDirectory 

####################################
$ClassDatabase = Read-Host "Enter class number database to connect to"

####################################
# Get Token
####################################
$Cred = Get-Credential
$Url = "https://fm.mygya.com/fmi/data/vLatest/databases/edu%20class%20$ClassDatabase/sessions"

$secret = Invoke-RestMethod -Method 'Post' -Uri $Url -Credential $Cred -Authentication 'Basic' -ContentType 'application/json' -Body '' # Need to be using Powershell 6 or above

####################################
# Get Students
####################################
$UrlLayout = "https://fm.mygya.com/fmi/data/vLatest/databases/edu%20class%20$ClassDatabase/layouts/CADETAPI/records?_limit=500"

$token = $secret.response.token

$headers = @{Authorization = "Bearer $token"}
$students = Invoke-RestMethod -Method 'Get' -Uri $UrlLayout -Headers $headers -ContentType 'application/json' -Body ''

####################################
# Delete access token
####################################
$UrlSessionDelete = "https://fm.mygya.com/fmi/data/vLatest/databases/edu%20class%20$ClassDatabase/sessions/$token"
Invoke-RestMethod -Method 'Delete' -Uri $UrlSessionDelete -ContentType 'application/json' -Body ''

####################################
# Run 
####################################
$returnedCount = $students.response.dataInfo.returnedCount

Write-Host "Got $returnedCount records."

# Function to create a student user
function New-StudentAD($student) {
    #create student here.
    # import-csv "G:\My Drive\Class 40\C40CadetImport\adgamimport.csv" | foreach-object { New-ADUser -Verbose -Name ($_."NameFirst" + " " + $_."NameLast") -CannotChangePassword $True -Path "OU=students,DC=gya,DC=local" -SamAccountName $_."SchoolUsername" -UserPrincipalName ($_."SchoolUsername" + "@gya.local") -AccountPassword (ConvertTo-SecureString $_."SchoolEmailPassword" -AsPlainText -Force) -EmailAddress ($_."SchoolUsername" + "@mygya.com") -Department $_."Group" -DisplayName ($_."NameFirst" + " " + $_."NameLast") -GivenName $_."NameFirst" -Surname $_."NameLast" -Title $_."Platoon" -Enabled $true -EmployeeID $_."TABEID" -WhatIf ; Add-ADGroupMember -Verbose -Identity "students" -Members $_."SchoolUsername" -WhatIf }
    

    #Create student account
    $studentDetails =@{
        Verbose = $true
        Name = ($student.NameFirst + " " + $student.NameLast)
        #CannotChangePassword = $true
        Path = "OU=students,DC=gya,DC=local"
        SamAccountName = $student.SchoolUsername
        UserPrincipalName = ($student.SchoolUsername + "@mygya.com")
        AccountPassword = (ConvertTo-SecureString -String $student.SchoolEmailPassword -AsPlainText -Force)
        EmailAddress = ($student.SchoolUsername + "@mygya.com")
        Department = $student.Group
        DisplayName = ($student.NameFirst + " " + $student.NameLast)
        GivenName = $student.NameFirst
        Surname = $student.NameLast
        Title = $student.Platoon
        Enabled = $true
        EmployeeID = $student.TABEID
        Whatif = $false
    }
    #New-ADUser -Verbose -Name ($student.NameFirst + " " + $student.NameLast) -CannotChangePassword $True -Path "OU=students,DC=gya,DC=local" -SamAccountName $student.SchoolUsername -UserPrincipalName ($student.SchoolUsername + "@gya.local") -AccountPassword (ConvertTo-SecureString -AsPlainText $student.SchoolEmailPassword -Force) -EmailAddress ($student.SchoolUsername + "@mygya.com") -Department $student.Group -DisplayName ($student.NameFirst + " " + $student.NameLast) -GivenName $student.NameFirst -Surname $student.NameLast -Title $student.Platoon -Enabled $true -EmployeeID $student.TABEID # -Whatif
    New-ADUser @studentDetails -WhatIf
    #Set-ADAccountPassword -Verbose -Identity $student.SchoolUsername -NewPassword (ConvertTo-SecureString -AsPlainText $($student.SchoolEmailPassword) -Force)

    #Add to student group
    Add-ADGroupMember -Verbose -Identity "students" -Members $student.SchoolUsername -Whatif
}

foreach ($student in $students.response.data.fielddata) {
Write-Host "Processing student $($student.NameLast), $($student.NameFirst), status: $($student.StatusActive) with username $($student.SchoolUsername)"
if($student.SchoolUsername) {
        
        # Grab user information from AD
        # Store as variable: https://old.reddit.com/r/PowerShell/comments/4qht5c/help_with_storing_getaduser_output_to_variables/
        try {
            $studentAD = Get-ADUser -Identity $student.SchoolUsername # -Properties * #adding -Properties was causing some issues
        } catch {
            if ($_ -like "*Cannot find an object with identity: '$($student.SchoolUsername)'*") {
                "User '$($student.SchoolUsername)' does not exist."
                #Check if TABEID can be found in AD EmployeeID,if so, update user. If not, create user.
                $studentEmployeeID = Get-ADUser -Filter "EmployeeID -eq $($student.TABEID)"
                if ($studentEmployeeID) {
                    # Found someone who has the same TABEID but different username, which means that the user exists but name has changed
                } else {
                    #create user here.
                    New-StudentAD($student)
                }
        } else {
            "An error occurred: $_"
        }
        continue
        }
        "User '$($studentAD.SamAccountName)' exists."
        # Do stuff with $Result
        
        # Write-Host $student.DistinguishedName
        #Move ISP students from Alumni to ISP OU if not already in ISP
        if($student.StatusActive -eq "isp" -and -Not $studentAD.DistinguishedName.contains("isp")) {
            Write-Host "Moving ISP student to ISP OU..."
            Move-ADObject -Verbose (Get-ADUser -Identity $student.SchoolUsername).distinguishedName -TargetPath 'OU=isp,DC=gya,Dc=local' # -Whatif
        } elseif($student.StatusActive -eq "ind st drop" -and -Not $studentAD.DistinguishedName.contains("alumni")) {
            # Move dropped ISP student to alumni folder if not already in alumni folder
            
            # grab user and move to alumni folder
            $LastTwo = $studentAD.samaccountname
            $LastTwo = $LastTwo.Substring($LastTwo.Length-2) # grabs class number from username
            $classOU = "class" + $LastTwo
            $alumniOU = "OU=" + $classOU + ",OU=alumni,DC=gya,DC=local"

            #Move student to alumni OU
            Write-Host "Moving ISP drop $($student.SchoolUsername) to $alumniOU..."
            Move-ADObject -Verbose -Identity $studentAD.ObjectGUID -TargetPath $alumniOU # -Whatif
        } elseif($student.StatusActive -eq "No" -and $studentAD.Enabled) {
            # Modify Ad object to enabled false
            Write-Host "Disabling inactive student $($student.SchoolUsername)..."
            Disable-ADAccount -Identity $student.SchoolUsername # -Whatif
        } elseif($student.StatusActive -eq "Yes" -and -Not $studentAD.Enabled) {
            # Enable account
            Write-Host "Activating re-joined student $($student.SchoolUsername)..."
            Enable-ADAccount -Identity $student.SchoolUsername # -Whatif
        } elseif($student.StatusActive -eq "Yes" -and -Not $studentAD.DistinguishedName.contains("students")) {
            # Move student to OU students if active but not in correct OU
            Write-Host "Moving active student to students OU: $($student.SchoolUsername)..."
            Move-ADObject -Verbose -Identity $studentAD.ObjectGUID -TargetPath "OU=students,DC=gya,DC=local" # -Whatif
        }


}
}
#####################################
# Stuff below is from original.
<#
$csv | ForEach-Object { 
    Write-Host "Processing $($_.SchoolUsername), status: $($_.StatusActive)"
    #Write-Host $_
    #Write-Host $_.SchoolUsername
    #Write-Host $_.StatusActive
    if($_.SchoolUsername) {
        
        # Grab user information from AD
        # Store as variable: https://old.reddit.com/r/PowerShell/comments/4qht5c/help_with_storing_getaduser_output_to_variables/
        $student = Get-ADUser -Identity $_.SchoolUsername -Properties *
        # Write-Host $student.DistinguishedName
        #Move ISP students from Alumni to ISP OU if not already in ISP
        if($_.StatusActive -eq "isp" -and -Not $student.DistinguishedName.contains("isp")) {
            Write-Host "Moving ISP student to ISP OU..."
            Move-ADObject -Verbose (Get-ADUser -Identity $_.SchoolUsername).distinguishedName -TargetPath 'OU=isp,DC=gya,Dc=local'# -WhatIf
        } elseif($_.StatusActive -eq "ind st drop" -and -Not $student.DistinguishedName.contains("alumni")) {
            # Move dropped ISP student to alumni folder if not already in alumni folder
            
            # grab user and move to alumni folder
            $LastTwo = $student.samaccountname
            $LastTwo = $LastTwo.Substring($LastTwo.Length-2) # grabs class number from username
            $classOU = "class" + $LastTwo
            $alumniOU = "OU=" + $classOU + ",OU=alumni,DC=gya,DC=local"

            #Move student to alumni OU
            Write-Host "Moving ISP drop $_.SchoolUsername to $alumniOU..."
            Move-ADObject -Verbose -Identity $student.ObjectGUID -TargetPath $alumniOU# -WhatIf
        } elseif($_.StatusActive -eq "No" -and $student.Enabled) {
            # Modify Ad object to enabled false
            Write-Host "Disabling inactive student $_.SchoolUsername..."
            Disable-ADAccount -Identity $_.SchoolUsername# -WhatIf
        } elseif($_.StatusActive -eq "Yes" -and -Not $student.Enabled) {
            # Enable account
            Write-Host "Activating re-joined student $_.SchoolUsername..."
            Enable-ADAccount -Identity $_.SchoolUsername# -WhatIf
        } elseif($_.StatusActive -eq "Yes" -and -Not $student.DistinguishedName.contains("students")) {
            # Move student to OU students if active but not in correct OU
            Write-Host "Moving active student to students OU $_.SchoolUsername..."
            Move-ADObject -Verbose -Identity $student.ObjectGUID -TargetPath "OU=students,DC=gya,DC=local"# -WhatIf
        }





        # Get current OU of user in Active Directory, just give me the top-level though please.
        #$OU = ($student.DistinguishedName -split ",")[1].replace("OU=","") #gives teachers
        #Write-Host $OU


    }
    

    # Move-ADObject -Verbose (Get-ADUser -Identity $_.SchoolUsername).distinguishedName -TargetPath 'OU=isp,DC=gya,Dc=local' 
}
#>
#End of process
# iterate over ISP OU
# move back to alumni if doesn't match CSV=isp or record doesn't exist at all
# Make sure to exclude the ispstudent user

$adISPstudents = Get-ADUser -SearchBase "OU=isp,DC=gya,DC=local" -Filter *
Write-Host "==============================================="
Write-Host "Now moving orphaned ISP students back to alumni"
Write-Host "==============================================="

Compare-Object -ReferenceObject $adISPstudents.samaccountname -DifferenceObject $students.response.data.fielddata.SchoolUsername -passThru | ForEach-Object { 
    if($_) { 
        # Write-Host "Processing $($_)" #uncomment to show on screen.
        # Move found account to respective alumni folder
        $LastTwo = $_ # Get-ADUser -Identity $_ -Properties samaccountname
        $LastTwo = $LastTwo.Substring($LastTwo.Length-2)
    
        # https://stackoverflow.com/questions/51171410/check-if-string-contains-numeric-value-in-powershell
        if($LastTwo -match "\d\d" -and -Not $currentClass) {
            $alumniOU = "class" + $LastTwo.ToString()
            $alumniOU = "OU=" + $alumniOU + ",OU=alumni,DC=gya,DC=local"
            $wrongplace = Get-ADUser -Identity $_ -Properties samaccountname
            Move-ADObject -Verbose -Identity $wrongplace -TargetPath $alumniOU # -Whatif
            Write-Host "Moving object $_ to $alumniOU"
        } 
    } 
}

# Clean up
# Remove Temp file created
#Remove-Item $TempCSV.FullName