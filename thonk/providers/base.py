from dataclasses import dataclass


@dataclass
class Response:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency: float = 0.0
