Import-Csv -Path "C:\Users\mpauls\Downloads\ADUpdate44to45.csv" | ForEach-Object {
    Write-Host $_.OldUsername
	$studentAD = Get-ADUser -Identity $_.OldUsername -Properties mail,EmployeeID,EmailAddress,Title,SamAccountName,UserPrincipalName
	Write-Host $studentAD.mail
	Write-Host $studentAD.EmailAddress
	Write-Host $studentAD.Title
	Write-Host $studentAD.SamAccountName
	
	$studentAD.mail = $_.SchoolEmail
	$studentAD.EmployeeID = $_.TABEID
	$studentAD.EmailAddress = $_.SchoolEmail
	$studentAD.Title = $_.Platoon
	$studentAD.SamAccountName = $_.SchoolUsername
	$studentAD.UserPrincipalName = $_.SchoolEmail
	#$studentAD.mail = "newmail"
	#$studentAD.EmployeeID = "newTABEID"
	
	#Set-ADUser -Instance $studentAD
    
}