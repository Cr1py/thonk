# thonk
Simple and convenient cli that allows users to quickly ask questions and sends each question to the LLM best suited for it. A local classifier (Laya) rates how hard your question is, and thonk forwards it to a model in the matching tier (cheap and fast models for easy questions, stronger ones for hard questions). If a model fails, the question moves up to the next tier automatically.

Since most questions don't need a flagship model, sending easier questions to the most capable model is a waste of tokens and MONEY, so thonk is here to make sure I don't waste money.

## What Does it Do??

```
                 ┌───────────────────────────────┐
  your message → │ Laya (runs locally, ~ms)      │
                 │ P(easy), P(medium), P(hard)   │
                 └──────────────┬────────────────┘
                                │ pick tier (low confidence → bump up one tier)
                                V
        ┌───────────┐     ┌───────────┐     ┌───────────┐
        │   easy    │ --> │   easy    │ --> │   hard    │
        │   qwen    │     │  gemini   │     │  claude   │
        │   grok    │     │ deepseek  │     │  chatgpt  │
        └───────────┘     └───────────┘     └───────────┘
            models in a tier take turns (round-robin)
      on error, try the next model, then the next tier up
```
 
1. Each message is sent to Laya, an open-source classifier that runs on your machine. Laya answers a typed question about a piece of text and returns a probability for each option.
2. The tier with the highest probability wins. However, if that probability is below `min_confidence` (default 0.60) and the tier isn't currently set to hard, the question is bumped up one tier. For example, if a question scores 45% easy / 40% medium / 15% hard it is routed to medium, because when the classifier is unsure it is cheaper to over-serve a question than to give a weak answer or wrong answer.
3. Within a tier, models take turns round-robin style to spread load, which also helps with rate limits. If a call fails for any reason (rate limit, timeout, auth error, outage), the next model in that tier is tried. When a tier is exhausted, the question moves up to the next tier. Lower tiers are tried only if everything at and above the chosen tier has failed. If every model fails, you get an error listing each failure and the question is removed from the history, so you can retry again.
4. The full conversation is sent to whichever model answers, so you can switch models mid-chat without losing context. History lives in memory for the session. `/clear` resets it.


## Tech stack & key dependencies

| Package | Purpose |
|---|---|
| Python 3.10+ | Language and runtime |
| [`typer`](https://typer.tiangolo.com) | Command-line interface |
| [`pyyaml`](https://pyyaml.org) | Parses `registry.yaml` (models, tiers, router settings) |
| [`openai`](https://github.com/openai/openai-python) | Client for OpenAI and any OpenAI-compatible API (Gemini, DeepSeek, Qwen, Grok, etc) |
| [`anthropic`](https://github.com/anthropics/anthropic-sdk-python) | Client for the Claude API |
| [`laya`](https://brainfunctioncollapse.com/laya) | Local difficulty classifier that returns easy/medium/hard probabilities |
| `torch`, `transformers` | Run the Laya model locally on CUDA, Apple MPS, or CPU |
| `setuptools` | Packaging, so `pip install -e .` creates the `thonk` command |


## Project structure
 
```

thonk/ 
├── pyproject.toml                        #
├── registry.yaml                         # models, tiers, API settings, env var names
├── README.md
├── evalset/                              # labelled questions for testing the router
├── logs/                                 # logs route decisions, latency, cost, errors 
└── thonk/
    ├── __init__.py                       # empty
    ├── cli.py                            # typer app: ask, chat, models (builds the CLI) 
    ├── config.py                         # models and loads config
    ├── router.py                         # Laya wrapper: load once, warm up, classify
    ├── engine.py                         # routing, round-robin, escalation, logging
    └── providers/
        ├── __init__.py
        ├── base.py                       # ask(prompt) -> response
        ├── anthropic_provider.py
        └── openai_compat.py              # covers OpenAI style APIs (DeepSeek, Qwen, Grok) 


```
