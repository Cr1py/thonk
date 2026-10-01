import os
from dataclasses import dataclass
from pathlib import Path

import yaml

TIERS = ["easy", "medium", "hard"]


@dataclass
class ModelCfg:
    name: str
    tier: str
    provider: str
    model: str
    api_key_env: str
    base_url: str | None = None
    enabled: bool = True
    max_tokens: int = 1024
    token_param: str = "max_tokens"

    def problem(self) -> str | None:
        """return why this model can't be used, or None if it's ready"""
        if not self.enabled:
            return "disabled"
        if self.model.startswith("CHANGE_ME"):
            return "model id not set"
        if self.base_url and self.base_url.startswith("CHANGE_ME"):
            return "base_url not set"
        if not os.environ.get(self.api_key_env):
            return f"{self.api_key_env} not set"
        return None


def load_config(path: Path) -> tuple[dict, list[ModelCfg]]:
    data = yaml.safe_load(Path(path).read_text())
    models = [ModelCfg(**m) for m in data["models"]]
    for m in models:
        if m.tier not in TIERS:
            raise ValueError(f"{m.name}: unknown tier {m.tier!r}")
    return data.get("router", {}), models
