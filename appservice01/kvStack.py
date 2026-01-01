import pulumi
import pulumi_azure_native.resources as resources
import pulumi_azure_native.keyvault as keyvault
import pulumi_azure_native.network as network
import pulumi_azure_native as azure_native
import pulumi_azure_native.authorization as authorization
import guid
import rbacRole
import datetime
import vnetStack
import pdnszStack

config = pulumi.Config("param")
env = config.require("env")
tags = config.require_object("tags")
keyValuts = config.require_object("keyValuts")
client = azure_native.authorization.get_client_config()

resource_group = resources.ResourceGroup(
    "rgKv",
    resource_group_name=f"rg-pulumi-kv-{env}-01",
    tags=tags,
)

for kv in keyValuts:
    kv_resource = keyvault.Vault(
        resource_name=kv["name"],
        vault_name=kv["name"],
        resource_group_name=kv.get("rgName", resource_group.name),
        location=resource_group.location,
        tags=tags,
        properties=keyvault.VaultPropertiesArgs(
            sku=resources.SkuArgs(
                name="Standard",
                family="A",
            ),
            tenant_id=client.tenant_id,
            access_policies=[],
            enabled_for_deployment=kv.get("enabledForDeployment", False),
            enabled_for_disk_encryption=kv.get("enabledForDiskEncryption", False),
            enabled_for_template_deployment=kv.get(
                "enabled_for_template_deployment", False
            ),
            enable_rbac_authorization=kv.get("enableRbac", True),
            public_network_access=kv.get("publicNetworkAccess", "Enabled"),
            network_acls=keyvault.NetworkRuleSetArgs(
                bypass="AzureServices",
                default_action="Deny",
                ip_rules=[
                    keyvault.IPRuleArgs(
                        value=ip,
                    )
                    for ip in kv.get("allowedIPs", [])
                ],
            ),
        ),
    )
    secret = keyvault.Secret(
        resource_name=f"secret-{kv['name']}",
        secret_name=f"guid",
        resource_group_name=kv.get("rgName", resource_group.name),
        vault_name=kv_resource.name,
        properties=keyvault.SecretPropertiesArgs(
            value=guid.create_guid("secret", kv["name"]),
            content_type=f"Updated {datetime.datetime.now().strftime('%Y-%m-%d-%p')}",
        ),
    )

    if kv.get("privateIP", "") != "":
        pep = network.PrivateEndpoint(
            resource_name=f"pep-{kv['name']}",
            private_endpoint_name=f"pep-{kv['name']}",
            resource_group_name=kv.get("rgName", resource_group.name),
            subnet=network.SubnetArgs(
                id=(
                    vnetStack.snet_dict["snet-pep"]
                    if "snet-pep" in vnetStack.snet_dict
                    else pulumi.error("snet-pep not found")
                ),
            ),
            custom_network_interface_name=f"nic-{kv['name']}",
            private_link_service_connections=[
                network.PrivateLinkServiceConnectionArgs(
                    name=f"plsc-{kv['name']}",
                    private_link_service_id=kv_resource.id,
                    group_ids=["vault"],
                )
            ],
            ip_configurations=(
                [
                    network.PrivateEndpointIPConfigurationArgs(
                        name="config",
                        group_id="vault",
                        member_name="default",
                        private_ip_address=kv.get("private_ip"),
                    )
                ]
                if kv.get("private_ip")
                else None
            ),
        )

        pdnsz = network.PrivateDnsZoneGroup(
            resource_name=f"pdnsz-{kv['name']}",
            private_dns_zone_group_name="vaultcore",
            private_endpoint_name=pep.name,
            resource_group_name=kv.get("rgName", resource_group.name),
            private_dns_zone_configs=[
                network.PrivateDnsZoneConfigArgs(
                    name="config",
                    private_dns_zone_id=pdnszStack.pdnsz_dict[
                        "privatelink.vaultcore.azure.net"
                    ],
                )
            ],
        )

if authorization.get_client_config().object_id == "abc":
    rbac_kv = authorization.RoleAssignment(
        resource_name=guid.create_guid(
            "rabcKv", authorization.get_client_config().object_id
        ),
        role_assignment_name=guid.create_guid(
            "rabcKv", authorization.get_client_config().object_id
        ),
        scope=kv_resource.id,
        principal_id=authorization.get_client_config().object_id,
        principal_type="User",  #'ServicePrincipal'
        role_definition_id=rbacRole.roleList["KeyVaultAdmin"],
    )
