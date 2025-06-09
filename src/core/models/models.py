from typing import List, Optional

from core.logger import info, error
from core.models.model_list import ALL_MODELS
from core.models.model_providers import MODEL_PROVIDERS
from core.models.objects import ModelInfo


__all__ = ["get_model_list", "resolve_model_record"]


def get_model_list() -> List[ModelInfo]:
    model_dict = {}

    for m in ALL_MODELS:
        if m.hidden:
            continue

        if not (p := next((p for p in MODEL_PROVIDERS if p.name == m.provider), None)):
            error(f"model {m.name}: provider {m.provider} not found. SKIPPING")
            continue

        if not p.is_env_set():
            info(f"model {m.name}: provider {m.provider} env {p.env} not set. SKIPPING")
            continue

        m.priority = p.priority

        existing_model = model_dict.get(m.name)
        if existing_model is None:
            model_dict[m.name] = m
        else:
            existing_priority = -1 if existing_model.priority is None else existing_model.priority
            current_priority = -1 if m.priority is None else m.priority

            if current_priority > existing_priority:
                model_dict[m.name] = m

    filtered_models = list(model_dict.values())
    for m in filtered_models:
        info(f"+MODEL {m.name}; RESOLVE_AS: {m.resolve_as}; PRIORITY: {m.priority}")

    return filtered_models


def resolve_model_record(
        model_name: str,
        model_list: List[ModelInfo],
) -> Optional[ModelInfo]:
    for model in model_list:
        if model.name == model_name or model_name in model.known_as:
            return model
