import pulumi
import pulumi_azure_native.resources as resources
import pulumi_azure_native as azure_native

config = pulumi.Config("param")
env = config.require("env")
tags = config.require_object("tags")

resource_group = resources.ResourceGroup(
    "rgMain",
    resource_group_name=f"rg-pulumi-main-{env}-01",
    tags=tags,
)

provider_secondary = azure_native.Provider(
    resource_name="sub_secondary",
    subscription_id="00552ad2-c424-41ef-96a3-db1612c7d96c",
    location="WestEurope",
)

resource_group_secondary = resources.ResourceGroup(
    "rgSecondary",
    resource_group_name=f"rg-pulumi-secondary-{env}-01",
    opts=pulumi.ResourceOptions(provider=provider_secondary),
)
