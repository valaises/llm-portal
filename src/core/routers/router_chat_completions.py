import json
from http.client import HTTPException

from typing import List, Optional

import litellm

from fastapi import Header, HTTPException
from fastapi.responses import StreamingResponse

from core.logger import warn, info, error
from core.models import AssetsModels, ModelInfo
from core.routers.router_auth import AuthRouter
from core.routers.chat_models import ChatPost, ChatMessage


async def litellm_completion_stream(
        model_name: str,
        messages: List[ChatMessage],
        model_record: ModelInfo,
        post: ChatPost
):
    prefix, postfix = "data: ", "\n\n"
    try:
        max_tokens = min(model_record.max_output_tokens, post.max_tokens) if post.max_tokens else post.max_tokens
        stream = await litellm.acompletion(
            model=model_name, messages=messages, stream=True,
            temperature=post.temperature, top_p=post.top_p,
            max_tokens=max_tokens,
            tools=post.tools,
            tool_choice=post.tool_choice,
            stop=post.stop if post.stop else None,
            n=post.n,
        )

        finish_reason = None
        async for chunk in stream:
            try:
                data = chunk.model_dump()
                choice0 = data["choices"][0]
                finish_reason = choice0["finish_reason"]
            except Exception as e:
                error(f"error in litellm_completion_stream: {e}")
                data = {"choices": [{"finish_reason": finish_reason}]}

            yield prefix + json.dumps(data) + postfix
    except Exception as e:
        err_msg = f"error in litellm_completion_stream: {e}"
        error(err_msg)
        yield prefix + json.dumps({"error": err_msg}) + postfix


async def litellm_completion_not_stream(
        model_name: str,
        messages: List[ChatMessage],
        model_record: ModelInfo,
        post: ChatPost
):
    try:
        max_tokens = min(model_record.max_output_tokens, post.max_tokens) if post.max_tokens else post.max_tokens
        response = await litellm.acompletion(
            model=model_name, messages=messages, stream=False,
            temperature=post.temperature, top_p=post.top_p,
            max_tokens=max_tokens,
            tools=post.tools,
            tool_choice=post.tool_choice,
            stop=post.stop if post.stop else None,
            n=post.n,
        )
        response_dict = response.model_dump()
        yield json.dumps(response_dict)

    except Exception as e:
        err_msg = f"error in litellm_completion_not_stream: {e}"
        error(err_msg)
        yield json.dumps({"error": err_msg})


class ChatCompletionsRouter(AuthRouter):
    def __init__(
            self,
            a_models: AssetsModels,
            *args, **kwargs
    ):
        self._a_models = a_models
        super().__init__(*args, **kwargs)

        self.add_api_route("/v1/chat/completions", self._chat_completions, methods=["POST"])

    async def _chat_completions(self, post: ChatPost, authorization: str = Header(None)):
        if not self._check_auth(authorization):
            return self._auth_error_response()

        model_record: Optional[ModelInfo] = next(model for model in self._a_models.model_list if model.name == post.model)
        if not model_record:
            raise HTTPException(status_code=404, detail=f"Model {post.model} not found")

        if model_record.resolve_as not in litellm.model_list:
            warn(f"model {model_record.name} not in litellm.model_list")
        info(f"model resolve {model_record.name} -> {model_record.resolve_as}")

        response_streamer = litellm_completion_stream(
            model_record.resolve_as,
            post.messages,
            model_record,
            post,
        ) if post.stream else litellm_completion_not_stream(
            model_record.resolve_as,
            post.messages,
            model_record,
            post,
        )

        return StreamingResponse(response_streamer, media_type="text/event-stream")
