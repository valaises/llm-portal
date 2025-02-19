import re
import json

from fastapi import APIRouter, Response, Header

from core.globals import API_KEY


class AuthRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _check_auth(self, authorization: Header = None) -> bool:
        if not authorization or not authorization.startswith("Bearer "):
            return False

        match = re.match(r"^Bearer\s+(.+)$", authorization)
        if not match:
            return False

        api_key = match.group(1)
        return api_key == API_KEY

    def _auth_error_response(self):
        return Response(
            status_code=401,
            content=json.dumps({
                "error": {
                    "message": "Invalid authentication",
                    "type": "invalid_request_error",
                    "code": "invalid_api_key"
                }
            }),
            media_type="application/json"
        )
