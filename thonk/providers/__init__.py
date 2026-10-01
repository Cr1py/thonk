def build_provider(cfg):
    if cfg.provider == "openai_compat":
        from .openai_compat import OpenAICompat

        return OpenAICompat(cfg)
    if cfg.provider == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(cfg)
    raise ValueError(f"{cfg.name}: unknown provider {cfg.provider!r}")
