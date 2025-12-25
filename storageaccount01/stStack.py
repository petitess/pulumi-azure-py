import pulumi
import pulumi_azure_native.resources as resources
import pulumi_azure_native.storage as storage
import pulumi_azure_native.network as network
import pulumi_azure_native.authorization as authorization
import pulumi_azure_native.monitor as monitor
import vnetStack
import pdnszStack
import guid
import rbacRole
import monitorStack

config = pulumi.Config("param")
env = config.require("env")
tags = config.require_object("tags")
storageAccounts = config.require_object("storageAccounts")

resource_group = resources.ResourceGroup(
    "rgSt",
    resource_group_name=f"rg-pulumi-st-{env}-01",
    tags=tags,
)

for s in storageAccounts:
    ipRules = []
    for ip in s.get("allowedIPs", []):
        ipRules.append(
            {
                "i_p_address_or_range": ip,
            }
        )

    st = storage.StorageAccount(
        resource_name=s["name"],
        account_name=s["name"],
        resource_group_name=s.get("rgName", resource_group.name),
        kind=storage.Kind.STORAGE_V2,
        public_network_access=s["publicNetworkAccess"],
        default_to_o_auth_authentication=s.get("rbacAuth", True),
        sku={"name": s["skuName"]},
        network_rule_set={
            "bypass": storage.Bypass.AZURE_SERVICES,
            "default_action": storage.DefaultAction.DENY,
            "ip_rules": ipRules,
        },
    )

    blob = storage.BlobContainer(
        resource_name=f"container-{s["name"]}",
        container_name="container",
        account_name=st.name,
        resource_group_name=s.get("rgName", resource_group.name),
    )

    blob_diag = monitor.DiagnosticSetting(
        resource_name=s["name"],
        name=s["name"],
        resource_uri=st.id.apply(lambda x: f"{x}/blobservices/default"),
        workspace_id=monitorStack.log.id,
        logs=[monitor.LogSettingsArgs(category="StorageRead", enabled=True)],
    )

    for p, ip in s.get("privateEndpoints", {}).items():
        pep = network.PrivateEndpoint(
            resource_name=f"pep-{s["name"]}-{p}",
            private_endpoint_name=f"pep-{s["name"]}-{p}",
            custom_network_interface_name=f"nic-{s["name"]}-{p}",
            resource_group_name=s.get("rgName", resource_group.name),
            ip_configurations=[
                {
                    "group_id": p,
                    "member_name": p,
                    "name": f"config-{p}",
                    "private_ip_address": ip,
                }
            ],
            subnet={"id": vnetStack.snet_dict["snet-pep"]},
            private_link_service_connections=[
                {
                    "name": f"config-{p}",
                    "private_link_service_id": st.id,
                    "group_ids": [p],
                }
            ],
        )
        dnszone = network.PrivateDnsZoneGroup(
            resource_name=f"default-{p}",
            resource_group_name=s.get("rgName", resource_group.name),
            private_endpoint_name=pep.name,
            private_dns_zone_group_name=p,
            private_dns_zone_configs=[
                {
                    "name": p,
                    "private_dns_zone_id": pdnszStack.pdnsz_dict[
                        f"privatelink.{p}.core.windows.net"
                    ],
                }
            ],
        )

rbac_st = authorization.RoleAssignment(
    resource_name=guid.create_guid(
        "rabcSt", authorization.get_client_config().object_id
    ),
    role_assignment_name=guid.create_guid(
        "rabcSt", authorization.get_client_config().object_id
    ),
    scope=resource_group.id,
    principal_id=authorization.get_client_config().object_id,
    principal_type="User",
    role_definition_id=rbacRole.roleList["StorageBlobDataContributor"],
)
