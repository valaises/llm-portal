from core.models.objects import ModelInfo


# https://platform.openai.com/docs/models
MODELS_OPENAI = [
    ModelInfo(
        name="gpt-4.1",
        provider="openai",
        backend="litellm",
        resolve_as="openai/gpt-4.1-2025-04-14",
        context_window=1_000_000,
        effective_context_window=100_000,
        max_output_tokens=16_384,
        dollars_input=2,
        dollars_output=8,
        tokens_per_minute=30_000,
        request_per_minute=500,
    ),
]

# https://ai.google.dev/gemini-api/docs/models
MODELS_GOOGLE = [
    ModelInfo(
        name="gemini-2.5-flash",
        provider="google",
        backend="litellm",
        resolve_as="gemini/gemini-2.5-flash-preview-05-20",
        context_window=1_000_000,
        effective_context_window=200_000,
        max_output_tokens=64_000,
        effective_max_output_tokens=16_000,
        dollars_input=0.15,
        dollars_output=0.6,
        tokens_per_minute=1_000_000,
        request_per_minute=1000,
        hidden=True,
    ),
    ModelInfo(
        name="gemini-2.5-pro",
        provider="google",
        backend="litellm",
        resolve_as="gemini/gemini-2.5-pro-preview-06-05",
        context_window=1_000_000,
        effective_context_window=200_000,
        max_output_tokens=64_000,
        effective_max_output_tokens=16_000,
        dollars_input=1.25,
        dollars_output=10,
        tokens_per_minute=2_000_000,
        request_per_minute=10,
        hidden=True,
    ),
]

# https://docs.anthropic.com/en/docs/about-claude/models/overview
MODELS_ANTHROPIC = [
    ModelInfo(
        name="claude-sonnet-4",
        provider="anthropic",
        backend="litellm",
        resolve_as="anthropic/claude-sonnet-4-20250514",
        context_window=200_000,
        effective_context_window=64_000,
        max_output_tokens=32_000,
        effective_max_output_tokens=16_000,
        dollars_input=3,
        dollars_output=15,
        tokens_per_minute=20_000,
        request_per_minute=50,
    ),
    ModelInfo(
        name="claude-opus-4",
        provider="anthropic",
        backend="litellm",
        resolve_as="anthropic/claude-opus-4-20250514",
        context_window=200_000,
        effective_context_window=64_000,
        max_output_tokens=32_000,
        effective_max_output_tokens=16_000,
        dollars_input=15,
        dollars_output=75,
        tokens_per_minute=20_000,
        request_per_minute=50,
        hidden=True,
    ),
]

MODELS_TOGETHERAI = [
    ModelInfo(
        name="deepseek-r1",
        provider="togetherai",
        backend="litellm",
        resolve_as="together_ai/deepseek-ai/DeepSeek-R1",
        context_window=128_000,
        max_output_tokens=32_000,
        dollars_input=3,
        dollars_output=7,
        request_per_minute=600,
        hidden=True,
    ),
]

# https://openrouter.ai/models
MODELS_OPENROUTER = [
    ModelInfo(
        name="gemini-2.5-flash",
        provider="openrouter",
        backend="litellm",
        resolve_as="openrouter/google/gemini-2.5-flash-preview-05-20",
        context_window=1_000_000,
        effective_context_window=200_000,
        max_output_tokens=64_000,
        effective_max_output_tokens=16_000,
        dollars_input=0.15,
        dollars_output=0.6,
        tokens_per_minute=1_000_000,
        request_per_minute=1000,
    ),
    ModelInfo(
        name="gemini-2.5-pro",
        provider="openrouter",
        backend="litellm",
        resolve_as="openrouter/google/gemini-2.5-pro-preview",
        context_window=1_000_000,
        effective_context_window=200_000,
        max_output_tokens=64_000,
        effective_max_output_tokens=16_000,
        dollars_input=1.25,
        dollars_output=10,
        tokens_per_minute=2_000_000,
        request_per_minute=10,
    ),
    ModelInfo(
        name="claude-sonnet-4",
        provider="openrouter",
        backend="litellm",
        resolve_as="openrouter/anthropic/claude-sonnet-4",
        context_window=200_000,
        effective_context_window=64_000,
        max_output_tokens=32_000,
        effective_max_output_tokens=16_000,
        dollars_input=3,
        dollars_output=15,
        tokens_per_minute=20_000,
        request_per_minute=50,
    ),
    ModelInfo(
        name="claude-opus-4",
        provider="openrouter",
        backend="litellm",
        resolve_as="openrouter/anthropic/claude-opus-4",
        context_window=200_000,
        effective_context_window=64_000,
        max_output_tokens=32_000,
        effective_max_output_tokens=16_000,
        dollars_input=15,
        dollars_output=75,
        tokens_per_minute=20_000,
        request_per_minute=50,
        hidden=True,
    )
]

ALL_MODELS = [
    *MODELS_OPENAI,
    *MODELS_GOOGLE,
    *MODELS_ANTHROPIC,
    *MODELS_TOGETHERAI,
    *MODELS_OPENROUTER,
]
