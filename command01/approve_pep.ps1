(Test-Path peps.txt) ? (Remove-Item peps.txt) : $Null

(Get-Date).ToString() | Out-File peps.txt -Append
$env:az_sub_id | Out-File peps.txt -Append
$env:az_token | Out-File peps.txt -Append
try {
    $Account = az storage account list --query [].id --output tsv
    # $Func = az functionapp list --query [].id --output tsv
    $Account[0]  | ForEach-Object {
        $PEP_ID = az network private-endpoint-connection list --id $_ --query "[?properties.privateLinkServiceConnectionState.status == 'Pending'].id | [0]" --output tsv
        $PEP_ID | Out-File peps.txt -Append
        if ($null -ne $PEP_ID) {
            $Approve = az network private-endpoint-connection approve --id $PEP_ID 
            Write-Output ($Approve | ConvertFrom-Json | Select-Object name, @{Name = "Status"; Expression = { $_.properties.privateLinkServiceConnectionState.status } })
        }
        else {
            Write-Output "Nothing to approve"
        }
    }
}
catch {

    Write-Host  "ErrorX"
}