import pulumi
import pulumi_command.local as local
import pulumi_azure_native.authorization as authorization
import datetime
import os

date = datetime.datetime.now()
sub_id = authorization.get_client_config().subscription_id
token = authorization.get_client_token().token

if not pulumi.runtime.is_dry_run() or pulumi.runtime.is_dry_run():
    azurecli = local.Command(
        resource_name="azure_cli",
        create=""
        "pwsh -Command az account show --output json; "
        "(Get-Service -Name W32Time)"
        "",
        update=""
        "pwsh -Command az account show --output json; "
        "(Get-Service -Name W32Time)"
        "",
    )

approve_pep = local.Command(
    resource_name="approve_pep",
    create="pwsh -File ./approve_pep.ps1",
    update="pwsh -File ./approve_pep.ps1",
    triggers=[f"{date}"],
    environment={"az_sub_id": sub_id, "az_token": token[0:35]},
    logging=local.Logging.STDOUT_AND_STDERR,
    asset_paths=["peps.txt"],
)

peps_asset = approve_pep.assets.apply(lambda assets: assets.get("peps.txt"))


def read_lines(asset: pulumi.asset.FileAsset):
    if asset is None:
        return []
    with open(asset.path, "r") as f:
        return [line.strip() for line in f]


peps_lines = peps_asset.apply(read_lines)
# peps_lines.apply(lambda lines: [print("A", line) for line in lines])
pulumi.export("peps_lines", peps_lines)
