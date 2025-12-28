## Commands
```as
az login
pulumi new azure-python -y -s dev
pip install -r requirements.txt
pip install pulumi_command
pulumi login --local
pulumi config set azure-native:location swedencentral
pulumi stack init prod
pulumi stack select prod
pulumi stack export
pulumi refresh --yes --neo 
pulumi refresh --yes --neo --target "urn:pulumi:dev::frontdoor01::azure-native:cdn:AFDOrigin::origin-google2"
pulumi refresh --preview-only --neo 
pulumi preview --diff --neo
pulumi up --yes --diff --neo
pulumi state delete <URN>
pulumi destroy --stack prod
```
## Environment variables
```pwsh
$env:PULUMI_CONFIG_PASSPHRASE = "12345678.abc"
$env:AZURE_SUBSCRIPTION_ID = "11111111-1111-1111-1111-111111111111"
$env:AZURE_TENANT_ID       = "22222222-2222-2222-2222-222222222222"  # optional
$env:AZURE_CLIENT_ID       = "..."   # only if using service principal
$env:AZURE_CLIENT_SECRET   = "..."   # only if using service principal
```