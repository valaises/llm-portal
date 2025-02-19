import json
import time
import re

from fastapi import APIRouter, Header
from fastapi.responses import Response

from core.models import AssetsModels
from core.globals import API_KEY


__all__ = ["BaseRouter"]


class AuthRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _check_auth(self, authorization: str = None) -> bool:
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


class BaseRouter(AuthRouter):
    def __init__(
            self,
            a_models: AssetsModels,
            *args, **kwargs
    ):
        self._a_models = a_models
        super().__init__(*args, **kwargs)

        self.add_api_route("/v1/models", self._models, methods=["GET"])

    async def _models(self, authorization: str = Header(None)):
        if not self._check_auth(authorization):
            return self._auth_error_response()

        data = {
            "object": "list",
            "data": [
                {
                    "model_name": m_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "system"
                }
                for m_name in [
                    *self._a_models.model_defaults.keys(),
                    *[i.name for i in self._a_models.model_list]
                ]
            ]
        }

        return Response(content=json.dumps(data, indent=2), media_type="application/json")
