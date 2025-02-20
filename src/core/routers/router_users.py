import json
import secrets

from fastapi import Header
from fastapi.responses import Response

from core.routers.router_auth import AuthRouter
from core.repositories.users_repository import ApiKeyUpdatePost, ApiKeyCreatePost


class UsersRouter(AuthRouter):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/v1/keys-list", self._list_keys, methods=["GET"])
        self.add_api_route("/v1/keys-create", self._create_key, methods=["POST"])
        self.add_api_route("/v1/keys-delete/{api_key}", self._delete_key, methods=["POST"])
        self.add_api_route("/v1/keys-update/{api_key}", self._update_key, methods=["POST"])

    async def _list_keys(self, authorization: str = Header(None)) -> Response:
        if not await self._check_auth(authorization, True):
            return self._auth_error_response()

        keys = await self.users_repository.list_keys()
        return Response(
            content=json.dumps(
                {
                    "object": "list",
                    "data": keys
                },
                indent=2
            ),
            media_type="application/json"
        )

    async def _create_key(
            self,
            post: ApiKeyCreatePost,
            authorization: str = Header(None)
    ) -> Response:
        if not await self._check_auth(authorization, True):
            return self._auth_error_response()

        if not post.api_key:
            post.api_key = f"sk-{secrets.token_urlsafe(16)}"

        try:
            success = await self.users_repository.create_key(post)
            if not success:
                return Response(
                    status_code=400,
                    content=json.dumps({
                        "error": {
                            "message": "API key already exists",
                            "type": "invalid_request_error",
                            "code": "duplicate_key"
                        }
                    }),
                    media_type="application/json"
                )

        except ValueError as e:
            return Response(
                status_code=400,
                content=json.dumps({
                    "error": {
                        "message": str(e),
                        "type": "invalid_request_error",
                        "code": "invalid_tenant"
                    }
                }),
                media_type="application/json"
            )

        return Response(
            content=json.dumps({
                "message": "API key created successfully",
                "object": "key",
                "data": {
                    "api_key": post.api_key,
                    "scope": post.scope,
                    "tenant": post.tenant
                }
            }, indent=2),
            media_type="application/json"
        )

    async def _delete_key(
            self,
            api_key: str,
            authorization: str = Header(None)
    ) -> Response:
        """Delete an API key."""
        if not await self._check_auth(authorization, True):
            return self._auth_error_response()

        if not await self.users_repository.delete_key(api_key):
            return Response(
                status_code=404,
                content=json.dumps({
                    "error": {
                        "message": "API key not found",
                        "type": "invalid_request_error",
                        "code": "key_not_found"
                    }
                }),
                media_type="application/json"
            )

        return Response(
            content=json.dumps({
                "message": "API key deleted successfully"
            }, indent=2),
            media_type="application/json"
        )

    async def _update_key(
            self,
            post: ApiKeyUpdatePost,
            authorization: str = Header(None)
    ) -> Response:
        """Update an API key's scope or tenant."""
        if not await self._check_auth(authorization, True):
            return self._auth_error_response()

        try:
            success = await self.users_repository.update_key(post)
            if not success:
                return Response(
                    status_code=404,
                    content=json.dumps({
                        "error": {
                            "message": "API key not found",
                            "type": "invalid_request_error",
                            "code": "key_not_found"
                        }
                    }),
                    media_type="application/json"
                )

        except ValueError as e:
            return Response(
                status_code=400,
                content=json.dumps({
                    "error": {
                        "message": str(e),
                        "type": "invalid_request_error",
                        "code": "invalid_request"
                    }
                }),
                media_type="application/json"
            )

        return Response(
            content=json.dumps({
                "message": "API key updated successfully"
            }, indent=2),
            media_type="application/json"
        )
