name="Standard" if kv['sku'].lower() == "standard" else "Premium",

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
