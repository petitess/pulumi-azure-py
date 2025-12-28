Write-Output $env:resource_id
$PEP_ID = az network private-endpoint-connection list --id $env:resource_id --query "[?properties.privateLinkServiceConnectionState.status == 'Pending'].id | [0]" --output tsv
$PEP_ID
if ($null -ne $PEP_ID) {
    $Approve = az network private-endpoint-connection approve --id $PEP_ID
    Write-Output ($Approve | ConvertFrom-Json | Select-Object name, @{Name = "Status"; Expression = { $_.properties.privateLinkServiceConnectionState.status } })
}
else {
    Write-Output "Nothing to approve"
}
