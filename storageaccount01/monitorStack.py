import pulumi
import pulumi_azure_native.operationalinsights as operationalinsights
import pulumi_azure_native.monitor as monitor
import pulumi_azure_native.network as network
import vnetStack
import pdnszStack
import guid
import pulumi_azure_native.authorization as authorization

config = pulumi.Config("param")
env = config.require("env")
rg_vnet_name = vnetStack.resource_group.name
ampl_ip = config.require("amplIp")
pls_ips = config.require_object("plsIps")
mg_root_id = config.require("mgRootId")
tags = config.require_object("tags")

pls_ips_list = []
for m, ip in pls_ips.items():
    pls_ips_list.append(
        network.PrivateEndpointIPConfigurationArgs(
            name=m, group_id="azuremonitor", member_name=m, private_ip_address=ip
        )
    )
pls_pdnsz = [
    "privatelink.monitor.azure.com",
    "privatelink.ods.opinsights.azure.com",
    "privatelink.oms.opinsights.azure.com",
    "privatelink.agentsvc.azure-automation.net",
    "privatelink.blob.core.windows.net",
]
pls_pdnsz_list = []
for dns in pls_pdnsz:
    pls_pdnsz_list.append(
        network.PrivateDnsZoneConfigArgs(
            name=dns, private_dns_zone_id=pdnszStack.pdnsz_dict[dns]
        )
    )

log = operationalinsights.Workspace(
    resource_name=f"log-{env}-01",
    workspace_name=f"log-{env}-01",
    resource_group_name=rg_vnet_name,
    tags=tags,
    sku={"name": "PerGB2018"},
)

pls = monitor.PrivateLinkScope(
    resource_name=f"pls-{env}-01",
    location="Global",
    scope_name=f"pls-{env}-01",
    tags=tags,
    access_mode_settings={
        "ingestion_access_mode": "PrivateOnly",
        "query_access_mode": "Open"
    },
    resource_group_name=rg_vnet_name,
)

pls_log = monitor.PrivateLinkScopedResource(
    resource_name=f"log-{env}-01",
    name=f"log-{env}-01",
    kind="resource",
    linked_resource_id=log.id,
    scope_name=pls.name,
    resource_group_name=rg_vnet_name
)

pls_pep = network.PrivateEndpoint(
    resource_name=f"pep-pls-{env}-01",
    private_endpoint_name=f"pep-pls-{env}-01",
    custom_network_interface_name=f"nic-pls-{env}-01",
    resource_group_name=rg_vnet_name,
    ip_configurations=pls_ips_list,
    subnet={"id": vnetStack.snet_dict["snet-pep"]},
    private_link_service_connections=[
        {
            "name": "config",
            "private_link_service_id": pls.id,
            "group_ids": ["azuremonitor"],
        }
    ],
)
pls_dnszone = network.PrivateDnsZoneGroup(
    resource_name=f"default-pls",
    resource_group_name=rg_vnet_name,
    private_endpoint_name=pls_pep.name,
    private_dns_zone_group_name="azuremonitor",
    private_dns_zone_configs=pls_pdnsz_list,
)

ampl = authorization.ResourceManagementPrivateLink(
    resource_name=f"ampl-{env}-01",
    rmpl_name=f"ampl-{env}-01",
    resource_group_name=rg_vnet_name,
)

ampl_link = authorization.PrivateLinkAssociation(
    resource_name=guid.create_guid("1", "1"),
    pla_id=guid.create_guid("1", "1"),
    group_id=mg_root_id,
    properties={"private_link": ampl.id, "public_network_access": "Enabled"},
)

ampl_pep = network.PrivateEndpoint(
    resource_name=f"pep-ampl-{env}-01",
    private_endpoint_name=f"pep-ampl-{env}-01",
    custom_network_interface_name=f"nic-ampl-{env}-01",
    resource_group_name=rg_vnet_name,
    ip_configurations=[
        {
            "group_id": "ResourceManagement",
            "member_name": "ResourceManagement",
            "name": "config",
            "private_ip_address": ampl_ip,
        }
    ],
    subnet={"id": vnetStack.snet_dict["snet-pep"]},
    private_link_service_connections=[
        {
            "name": "config",
            "private_link_service_id": ampl.id,
            "group_ids": ["ResourceManagement"],
        }
    ],
)
ampl_dnszone = network.PrivateDnsZoneGroup(
    resource_name=f"default-ampl",
    resource_group_name=rg_vnet_name,
    private_endpoint_name=ampl_pep.name,
    private_dns_zone_group_name="azure",
    private_dns_zone_configs=[
        {
            "name": "azure",
            "private_dns_zone_id": pdnszStack.pdnsz_dict[f"privatelink.azure.com"],
        }
    ],
)
