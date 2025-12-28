import pulumi
import pulumi_azure_native.resources as resources
import pulumi_azure_native.cdn as cdn
import pulumi_azure_native.frontdoor as frontdoor
import pulumi_azure_native.dns as dns
import pulumi_azure_native.authorization as authorization
import pulumi_azure_native as azure_native
import pulumi_command.local as local
import guid
import rbacRole
import datetime

date = datetime.datetime.now()
config = pulumi.Config("param")
env = config.require("env")
tags = config.require_object("tags")
storageAccounts = config.require_object("storageAccounts")
frontdoor_endpoints = config.require_object("frontdoorEndpoints")
dns_rg = "rg-dns-01"
client = azure_native.authorization.get_client_config()

resource_group = resources.ResourceGroup(
    "rgAfd",
    resource_group_name=f"rg-pulumi-afd-{env}-01",
    tags=tags,
)

afd = cdn.Profile(
    resource_name=f"afd-{env}-01",
    location="Global",
    profile_name=f"afd-{env}-01",
    resource_group_name=resource_group.name,
    tags=tags,
    sku={"name": "Premium_AzureFrontDoor"},
    origin_response_timeout_seconds=60,
    identity=cdn.ManagedServiceIdentityArgs(
        type=cdn.ManagedServiceIdentityType.SYSTEM_ASSIGNED
    ),
)

for e in frontdoor_endpoints:
    app_name = e["appName"]
    endpoint_name = e.get("endpointName", app_name)
    app_fqdn = e["appFqdn"]
    app_group_id = e.get("appGroupId", "")
    pl_sub_id = e.get("subId", "")
    pl_app_rg = e.get("appRg", "")
    pl_res_type = e.get("resourceType", "")
    enable_health_probe = e.get("enableHealthProbe", True)
    disable_cache = e.get("disableCache", False)
    query_string_caching_behavior = e.get(
        "queryStringCachingBehavior", "IgnoreQueryString"
    )
    custom_domain = e.get("customDomain", "")
    cert_name = e.get("certificateName", "")
    dns_zone_name = e.get("DnsZoneName", "")
    rules = e.get("rules", [])
    custom_rules = e.get("customRules", [])
    rule_group_overrides = e.get("ruleGroupOverrides", [])

    fde = cdn.AFDEndpoint(
        resource_name=f"fde-{endpoint_name}",
        endpoint_name=f"fde-{endpoint_name}",
        location="global",
        resource_group_name=resource_group.name,
        profile_name=afd.name,
        enabled_state="Enabled",
    )

    health_probe_settings = None
    if enable_health_probe:
        health_probe_settings = {
            "probe_interval_in_seconds": 100,
            "probe_path": "/",
            "probe_protocol": "Https",
            "probe_request_type": "HEAD",
        }

    ogrp = cdn.AFDOriginGroup(
        resource_name=f"grp-{endpoint_name}",
        origin_group_name=f"grp-{endpoint_name}",
        resource_group_name=resource_group.name,
        profile_name=afd.name,
        session_affinity_state="Disabled",
        load_balancing_settings={
            "additional_latency_in_milliseconds": 50,
            "sample_size": 4,
            "successful_samples_required": 3,
        },
        health_probe_settings=health_probe_settings,
    )

    shared_private_link_resource = None
    if app_group_id != "":
        shared_private_link_resource = {
            "group_id": app_group_id,
            "private_link_location": "swedencentral",
            "request_message": f"Used by fde-{endpoint_name}(afd-{env}-01)",
            "private_link": {
                "id": f"/subscriptions/{pl_sub_id}/resourceGroups/{pl_app_rg}/providers/{pl_res_type}/{app_name}"
            },
        }

    origin = cdn.AFDOrigin(
        resource_name=f"origin-{endpoint_name}",
        origin_name="origin",
        origin_group_name=ogrp.name,
        resource_group_name=resource_group.name,
        enforce_certificate_name_check=True,
        enabled_state="Enabled",
        profile_name=afd.name,
        host_name=app_fqdn,
        http_port=80,
        https_port=443,
        weight=1000,
        origin_host_header=app_fqdn,
        priority=1,
        shared_private_link_resource=shared_private_link_resource,
    )

    if rules != []:
        ruleset = cdn.RuleSet(
            resource_name=f"ruleset{endpoint_name.replace('-', '')}",
            rule_set_name=f"ruleset{endpoint_name.replace('-', '')}",
            profile_name=afd.name,
            resource_group_name=resource_group.name,
        )

    for r in rules:
        rule = cdn.Rule(
            resource_name=f"{r["name"]}-{endpoint_name}",
            rule_name=r["name"],
            profile_name=afd.name,
            resource_group_name=resource_group.name,
            rule_set_name=ruleset.name,
            order=r["order"],
            match_processing_behavior=r["matchProcessingBehavior"],
            actions=r["actions"],
            conditions=r.get("conditions", []),
        )

    azure_dns_zone = None
    if dns_zone_name != "":
        azure_dns_zone = {
            "id": f"/subscriptions/{client.subscription_id}/resourceGroups/{dns_rg}/providers/Microsoft.Network/dnszones/{dns_zone_name}"
        }

    secret = None
    certificate_type = "ManagedCertificate"
    if cert_name != "":
        secret = {"id": f"{afd.id}/secrets/{cert_name}"}
        certificate_type = "CustomerCertificate"

    if custom_domain != "" and dns_zone_name != "":
        custom_domainx = cdn.AFDCustomDomain(
            resource_name=custom_domain,
            custom_domain_name=custom_domain.replace(f".{dns_zone_name}", ""),
            resource_group_name=resource_group.name,
            profile_name=afd.name,
            host_name=custom_domain,
            azure_dns_zone=azure_dns_zone,
            tls_settings={
                "certificate_type": certificate_type,
                "minimum_tls_version": "TLS12",
                "secret": secret,
            },
        )

        dns_cname = dns.RecordSet(
            resource_name=custom_domain.replace(f".{dns_zone_name}", ""),
            zone_name=dns_zone_name,
            resource_group_name=dns_rg,
            cname_record={"cname": fde.host_name},
            ttl=3600,
            record_type="Cname",
            relative_record_set_name=custom_domain.replace(f".{dns_zone_name}", ""),
        )

        dns_txt = dns.RecordSet(
            resource_name=f"_dnsauth.{custom_domain.replace(f".{dns_zone_name}", "")}",
            zone_name=dns_zone_name,
            resource_group_name=dns_rg,
            txt_records=[
                {
                    "value": [
                        custom_domainx.validation_properties.apply(
                            lambda x: x.validation_token
                        )
                    ]
                }
            ],
            ttl=3600,
            record_type="Txt",
            relative_record_set_name=f"_dnsauth.{custom_domain.replace(f".{dns_zone_name}", "")}",
        )

    rule_sets = None
    if rules != []:
        rule_sets = [{"id": ruleset.id}]

    cache_configuration = None
    if not disable_cache:
        cache_configuration = {
            "query_string_caching_behavior": query_string_caching_behavior,
            "compression_settings": {
                "is_compression_enabled": False,
                "content_types_to_compress": [
                    "application/eot",
                    "application/font",
                    "application/font-sfnt",
                    "application/javascript",
                    "application/json",
                    "application/opentype",
                    "application/otf",
                    "application/pkcs7-mime",
                    "application/truetype",
                    "application/ttf",
                    "application/vnd.ms-fontobject",
                    "application/xhtml+xml",
                    "application/xml",
                    "application/xml+rss",
                    "application/x-font-opentype",
                    "application/x-font-truetype",
                    "application/x-font-ttf",
                    "application/x-httpd-cgi",
                    "application/x-javascript",
                    "application/x-mpegurl",
                    "application/x-opentype",
                    "application/x-otf",
                    "application/x-perl",
                    "application/x-ttf",
                    "font/eot",
                    "font/ttf",
                    "font/otf",
                    "font/opentype",
                    "image/svg+xml",
                    "text/css",
                    "text/csv",
                    "text/html",
                    "text/javascript",
                    "text/js",
                    "text/plain",
                    "text/richtext",
                    "text/tab-separated-values",
                    "text/xml",
                    "text/x-script",
                    "text/x-component",
                    "text/x-java-source",
                ],
            },
        }
    custom_domains = None
    if custom_domain != "":
        custom_domains = [{"id": custom_domainx.id}]
    route = cdn.Route(
        resource_name=f"rt-{endpoint_name}",
        route_name=f"rt-{endpoint_name}",
        resource_group_name=resource_group.name,
        profile_name=afd.name,
        endpoint_name=fde.name,
        origin_group={"id": ogrp.id},
        custom_domains=custom_domains,
        rule_sets=rule_sets,
        cache_configuration=cache_configuration,
        link_to_default_domain="Enabled",
        forwarding_protocol="HttpsOnly",
        https_redirect="Enabled",
        opts=pulumi.ResourceOptions(depends_on=[ogrp, origin]),
    )

    fdfp = frontdoor.Policy(
        resource_name=f"WAF{endpoint_name.replace('-','')}",
        policy_name=f"WAF{endpoint_name.replace('-','')}",
        resource_group_name=resource_group.name,
        location="global",
        policy_settings={
            "state": "Enabled",
            "mode": "Prevention",
            "request_body_check": "Enabled",
        },
        sku=cdn.SkuArgs(name=cdn.SkuName.PREMIUM_AZURE_FRONT_DOOR),
        custom_rules=cdn.CustomRuleListArgs(rules=custom_rules),
        managed_rules={
            "managed_rule_sets": [
                frontdoor.ManagedRuleSetArgsDict(
                    rule_set_type="Microsoft_DefaultRuleSet",
                    rule_set_version="2.1",
                    rule_set_action="Block",
                    rule_group_overrides=rule_group_overrides,
                    exclusions=[],
                ),
                frontdoor.ManagedRuleSetArgsDict(
                    rule_set_type="Microsoft_BotManagerRuleSet",
                    rule_set_version="1.1",
                    rule_group_overrides=[],
                    exclusions=[],
                ),
            ]
        },
    )

    domains = [{"id": fde.id}]
    if custom_domain != "":
        domains = [{"id": fde.id}, {"id": custom_domainx.id}]
    sec_policy = cdn.SecurityPolicy(
        resource_name=f"s-{endpoint_name}",
        security_policy_name=f"s-{endpoint_name}",
        resource_group_name=resource_group.name,
        profile_name=afd.name,
        parameters={
            "type": "WebApplicationFirewall",
            "waf_policy": {"id": fdfp.id},
            "associations": [
                {
                    "domains": domains,
                    "patterns_to_match": ["/*"],
                }
            ],
        },
    )
    if authorization.get_client_config().object_id == "abc":
        rbac_fde = authorization.RoleAssignment(
            resource_name=guid.create_guid(
                "rabcFde", authorization.get_client_config().object_id
            ),
            role_assignment_name=guid.create_guid(
                "rabcFde", authorization.get_client_config().object_id
            ),
            scope=fde.id,
            description="perform CDN purge operations from deployment pipelines",
            principal_id=authorization.get_client_config().object_id,
            principal_type="User",  #'ServicePrincipal'
            role_definition_id=rbacRole.roleList["CDNProfileContributor"],
        )

    # if not pulumi.runtime.is_dry_run() and app_group_id != "":
    if app_group_id != "":
        approve_pep = local.Command(
            resource_name=f"approve_pep-{endpoint_name}",
            create="pwsh -File ./approve_pep.ps1",
            update="pwsh -File ./approve_pep.ps1",
            triggers=[f"{date}"],
            environment={
                "afd_name": afd.name,
                "resource_id": origin.shared_private_link_resource.apply(
                    lambda x: x.private_link.id
                ),
            },
        )
