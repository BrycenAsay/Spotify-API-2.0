import base64

def auth_encoding_process(_client_id, _client_secret):
    plain_auth_str = f"{_client_id}:{_client_secret}"
    plain_auth_bytes = plain_auth_str.encode("ascii")
    auth_bytes = base64.b64encode(plain_auth_bytes)
    true_auth = auth_bytes.decode("ascii")
    return true_auth