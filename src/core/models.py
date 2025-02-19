import json
import os

from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path

from core.logger import warn


__all__ = ["AssetsModels", "ModelInfo", "get_assets_models", "resolve_model_record"]


@dataclass
class ModelProviderInfo:
    name: str
    env: Optional[str]

@dataclass
class ModelInfo:
    name: str
    provider: str
    resolve_as: str
    context_window: int
    max_output_tokens: int
    dollars_input: int
    dollars_output: int
    tokens_per_minute: Optional[int]
    request_per_minute: Optional[int]


@dataclass
class AssetsModels:
    model_list: List[ModelInfo]
    model_defaults: Dict[str, str]


def _models_info(base_dir: Path) -> List[ModelInfo]:
    models_file = base_dir.joinpath("assets").joinpath("model_list.json")
    assert models_file.is_file(), f"model_list.json not found at {models_file}"

    models_json = json.loads(models_file.read_text())

    return [
        ModelInfo(
            name=model_name,
            provider=model_info["provider"],
            resolve_as=model_info["resolve_as"],
            context_window=model_info["context_window"],
            max_output_tokens=model_info["max_output_tokens"],
            dollars_input=model_info["dollars_input"],
            dollars_output=model_info["dollars_output"],
            tokens_per_minute=model_info.get("tpm"),
            request_per_minute=model_info.get("rpm"),
        )
        for model_data in models_json
        for model_name, model_info in model_data.items()
    ]

def get_model_providers(base_dir: Path) -> List[ModelProviderInfo]:
    providers_file = base_dir.joinpath("assets").joinpath("model_providers.json")
    assert providers_file.is_file(), f"model_providers.json not found at {providers_file}"

    providers_json = json.loads(providers_file.read_text())

    return [
        ModelProviderInfo(
            name=provider_name,
            env=provider_info.get("env"),
        )
        for provider_data in providers_json
        for provider_name, provider_info in provider_data.items()
    ]

def get_model_list(base_dir: Path) -> List[ModelInfo]:
    all_models = _models_info(base_dir)
    providers = get_model_providers(base_dir)

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

def get_assets_models(base_dir: Path) -> AssetsModels:
    return AssetsModels(
        model_list=get_model_list(base_dir),
        model_defaults=get_model_defaults(base_dir),
    )

def get_model_defaults(base_dir: Path) -> Dict[str, str]:
    defaults_file = base_dir.joinpath("assets").joinpath("model_defaults.json")
    assert defaults_file.is_file(), f"model_defaults.json not found at {defaults_file}"

    defaults_json = json.loads(defaults_file.read_text())
    return defaults_json

def resolve_model_record(model_name: str, a_models: AssetsModels) -> ModelInfo:
    model_name = a_models.model_defaults.get(model_name, model_name)
    for model in a_models.model_list:
        if model.name == model_name:
            return model
