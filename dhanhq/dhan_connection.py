import dhanhq


def initialize_dhan(api_key, api_secret, access_token):
    dhan = dhanhq.Dhan(api_key=api_key, api_secret=api_secret, access_token=access_token)
    return dhan
