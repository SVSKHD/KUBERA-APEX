from dhanhq import dhanhq

client_id = "1100567724"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzE5MTU1ODkzLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDU2NzcyNCJ9.0cprkA0dIOG_j8ikgGWsMMKTrz0aKRC4axw6E6Jc_r4QpDGPJlJQfvK-G_snfjVeZ0a72C_LXs9ogKPbtmQbMQ"

def initialize_dhan(client_id, access_token):
    connection = dhanhq(client_id=client_id, access_token=access_token)
    return connection


dhan = initialize_dhan(client_id , access_token)

