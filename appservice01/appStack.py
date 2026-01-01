import pulumi
import pulumi_azure_native as azure_native
from pulumi_azure_native import authorization, monitor, network, resources, web
import vnetStack
import aspStack
import pdnszStack
import guid
import rbacRole

config = pulumi.Config("param")
env = config.require("env")
rg_vnet_name = config.require("rgVnetName")
vnet_name = config.require("vnetName")
tags: dict[str, str] = config.require_object("tags")

allowed_ip = "188.150.118.0/24"
prefix = "pulumi"
app_name = f"app-{prefix}-{env}-01"
slot_name = "stagex"
private_ip_address = "10.100.4.7"
private_ip_address_slot = "10.100.4.8"

client_config = authorization.get_client_config()

logs = [
    "AppServiceAntivirusScanAuditLogs",
    "AppServiceHTTPLogs",
    "AppServiceConsoleLogs",
    "AppServiceAppLogs",
    "AppServiceFileAuditLogs",
    "AppServiceAuditLogs",
    "AppServiceIPSecAuditLogs",
    "AppServicePlatformLogs",
    "AppServiceAuthenticationLogs",
]

resource_group = resources.ResourceGroup(
    f"rgApp-{prefix}",
    resource_group_name=f"rg-{prefix}-app-{env}-01",
    tags=tags,
)

app_service = web.WebApp(
    resource_name=f"app-{prefix}",
    name=app_name,
    resource_group_name=resource_group.name,
    tags=tags,
    kind="app",
    public_network_access="Enabled",
    server_farm_id=aspStack.asp_dict[f"asp-{prefix}-{env}-01"],
    virtual_network_subnet_id=(
        vnetStack.snet_dict["snet-app"]
        if "snet-app" in vnetStack.snet_dict
        else pulumi.error("snet-app not found")
    ),
    https_only=True,
    storage_account_required=False,
    identity=web.ManagedServiceIdentityArgs(
        type=web.ManagedServiceIdentityType.SYSTEM_ASSIGNED
    ),
    site_config=web.SiteConfigArgs(
        min_tls_version="1.2",
        health_check_path="/health/index.html",
        vnet_route_all_enabled=True,
        always_on=False,
        ip_security_restrictions=[
            web.IpSecurityRestrictionArgs(
                action="Allow",
                ip_address=allowed_ip,
            )
        ],
    ),
)

web.WebAppApplicationSettings(
    resource_name=f"appsettings-{prefix}",
    resource_group_name=resource_group.name,
    name=app_service.name,
    properties={
        "WEBSITE_TIME_ZONE": "Central European Standard Time",
        "SLOT_NAME": env.upper(),
        "WEBSITE_AUTH_AAD_ALLOWED_TENANTS": client_config.tenant_id,
        "CURRENT_SUBSCRIPTION_ID": client_config.subscription_id,
        "CURRENT_OBJECT_ID": client_config.object_id,
        "CURRENT_CLIENT_ID": client_config.client_id,
        "WEBSITE_RUN_FROM_AZURE_WEBAPP": "true",
        "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET": f"@Microsoft.KeyVault(VaultName=kv-pulumi-{env}-01;SecretName=guid)",
    },
)

web.WebAppSlotConfigurationNames(
    resource_name=f"slotconfig-{prefix}",
    resource_group_name=resource_group.name,
    name=app_service.name,
    app_setting_names=["SLOT_NAME"],
)

web.WebAppFtpAllowed(
    resource_name=f"ftpCred-{prefix}",
    name=app_service.name,
    resource_group_name=resource_group.name,
    allow=True,
)

web.WebAppScmAllowed(
    resource_name=f"scmCred-{prefix}",
    name=app_service.name,
    resource_group_name=resource_group.name,
    allow=True,
)

web.WebAppAuthSettingsV2(
    resource_name=f"authV2-{prefix}",
    name=app_service.name,
    resource_group_name=resource_group.name,
    platform=web.AuthPlatformArgs(enabled=True),
    login=web.LoginArgs(token_store=web.TokenStoreArgs(enabled=True)),
    global_validation=web.GlobalValidationArgs(
        excluded_paths=["/nosecrets/Path"],
        redirect_to_provider="azureactivedirectory",
        require_authentication=True,
        unauthenticated_client_action=web.UnauthenticatedClientActionV2.REDIRECT_TO_LOGIN_PAGE,
    ),
    http_settings=web.HttpSettingsArgs(
        require_https=True,
        routes=web.HttpSettingsRoutesArgs(api_prefix="/.auth"),
        forward_proxy=web.ForwardProxyArgs(
            convention=web.ForwardProxyConvention.NO_PROXY,
        ),
    ),
    identity_providers=web.IdentityProvidersArgs(
        azure_active_directory=web.AzureActiveDirectoryArgs(
            enabled=True,
            is_auto_provisioned=True,
            login=web.AzureActiveDirectoryLoginArgs(disable_www_authenticate=False),
            registration=web.AzureActiveDirectoryRegistrationArgs(
                client_id="123-4fe3-4707-b981-123",
                client_secret_setting_name="MICROSOFT_PROVIDER_AUTHENTICATION_SECRET",
                open_id_issuer=f"https://sts.windows.net/{client_config.tenant_id}/v2.0",
            ),
            validation=web.AzureActiveDirectoryValidationArgs(
                allowed_audiences=["api://123-4fe3-4707-b981-123"]
            ),
        )
    ),
)

slot = web.WebAppSlot(
    resource_name=f"slot-{prefix}",
    name=app_service.name,
    slot=slot_name,
    resource_group_name=resource_group.name,
    tags=tags,
    kind="app",
    public_network_access="Enabled",
    server_farm_id=aspStack.asp_dict[f"asp-{prefix}-{env}-01"],
    virtual_network_subnet_id=(
        vnetStack.snet_dict["snet-app"]
        if "snet-app" in vnetStack.snet_dict
        else pulumi.error("snet-app not found")
    ),
    https_only=True,
    storage_account_required=False,
    identity=web.ManagedServiceIdentityArgs(
        type=web.ManagedServiceIdentityType.SYSTEM_ASSIGNED
    ),
    site_config=web.SiteConfigArgs(
        min_tls_version="1.2",
        health_check_path="/health/index.html",
        vnet_route_all_enabled=True,
        always_on=False,
        ip_security_restrictions=[
            web.IpSecurityRestrictionArgs(
                action="Allow",
                ip_address=allowed_ip,
            )
        ],
    ),
)

web.WebAppApplicationSettingsSlot(
    resource_name=f"appsettings-slot-{prefix}",
    resource_group_name=resource_group.name,
    name=app_service.name,
    slot=slot_name,
    properties={
        "WEBSITE_TIME_ZONE": "Central European Standard Time",
        "SLOT_NAME": env.upper(),
        "WEBSITE_AUTH_AAD_ALLOWED_TENANTS": client_config.tenant_id,
        "CURRENT_SUBSCRIPTION_ID": client_config.subscription_id,
        "CURRENT_OBJECT_ID": client_config.object_id,
        "CURRENT_CLIENT_ID": client_config.client_id,
        "WEBSITE_RUN_FROM_AZURE_WEBAPP": "true",
        "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET": "abc",
    },
    opts=pulumi.ResourceOptions(depends_on=[slot]),
)

# log_settings = [monitor.LogSettingsArgs(category=l, enabled=True) for l in logs]

# monitor.DiagnosticSetting(
#     f"diag-{prefix}",
#     name="diag-app",
#     resource_uri=app_service.id,
#     storage_account_id="<st_id>",
#     logs=log_settings,
# )

pep_prod = network.PrivateEndpoint(
    resource_name=f"pep-{app_name}",
    private_endpoint_name=f"pep-{app_name}",
    custom_network_interface_name=f"nic-{app_name}",
    resource_group_name=resource_group.name,
    subnet=network.SubnetArgs(
        id=(
            vnetStack.snet_dict["snet-pep"]
            if "snet-pep" in vnetStack.snet_dict
            else pulumi.error("snet-pep not found")
        ),
    ),
    private_link_service_connections=[
        network.PrivateLinkServiceConnectionArgs(
            name="config",
            private_link_service_id=app_service.id,
            group_ids=["sites"],
        )
    ],
    ip_configurations=[
        network.PrivateEndpointIPConfigurationArgs(
            name="config",
            group_id="sites",
            member_name="sites",
            private_ip_address=private_ip_address,
        )
    ],
)

network.PrivateDnsZoneGroup(
    resource_name=f"default-{app_name}",
    name="default",
    resource_group_name=resource_group.name,
    private_endpoint_name=pep_prod.name,
    private_dns_zone_group_name="azurewebsites",
    private_dns_zone_configs=[
        network.PrivateDnsZoneConfigArgs(
            name="azurewebsites",
            private_dns_zone_id=pdnszStack.pdnsz_dict["privatelink.azurewebsites.net"],
        )
    ],
)

pep_slot = network.PrivateEndpoint(
    resource_name=f"pep-{app_name}-{slot_name}",
    private_endpoint_name=f"pep-{app_name}-{slot_name}",
    custom_network_interface_name=f"nic-{app_name}-{slot_name}",
    resource_group_name=resource_group.name,
    subnet=network.SubnetArgs(
        id=(
            vnetStack.snet_dict["snet-pep"]
            if "snet-pep" in vnetStack.snet_dict
            else pulumi.error("snet-pep not found")
        ),
    ),
    private_link_service_connections=[
        network.PrivateLinkServiceConnectionArgs(
            name="config",
            private_link_service_id=app_service.id,
            group_ids=[f"sites-{slot_name}"],
        )
    ],
    ip_configurations=[
        network.PrivateEndpointIPConfigurationArgs(
            name="config",
            group_id=f"sites-{slot_name}",
            member_name=f"sites-{slot_name}",
            private_ip_address=private_ip_address_slot,
        )
    ],
    opts=pulumi.ResourceOptions(depends_on=[slot]),
)

network.PrivateDnsZoneGroup(
    resource_name=f"default-{app_name}-{slot_name}",
    name="default",
    resource_group_name=resource_group.name,
    private_endpoint_name=pep_slot.name,
    private_dns_zone_group_name="azurewebsites",
    private_dns_zone_configs=[
        network.PrivateDnsZoneConfigArgs(
            name="azurewebsites",
            private_dns_zone_id=pdnszStack.pdnsz_dict["privatelink.azurewebsites.net"],
        )
    ],
)

if True:
    rbac_kv = authorization.RoleAssignment(
        resource_name=guid.create_guid("rabcKv", app_name),
        role_assignment_name=guid.create_guid("rabcKv", app_name),
        scope=resource_group.id,
        principal_id=app_service.identity.apply(lambda id: id.principal_id),
        principal_type="ServicePrincipal",
        role_definition_id=rbacRole.roleList["KeyVaultAdmin"],
    )
