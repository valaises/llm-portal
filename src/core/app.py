from queue import Queue
from typing import Dict

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from core.models import get_model_list
from core.repositories.users_repository import UsersRepository
from core.routers.router_chat_completions import ChatCompletionsRouter
from core.routers.router_models import ModelsRouter
from core.routers.router_users import UsersRouter
from core.tokenizers import resolve_tokenizer, Tokenizer


__all__ = ["App"]


class App(FastAPI):
    def __init__(
            self,
            stats_q: Queue,
            users_repository: UsersRepository,
            *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._model_list = get_model_list()
        assert self._model_list, "No models available"

        self._tokenizers: Dict[str, Tokenizer] = {
            tok_name: resolve_tokenizer(tok_name)
            for tok_name in {m.tokenizer for m in self._model_list}
        }

        self._stats_q = stats_q
        self._users_repository = users_repository

        self._setup_middlewares()
        self.add_event_handler("startup", self._startup_events)


    def _setup_middlewares(self):
        self.add_middleware(
            CORSMiddleware, # type: ignore[arg-type]
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.add_middleware(NoCacheMiddleware) # type: ignore[arg-type]

    async def _startup_events(self):
        self._users_repository.create_admin_record_if_needed()

        for router in self._routers():
            self.include_router(router)

    def _routers(self):
        return [
            ModelsRouter(
                self._model_list,
                self._users_repository
            ),
            ChatCompletionsRouter(
                self._model_list,
                self._tokenizers,
                self._stats_q,
                self._users_repository
            ),
            UsersRouter(
                self._users_repository
            ),
        ]


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache"
        return response
