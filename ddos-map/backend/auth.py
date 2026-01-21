from jose import jwt
import requests
import time

CF_CERTS_URL = "https://ini93.cloudflareaccess.com/cdn-cgi/access/certs"
ISSUER = "https://ini93.cloudflareaccess.com"

_certs = None
_certs_ts = 0
_CERT_TTL = 3600


def get_certs():
    global _certs, _certs_ts
    now = time.time()
    if _certs is None or now - _certs_ts > _CERT_TTL:
        _certs = requests.get(CF_CERTS_URL, timeout=5).json()
        _certs_ts = now
    return _certs


def verify_jwt(token: str) -> dict:
    certs = get_certs()
    return jwt.decode(
        token,
        certs,
        algorithms=["RS256"],
        issuer=ISSUER,
        options={
            "verify_exp": True,
            "verify_iss": True,
            "verify_aud": False,  # 👈 explicitly disabled
        },
    )
