import pulumi
from pulumi_azure_native.resources import ResourceGroup
from pulumi_azure_native.web import AppServicePlan, SkuDescriptionArgs

# class AppServicePlanConfig:
#     def __init__(self, name: str, sku_name: str = "P0v4", sku_tier: str = "Premium0V4", kind: str = "app"):
#         self.name = name
#         self.sku_name = sku_name
#         self.sku_tier = sku_tier
#         self.kind = kind

# class AspStack(pulumi.Stack):
#     def __init__(self):
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
# Convert to list of AppServicePlanConfig objects
# app_service_plans = [
#     AppServicePlan(
#         name=item["name"],
#         sku_name=item.get("skuName", "P0v4"),
#         sku_tier=item.get("skuTier", "Premium0V4"),
#         kind=item.get("kind", "app"),
#         resource_name=item["name"],
#         resource_group_name=
#     )
#     for item in app_service_plans
# ]

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

# Validate kinds
for asp in app_service_plans:
    if asp["kind"] not in allowed_kinds:
        raise Exception(
            f"Invalid kind '{asp["kind"]}'. Allowed values are: {', '.join(allowed_kinds)}"
        )

# Dictionary to collect ASP IDs
# id_map = {}

# Create each App Service Plan
for asp in app_service_plans:
    app_service_plan = AppServicePlan(
        resource_name=asp[
            "name"
        ],  # Pulumi resource name can't have hyphens in some cases; adjust if needed
        name=asp["name"],
        resource_group_name=resource_group.name,
        kind=asp["kind"],
        sku=SkuDescriptionArgs(
            name=asp["skuName"],
            tier=asp["skuTier"],
        ),
    )
    asp_dict[asp["name"]] = app_service_plan.id
    # id_map[asp["name] = app_service_plan.id

# Export the map of ASP names to their resource IDs
# self.ids = pulumi.Output.all(id_map).apply(lambda m: m)
