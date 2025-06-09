import os

from dataclasses import dataclass
from typing import Optional, Literal, List

from pydantic import BaseModel, Field


@dataclass
class ModelProviderInfo:
    name: str
    env: Optional[str]
    priority: Optional[int] = None

    def is_env_set(self) -> bool:
        return self.env is not None and os.environ.get(self.env, "").strip() != ""


class ModelInfo(BaseModel):
    name: str
    provider: Literal["openai", "google", "togetherai", "anthropic", "openrouter"]
    backend: Literal["litellm"]
    resolve_as: str
    context_window: int
    effective_context_window: Optional[int] = None
    tokenizer: Literal["simplified"] = "simplified"
    max_output_tokens: int
    effective_max_output_tokens: Optional[int] = None
    dollars_input: float
    dollars_output: float
    tokens_per_minute: Optional[int] = None
    request_per_minute: Optional[int] = None
    known_as: List[str] = Field(default_factory=list)
    hidden: bool = False

    priority: Optional[int] = None
