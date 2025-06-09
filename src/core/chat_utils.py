from typing import List, Iterator

from core.logger import info
from core.models.objects import ModelInfo
from core.models.tokenizers import Tokenizer
from openai_wrappers.types import ChatMessage, ChatMessageSystem, ToolCall, ChatMessageTool, ChatMessageAssistant


def limit_messages(
        messages: List[ChatMessage],
        tok: Tokenizer,
        model_record: ModelInfo
) -> List[ChatMessage]:
    new_messages = []

    messages_tok_limit: int = model_record.effective_context_window or model_record.context_window

    take_messages = [
        isinstance(m, ChatMessageSystem) for m in messages
    ]
    tok_count = sum([
        tok.count_tokens(m.content) for (m, take) in zip(messages, take_messages) if take
    ])

    take_messages.reverse()
    messages.reverse()

    for (message, take) in zip(messages, take_messages):
        if take == True:
            new_messages.append(message)
            continue

        m_tokens = tok.count_tokens(message.content)
        if tok_count + m_tokens > messages_tok_limit:
            break

        tok_count += m_tokens
        new_messages.append(message)

    new_messages.reverse()

    info(f"model={model_record.name}; {tok_count=}; {messages_tok_limit=}")

    return new_messages


def get_unanswered_tool_calls(messages: List[ChatMessage]) -> Iterator[ToolCall]:
    tool_messages: List[ChatMessageTool] = [
        m for m in messages if isinstance(m, ChatMessageTool)
    ]
    answered_tool_call_ids = {
        tool_call_id for m in tool_messages if (tool_call_id := m.tool_call_id)
    }

    for m in messages:
        if isinstance(m, ChatMessageAssistant) and m.tool_calls:
            for tool_call in m.tool_calls:
                if tool_call.id not in answered_tool_call_ids:
                    yield tool_call


def answer_unanswered_tool_calls_with_error(messages: List[ChatMessage]) -> List[ChatMessage]:
    unanswered_tool_calls = list(get_unanswered_tool_calls(messages))
    if not unanswered_tool_calls:
        return []

    new_messages = [
        ChatMessageTool(
            role="tool",
            content=f"Failed to execute tool {utc.function.name}",
            tool_call_id=utc.id
        )
        for utc in unanswered_tool_calls
    ]

    return new_messages


def remove_trail_tool_calls(messages: List[ChatMessage]):
    # Get all unanswered tool calls
    unanswered_tool_calls = list(get_unanswered_tool_calls(messages))
    unanswered_tool_call_ids = {tool_call.id for tool_call in unanswered_tool_calls}

    # Remove unanswered tool calls from assistant messages
    for m in messages:
        if isinstance(m, ChatMessageAssistant) and m.tool_calls:
            m.tool_calls = [
                tool_call for tool_call in m.tool_calls
                if tool_call.id not in unanswered_tool_call_ids
            ]
            if len(m.tool_calls) == 0:
                m.tool_calls = None
