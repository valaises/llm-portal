import json
from http.client import HTTPException
from queue import Queue

from typing import List, Optional, Dict

import litellm

from fastapi import Header, HTTPException
from fastapi.responses import StreamingResponse

from core.chat_utils import limit_messages, remove_trail_tool_calls, answer_unanswered_tool_calls_with_error
from core.logger import info, error
from core.models import ModelInfo, resolve_model_record
from core.repositories.stats_repository import UsageStatRecord
from core.routers.router_auth import AuthRouter
from core.tokenizers import Tokenizer
from openai_wrappers.types import ChatMessage, ChatPost


def increment_stats_record(rec: UsageStatRecord, model_record: ModelInfo, usage: Dict):
    try:
        rec.tokens_in += usage["prompt_tokens"]
        rec.tokens_out += usage["completion_tokens"]
        try:
            rec.dollars_in += round(usage["prompt_tokens"] / 1_000_000 * model_record.dollars_input, 5)
            rec.dollars_out += round(usage["completion_tokens"] / 1_000_000 * model_record.dollars_output, 5)
        except Exception:
            pass
    except Exception:
        pass


async def litellm_completion_stream(
        messages: List[ChatMessage],
        model_record: ModelInfo,
        post: ChatPost,
        stats_record: UsageStatRecord,
        stats_q: Queue,
):
    prefix, postfix = "data: ", "\n\n"
    finish_reason = None
    try:
        stream = await litellm.acompletion(
            model=model_record.resolve_as, messages=messages, stream=True,
            temperature=post.temperature, top_p=post.top_p,
            max_tokens=post.max_tokens,
            tools=post.tools,
            tool_choice=post.tool_choice,
            stop=post.stop if post.stop else None,
            n=post.n,
            stream_options={
                "include_usage": True,
            }
        )

        async for chunk in stream:
            try:
                data = chunk.model_dump()
                choice0 = data["choices"][0]
                finish_reason = choice0["finish_reason"]

                if usage := data.get("usage"):
                    increment_stats_record(stats_record, model_record, usage)
                if finish_reason:
                    stats_record.finish_reason = finish_reason

            except Exception as e:
                error(f"error in litellm_completion_stream: {e}")
                data = {"choices": [{"finish_reason": finish_reason}]}

            yield prefix + json.dumps(data) + postfix
    except Exception as e:
        err_msg = f"error in litellm_completion_stream: {e}"
        error(err_msg)
        yield prefix + json.dumps({"error": err_msg}) + postfix
    finally:
        stats_q.put(stats_record)


async def litellm_completion_not_stream(
        messages: List[ChatMessage],
        model_record: ModelInfo,
        post: ChatPost,
        stats_record: UsageStatRecord,
        stats_q: Queue,
):
    try:
        response = await litellm.acompletion(
            model=model_record.resolve_as, messages=messages, stream=False,
            temperature=post.temperature, top_p=post.top_p,
            max_tokens=post.max_tokens,
            tools=post.tools,
            tool_choice=post.tool_choice,
            stop=post.stop if post.stop else None,
            n=post.n,
        )
        response_dict = response.model_dump()

        if usage := response_dict.get("usage"):
            increment_stats_record(stats_record, model_record, usage)
        stats_q.put(stats_record)

        yield json.dumps(response_dict)

    except Exception as e:
        err_msg = f"error in litellm_completion_not_stream: {e}"
        error(err_msg)
        yield json.dumps({"error": err_msg})


class ChatCompletionsRouter(AuthRouter):
    def __init__(
            self,
            model_list: List[ModelInfo],
            tokenizers: Dict[str, Tokenizer],
            stats_q: Queue,
            *args, **kwargs
    ):
        self._model_list = model_list
        self._tokenizers = tokenizers
        self._stats_q = stats_q

        super().__init__(*args, **kwargs)

        self.add_api_route(f"/v1/chat/completions", self._chat_completions, methods=["POST"])

    async def _chat_completions(self, post: ChatPost, authorization: str = Header(None)):
        info(post.tools)
        user = await self._check_auth(authorization)
        if not user:
            return self._auth_error_response()

        model_record: Optional[ModelInfo] = resolve_model_record(post.model, self._model_list)
        if not model_record:
            raise HTTPException(status_code=404, detail=f"Model {post.model} not found")

        tokenizer = self._tokenizers.get(model_record.tokenizer)
        if not tokenizer:
            raise HTTPException(status_code=404, detail=f"Tokenizer {model_record.tokenizer} not found")

        messages = post.messages

        tool_res_messages = answer_unanswered_tool_calls_with_error(messages)
        messages.extend(tool_res_messages)

        messages = limit_messages(messages, tokenizer, model_record)

        remove_trail_tool_calls(messages)

        stats_record = UsageStatRecord(
            user_id=user["user_id"],
            api_key=user["api_key"],
            model=model_record.resolve_as,
            tokens_in=0,
            tokens_out=0,
            dollars_in=0,
            dollars_out=0,
            messages_cnt=len(messages),
        )

        max_tokens = min(model_record.max_output_tokens, post.max_tokens) if post.max_tokens else post.max_tokens
        if post.max_tokens != max_tokens:
            info(f"model {model_record.name} max_tokens {post.max_tokens} -> {max_tokens}")
            post.max_tokens = max_tokens

        if model_record.backend == "litellm":
            response_streamer = litellm_completion_stream(
                messages,
                model_record,
                post,
                stats_record,
                self._stats_q,
            ) if post.stream else litellm_completion_not_stream(
                messages,
                model_record,
                post,
                stats_record,
                self._stats_q,
            )

        else:
            raise HTTPException(status_code=400, detail=f"Model {model_record.name}: Backend {model_record.backend} is not supported")

        return StreamingResponse(response_streamer, media_type="text/event-stream")
