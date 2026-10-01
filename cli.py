from pathlib import Path

import typer

from .config import TIERS, load_config
from .engine import AllFailed, Engine
from .providers import build_provider
from .router import HeuristicRouter, LayaRouter, build_state

app = typer.Typer(
    add_completion=False, help="Route questions to the right LLM by difficulty."
)
CONFIG = typer.Option(Path("registry.yaml"), "--config", "-c")

HELP = "/tier easy|medium|hard|auto  /verbose  /models  /clear  /quit"


@app.command()
def models(config: Path = CONFIG):
    """show every model and whether it's ready to use or not"""
    _, cfgs = load_config(config)
    for t in TIERS:
        for c in (c for c in cfgs if c.tier == t):
            status = c.problem() or "ready"
            typer.echo(f"{t:7} {c.name:10} {c.model:28} {status}")


@app.command()
def chat(
    config: Path = CONFIG,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    heuristic: bool = typer.Option(
        False, "--heuristic", help="Skip Laya; use simple rules"
    ),
):
    """interactive chat: each message is classified and routed"""
    router_cfg, cfgs = load_config(config)
    providers = []
    for c in cfgs:
        if why := c.problem():
            typer.echo(f"  skipping {c.name}: {why}")
        else:
            providers.append(build_provider(c))
    if not providers:
        raise typer.Exit("No usable models. Run 'thonk models' to see what's missing.")

    if heuristic:
        router = HeuristicRouter()
    else:
        try:
            typer.echo("Loading Laya (25-35 s the first time)...")
            router = LayaRouter(
                router_cfg.get("checkpoint", "convaiinnovations/laya"),
                router_cfg.get("subfolder"),
            )
        except ImportError:
            typer.echo(
                "Laya not installed (pip install '.[laya]'); using heuristic router."
            )
            router = HeuristicRouter()

    engine = Engine(
        providers, router, router_cfg.get("min_confidence", 0.6), "logs/routes.jsonl"
    )
    history, forced = [], None
    typer.echo(f"Ready. {HELP}")

    while True:
        try:
            msg = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg:
            continue
        if msg.startswith("/"):
            cmd, *arg = msg[1:].split()
            if cmd in ("quit", "exit"):
                break
            elif cmd == "verbose":
                verbose = not verbose
                typer.echo(f"verbose {'on' if verbose else 'off'}")
            elif cmd == "clear":
                history.clear()
                typer.echo("history cleared")
            elif cmd == "tier" and arg and (arg[0] in TIERS or arg[0] == "auto"):
                forced = None if arg[0] == "auto" else arg[0]
                typer.echo(f"tier: {arg[0]}")
            elif cmd == "models":
                for t in TIERS:
                    typer.echo(f"{t}: {[p.cfg.name for p in engine.by_tier[t]]}")
            else:
                typer.echo(HELP)
            continue

        state = build_state(history, msg)
        history.append({"role": "user", "content": msg})
        try:
            r, info = engine.answer(history, state, forced)
        except AllFailed as e:
            history.pop()
            typer.echo(f"All models failed: {e}")
            continue
        history.append({"role": "assistant", "content": r.text})

        typer.echo(f"\n{r.text}")
        tag = f"{info['model']} · {info['answered_tier']} · {r.latency:.1f}s"
        if verbose:
            if info["probs"]:
                tag += " · " + " ".join(
                    f"{k}={v:.2f}" for k, v in info["probs"].items()
                )
            tag += f" · {info['why']}"
            for t, m, err in info["failed"]:
                tag += f"\n  failed {m} ({t}): {err[:120]}"
        typer.echo(f"[{tag}]")


if __name__ == "__main__":
    app()
