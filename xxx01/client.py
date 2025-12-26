client = azure_native.authorization.get_client_config()
print("SUBID: ", client.subscription_id)
token = azure_native.authorization.get_client_token()
print("token: ", token.token)
