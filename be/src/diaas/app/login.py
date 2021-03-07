import cachecontrol
import google.auth.transport.requests
import requests
from flask import request
from google.oauth2.id_token import verify_oauth2_token

from diaas.app.utils import Request
from diaas.config import CONFIG
from diaas.model import User


def make_caching_request():
    session = requests.session()
    cached_session = cachecontrol.CacheControl(session)
    return google.auth.transport.requests.Request(session=cached_session)


CACHING_REQUEST = make_caching_request()


def login():
    req = Request()

    if CONFIG.AUTH_METHOD == "TRUST":
        email = req.require("email")
        if email is not None:
            return User.ensure_user(email)

    id_token = req.json.get("google", {}).get("id_token")
    if id_token is not None:
        id_info = verify_oauth2_token(
            id_token, CACHING_REQUEST, CONFIG.AUTH_GOOGLE_CLIENT_ID
        )

        iss = id_info.get("iss", None)
        if iss not in ("https://accounts.google.com", "accounts.google.com"):
            raise ValueError(f"Wrong issuer: {iss}")

        if not id_info.get("email_verified", False):
            return None

        email = id_info.get("email")
        # name = id_info.get('name')
        # friendly_name = id_info.get('given_name')

        return User.ensure_user(email)

    return None
