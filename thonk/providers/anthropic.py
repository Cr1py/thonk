import os
import thonk.providers.anthropic as anthropic

from .base import Response


class AnthropicProvider:
    """covers Claude APIs"""

    def __init__(self, cfg):
        self.cfg = cfg
        self.client = anthropic.Anthropic(
            api_key=os.environ[cfg.api_key_env], timeout=60
        )

    def ask(self, messages: list[dict]) -> Response:
        r = self.client.messages.create(
            model=self.cfg.model, max_tokens=self.cfg.max_tokens, messages=messages
        )
        text = "".join(b.text for b in r.content if b.type == "text")
        return Response(
            text=text,
            model=self.cfg.model,
            input_tokens=r.usage.input_tokens,
            output_tokens=r.usage.output_tokens,
        )
