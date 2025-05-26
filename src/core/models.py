import json
import os

from typing import List, Optional, Literal
from dataclasses import dataclass
from pydantic import BaseModel, Field

from core.globals import MODELS_FILE, MODELS_PROVIDERS_FILE
from core.logger import warn


@dataclass
class ModelProviderInfo:
    name: str
    env: Optional[str]


class ModelInfo(BaseModel):
    name: str
    provider: Literal["openai", "google", "togetherai", "anthropic"]
    backend: Literal["litellm"]
    resolve_as: str
    context_window: int
    effective_context_window: Optional[int] = None
    tokenizer: Literal["str"] = "simplified"
    max_output_tokens: int
    dollars_input: float
    dollars_output: float
    tokens_per_minute: Optional[int] = None
    request_per_minute: Optional[int] = None
    known_as: List[str] = Field(default_factory=list)
    hidden: bool = False


def models_info() -> List[ModelInfo]:
    models_json = json.loads(MODELS_FILE.read_text())

    models = []
    for model_data in models_json:
        for model_name, model_info in model_data.items():
            # Add the name to the model info dict
            model_info["name"] = model_name
            # Create a ModelInfo instance using Pydantic
            models.append(ModelInfo.model_validate(model_info))

    return models


def get_model_providers() -> List[ModelProviderInfo]:
    providers_json = json.loads(MODELS_PROVIDERS_FILE.read_text())

    return [
        ModelProviderInfo(
            name=provider_name,
            env=provider_info.get("env"),
        )
        for provider_data in providers_json
        for provider_name, provider_info in provider_data.items()
    ]


def get_model_list() -> List[ModelInfo]:
    all_models = models_info()
    providers = get_model_providers()

    filtered_models = []
    for m in all_models:
        if not (p := next((p for p in providers if p.name == m.provider), None)):
            warn(f"model {m.name}: provider {m.provider} not found. SKIPPING")
            continue

        if p.env and not os.environ.get(p.env):
            warn(f"model {m.name}: provider {m.provider} env {p.env} not set. SKIPPING")
            continue

        filtered_models.append(m)

    return filtered_models


def resolve_model_record(
        model_name: str,
        model_list: List[ModelInfo],
) -> Optional[ModelInfo]:
    for model in model_list:
        if model.name == model_name or model_name in model.known_as:
            return model
