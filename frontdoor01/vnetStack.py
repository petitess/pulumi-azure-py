import pulumi
import pulumi_azure_native.resources as resources
import pulumi_azure_native.network as network
import yaml
from typing import List, Dict, Any, Optional


class SubnetConfig:
    def __init__(self, data: Dict[str, Any]):
        self.snet_name = data["snetName"]
        self.prefix = data["prefix"]
        self.private_endpoint_network_policies = data.get(
            "privateEndpointNetworkPolicies"
        )
        self.private_link_service_network_policies = data.get(
            "privateLinkServiceNetworkPolicies"
        )
        self.service_endpoints = data.get("serviceEndpoints", [])
        self.delegations = data.get("delegations", [])    

config = pulumi.Config("param")
env = config.require("env")
rg_vnet_name = config.require("rgVnetName")
vnet_name = config.require("vnetName")
tags = config.require_object("tags")
subnet_configs = config.require_object("subnets")
address_prefixes = config.require_object("addressPrefixes")

yaml_file = f"./Pulumi.{env}_nsg.yaml"
with open(yaml_file, "r") as f:
    nsg_data = yaml.safe_load(f)

network_security_groups = nsg_data

resource_group = resources.ResourceGroup(
    "rgVnet",
    resource_group_name=rg_vnet_name,
    tags=tags,
)

vnet = network.VirtualNetwork(
    "vnet",
    virtual_network_name=vnet_name,
    resource_group_name=resource_group.name,
    address_space=network.AddressSpaceArgs(address_prefixes=address_prefixes),
    tags=tags,
)

for snet_config_dict in subnet_configs:
    snet = SubnetConfig(snet_config_dict)

    matching_nsgs = [
        n for n in network_security_groups if n["snetName"] == snet.snet_name
    ]

    nsg = None
    if matching_nsgs:
        security_rules: List[network.SecurityRuleArgs] = []

        for nsg_item in matching_nsgs:
            for rule in nsg_item["rules"]:
                dest_asgs = (
                    [
                        network.ApplicationSecurityGroupArgs(id=asg_id)
                        for asg_id in rule.get(
                            "destinationApplicationSecurityGroups", []
                        )
                    ]
                    if rule.get("destinationApplicationSecurityGroups", [])
                    else None
                )

                src_asgs = (
                    [
                        network.ApplicationSecurityGroupArgs(id=asg_id)
                        for asg_id in rule.get("sourceApplicationSecurityGroups", [])
                    ]
                    if rule.get("sourceApplicationSecurityGroups", [])
                    else None
                )

                security_rules.append(
                    network.SecurityRuleArgs(
                        name=rule["name"],
                        access=rule["access"],
                        description=rule.get("description", ""),
                        destination_address_prefix=rule.get(
                            "destinationAddressPrefix", ""
                        ),
                        destination_address_prefixes=rule.get(
                            "destinationAddressPrefixes", []
                        ),
                        destination_port_range=str(
                            rule.get("destinationPortRange", "")
                        ),
                        destination_port_ranges=rule.get("destinationPortRanges", []),
                        direction=rule["direction"],
                        priority=rule["priority"],
                        protocol=rule["protocol"],
                        source_address_prefix=rule.get("sourceAddressPrefix", ""),
                        source_address_prefixes=rule.get("sourceAddressPrefixes", []),
                        source_port_range=rule.get("sourcePortRange", ""),
                        source_port_ranges=rule.get("sourcePortRanges", []),
                        destination_application_security_groups=dest_asgs,
                        source_application_security_groups=src_asgs,
                    )
                )

        nsg = network.NetworkSecurityGroup(
            f"nsg-snet-{snet.snet_name}",
            network_security_group_name=f"nsg-snet-{snet.snet_name}",
            resource_group_name=resource_group.name,
            security_rules=security_rules,
        )

    service_endpoints_args = (
        [
            network.ServiceEndpointPropertiesFormatArgs(service=srv)
            for srv in snet.service_endpoints
        ]
        if snet.service_endpoints
        else None
    )

    delegations_args = (
        [
            network.DelegationArgs(
                name=srv,
                service_name=srv,
            )
            for srv in snet.delegations
        ]
        if snet.delegations
        else None
    )

    subnet = network.Subnet(
        f"snet-{snet.snet_name}",
        subnet_name=f"snet-{snet.snet_name}",
        resource_group_name=resource_group.name,
        virtual_network_name=vnet.name,
        address_prefix=snet.prefix,
        private_endpoint_network_policies=snet.private_endpoint_network_policies,
        private_link_service_network_policies=snet.private_link_service_network_policies,
        service_endpoints=service_endpoints_args,
        network_security_group=(
            network.NetworkSecurityGroupArgs(id=nsg.id) if nsg else None
        ),
        delegations=delegations_args,
    )
