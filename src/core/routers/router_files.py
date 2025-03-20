import json
from typing import Literal, List, Optional

import aiohttp
from fastapi import Header, Response
from openai import OpenAI
from pydantic import BaseModel

from core.logger import warn
from core.routers.router_auth import AuthRouter


class FileUpload(BaseModel):
    file_data: str
    filename: str
    purpose: Literal["assistants", "fine-tune", "vision", "batch"]


class FilesUploadPost(BaseModel):
    files: List[FileUpload]


class FilesRetrievePost(BaseModel):
    file_id: str


class VectorStoreCreate(BaseModel):
    name: str
    file_ids: List[str]


class VectorStoreRetrieve(BaseModel):
    vector_store_id: str


class VectorStoreSearch(BaseModel):
    vector_store_id: str
    query: str
    max_num_results: Optional[int] = 10


class FilesRouter(AuthRouter):
    def __init__(
            self,
            *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.add_api_route(f"/v1/files-list", self._files_list, methods=["GET"])
        self.add_api_route(f"/v1/files-upload", self._files_upload, methods=["POST"])
        # retrieve information about specific file
        self.add_api_route(f"/v1/file-retrieve", self._file_retrieve, methods=["POST"])
        # retrieve file content
        # delete file
        self.add_api_route(f"/v1/vector-store/create", self._vector_store_create, methods=["POST"])
        self.add_api_route(f"/v1/vector-stores/list", self._vector_stores_list, methods=["GET"])
        self.add_api_route(f"/v1/vector-store/retrieve", self._vector_store_retrieve, methods=["POST"])
        # modify vector store
        # delete vector store
        self.add_api_route(f"/v1/vector-store/search", self._vector_store_search, methods=["POST"])

    async def _files_list(self, authorization: str = Header(None)):
        user = await self._check_auth(authorization)
        if not user:
            return self._auth_error_response()

        limit = 1000

        client = OpenAI()

        files = list(client.files.list(limit=limit))
        if len(files) == limit:
            while True:
                try:
                    batch = list(client.files.list(limit=limit, after=(files[-1] or {}).get("id")))
                    files.extend(batch)
                    if len(batch) != limit:
                        break
                except Exception as e:
                    warn(e)
                    break

        return Response(content=json.dumps([f.model_dump() for f in files], indent=2), media_type="application/json")

    async def _files_upload(self, post: FilesUploadPost, authorization: str = Header(None)):
        user = await self._check_auth(authorization)
        if not user:
            return self._auth_error_response()

        client = OpenAI()
        responses = []
        for file in post.files:
            resp = client.files.create(file=(file.filename, file.file_data.encode()), purpose=file.purpose)
            responses.append(resp)

        return Response(content=json.dumps([r.model_dump() for r in responses], indent=2), media_type="application/json")

    async def _file_retrieve(self, post: FilesUploadPost, authorization: str = Header(None)):
        user = await self._check_auth(authorization)
        if not user:
            return self._auth_error_response()

        client = OpenAI()
        content = client.files.content(file_id=post.file_id)

        return Response(content=json.dumps(content, indent=2), media_type="application/json")

    async def _vector_store_create(self, post: VectorStoreCreate, authorization: str = Header(None)):
        user = await self._check_auth(authorization)
        if not user:
            return self._auth_error_response()

        client = OpenAI()
        try:
            vector_store = client.beta.vector_stores.create(
                name=post.name,
                file_ids=post.file_ids,
            )
            return Response(content=json.dumps(vector_store.model_dump(), indent=2), media_type="application/json")
        except Exception as e:
            warn(f"Error creating vector store: {e}")
            return Response(
                content=json.dumps({"error": str(e)}),
                status_code=400,
                media_type="application/json"
            )

    async def _vector_stores_list(self, authorization: str = Header(None)):
        user = await self._check_auth(authorization)
        if not user:
            return self._auth_error_response()

        client = OpenAI()
        try:
            vector_stores = list(client.beta.vector_stores.list())
            return Response(content=json.dumps([s.model_dump() for s in vector_stores], indent=2), media_type="application/json")
        except Exception as e:
            warn(f"Error listing vector stores: {e}")
            return Response(
                content=json.dumps({"error": str(e)}),
                status_code=400,
                media_type="application/json"
            )

    async def _vector_store_retrieve(self, post: VectorStoreRetrieve, authorization: str = Header(None)):
        user = await self._check_auth(authorization)
        if not user:
            return self._auth_error_response()

        client = OpenAI()
        try:
            vector_store = client.beta.vector_stores.retrieve(vector_store_id=post.vector_store_id)
            return Response(content=json.dumps(vector_store.model_dump(), indent=2), media_type="application/json")
        except Exception as e:
            warn(f"Error retrieving vector store: {e}")
            return Response(
                content=json.dumps({"error": str(e)}),
                status_code=400,
                media_type="application/json"
            )

    async def _vector_store_search(self, post: VectorStoreSearch, authorization: str = Header(None)):
        user = await self._check_auth(authorization)
        if not user:
            return self._auth_error_response()

        try:
            api_key = OpenAI().api_key

            url = f"https://api.openai.com/v1/vector_stores/{post.vector_store_id}/search"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "query": post.query,
                "max_num_results": post.max_num_results
            }

            if hasattr(post, 'filters') and post.filters:
                payload["filters"] = post.filters

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return Response(content=json.dumps(result, indent=2), media_type="application/json")
                    else:
                        error_text = await resp.text()
                        warn(f"Error searching vector store: {error_text}")
                        return Response(
                            content=json.dumps({"error": error_text}),
                            status_code=resp.status,
                            media_type="application/json"
                        )
        except Exception as e:
            warn(f"Error searching vector store: {e}")
            return Response(
                content=json.dumps({"error": str(e)}),
                status_code=500,
                media_type="application/json"
            )
