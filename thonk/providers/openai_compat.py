import os
from openai import OpenAI

from .base import Response


class OpenAICompat:
    """covers OpenAI, DeepSeek, Qwen, Grok, and other OpenAI compatible APIs"""

    def __init__(self, cfg):
        self.cfg = cfg
        self.client = OpenAI(
            api_key=os.environ[cfg.api_key_env], base_url=cfg.base_url, timeout=60
        )

    def ask(self, messages: list[dict]) -> Response:
        r = self.client.chat.completions.create(
            model=self.cfg.model,
            messages=messages,
            **{self.cfg.token_param: self.cfg.max_tokens},
        )
        u = r.usage
        return Response(
            text=r.choices[0].message.content or "",
            model=self.cfg.model,
            input_tokens=getattr(u, "prompt_tokens", 0) or 0,
            output_tokens=getattr(u, "completion_tokens", 0) or 0,
        )
