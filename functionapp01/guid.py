import uuid
def create_guid(namespace: str, name: str) -> str:
    ns_uuid = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    return str(uuid.uuid3(ns_uuid, f"{namespace}{name}"))