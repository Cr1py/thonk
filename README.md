# thonk
Current Project (WIP): Simple and convenient cli that allows users to quickly ask questions and receive answers directly from the terminal.

## What Does it Do?? (Currently)
 
1. 

## Current Demo Images


## Current To Do:


## Tech stack & key dependencies

| Package | Purpose |
|---|---|


## Project structure
 
```
llmroute/
├── cli.py                   # typer app: ask, chat, models, eval
├── router.py                # Laya wrapper: load once, warm up, classify
├── registry.yaml            # models, tiers, API settings, env var names
├── providers/
│   ├── base.py              # ask(prompt) -> Response
│   ├── anthropic.py    
│   └── openai_compat.py     # covers OpenAI, DeepSeek, Qwen (OpenAI-style APIs)
├── escalation.py            # retry and next-tier logic
├── evalset/                 # labelled questions for testing the router
└── logs/                    # route decisions, latency, cost 

```
