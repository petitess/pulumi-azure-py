import pulumi_azure_native.authorization as authorization

roles = {
    "KeyVaultAdmin": "00482a5a-887f-4fb3-b363-3b7fe8e74483",
    "Contributor": "b24988ac-6180-42a0-ab88-20f7382dd24c",
    "Reader": "acdd72a7-3385-48ef-bd42-f606fba81ae7",
    "StorageBlobDataContributor": "ba92f5b4-2d11-453d-a403-e96b0029c9fe",
    "MonitoringMetricsPublisher": "3913510d-42f4-4e42-8a64-420c390055eb",
}

roleList = {}
for r, id in roles.items():
    role_def = authorization.get_role_definition(
        role_definition_id=id,
        scope=f"/subscriptions/{authorization.get_client_config().subscription_id}",
    )
    roleList[r] = role_def.id