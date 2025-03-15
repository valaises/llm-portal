import re
import json
from typing import Optional, Dict

from fastapi import APIRouter, Response, Header

from core.globals import SECRET_KEY
from core.repositories.users_repository import UsersRepository, ApiKeyListPost


class AuthRouter(APIRouter):
    def __init__(
            self,
            users_repository: UsersRepository,
            *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.users_repository = users_repository

        self.add_api_route("/v1/auth", self._auth, methods=["GET"])

    async def _auth(self, authorization: str = Header(None)) -> Response:
        auth = await self._check_auth(authorization)
        if not auth:
            return self._auth_error_response()

        return Response(
            content=json.dumps({"auth": auth}),
            media_type="application/json"
        )

    async def _check_auth(
            self,
            authorization: Header = None,
            accept_secret: bool = False
    ) -> Optional[Dict]:
        if not authorization:
            return

        match = re.match(r"^Bearer\s+(.+)$", authorization)
        if not match:
            return

        api_key = match.group(1)
        if api_key == SECRET_KEY and accept_secret:
            return {"api_key": api_key}

        data = await self.users_repository.list_keys(post=ApiKeyListPost())

        for d in data:
            if d["api_key"] == api_key:
                return d

        return

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
