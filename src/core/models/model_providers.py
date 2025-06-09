from core.models.objects import ModelProviderInfo


MODEL_PROVIDERS = [
    ModelProviderInfo(name="openai", env="OPENAI_API_KEY", priority=1),
    ModelProviderInfo(name="google", env="GEMINI_API_KEY", priority=1),
    ModelProviderInfo(name="anthropic", env="ANTHROPIC_API_KEY", priority=1),
    ModelProviderInfo(name="togetherai", env="TOGETHERAI_API_KEY", priority=1),
    ModelProviderInfo(name="openrouter", env="OPENROUTER_API_KEY", priority=0),
]
