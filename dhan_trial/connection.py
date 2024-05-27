from dhanhq import dhanhq


def initialize_dhan(client_id, access_token):
    connection = dhanhq(client_id=client_id, access_token=access_token)
    return connection
