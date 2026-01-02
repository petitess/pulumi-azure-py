import pulumi
from pulumi_azure_native.resources import ResourceGroup
from pulumi_azure_native.web import AppServicePlan, SkuDescriptionArgs
from pulumi_azure_native import web

config = pulumi.Config("param")
env = config.require("env")
tags: dict[str, str] = config.require_object("tags")
app_service_plans: list[dict] = config.require_object("appServicePlans")
asp_dict = {}

resource_group = ResourceGroup(
    "rgAsp",
    resource_group_name=f"rg-pulumi-asp-{env}-01",
    tags=tags,
)

allowed_kinds = {
    "app",
    "app,linux",
    "app,linux,container",
    "hyperV",
    "app,container,windows",
    "app,linux,kubernetes",
    "app,linux,container,kubernetes",
    "functionapp",
    "functionapp,linux",
    "functionapp,linux,container,kubernetes",
    "functionapp,linux,kubernetes",
}

for asp in app_service_plans:
    if asp["kind"] not in allowed_kinds:
        raise Exception(
            f"Invalid kind '{asp["kind"]}'. Allowed values are: {', '.join(allowed_kinds)}"
        )

for asp in app_service_plans:
    app_service_plan = AppServicePlan(
        resource_name=asp["name"],
        name=asp["name"],
        resource_group_name=resource_group.name,
        reserved=True if asp["kind"].find("functionapp") != -1 else False,
        kind=asp["kind"],
        sku=SkuDescriptionArgs(
            name=asp["skuName"],
            tier=asp["skuTier"],
        ),
    )
    asp_dict[asp["name"]] = app_service_plan.id
