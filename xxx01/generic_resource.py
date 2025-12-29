import pulumi_azure_native.resources as resources

resource_group = resources.ResourceGroup(
    "rgCustom", resource_group_name="rg-custom-res-01"
)

custom_resource = resources.Resource(
    resource_name="id-custom-res-01",
    resource_name_="id-custom-res-01",
    resource_group_name=resource_group.name,
    api_version="2024-11-30",
    resource_provider_namespace="Microsoft.ManagedIdentity",
    resource_type="userassignedidentities",
    properties={"isolationScope": "None"},
    parent_resource_path="",
)
