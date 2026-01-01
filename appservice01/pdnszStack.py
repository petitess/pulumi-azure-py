import pulumi
import pulumi_azure_native.privatedns as privatedns
import vnetStack

config = pulumi.Config("param")
env = config.require("env")
rg_vnet_name = vnetStack.resource_group.name
vnet_name = vnetStack.vnet.name 
tags = config.require_object("tags")
dnszones = config.require_object("dnszones")

pdnsz_dict = {}
for dns in dnszones:
    pdnsz = privatedns.PrivateZone(
        resource_name=dns,
        location="Global",
        private_zone_name=dns,
        resource_group_name=rg_vnet_name,
        tags=tags,
    )
    link = privatedns.VirtualNetworkLink(
        resource_name=f"link-{dns.split(".")[1]}-{env}",
        virtual_network_link_name=f"link-{dns.split(".")[1]}-{env}",
        private_zone_name=pdnsz.name,
        registration_enabled=False,
        location="Global",
        virtual_network={"id": vnetStack.vnet.id},
        resource_group_name=rg_vnet_name,
        tags=tags,
    )
    pdnsz_dict[dns] = pdnsz.id
