import json
import time
from pathlib import Path

from .config import TIERS
from .router import pick_tier


class AllFailed(Exception):
    def __init__(self, attempts):
        super().__init__("; ".join(f"{m}: {e}" for _, m, e in attempts))
        self.attempts = attempts


class Engine:
    def __init__(self, providers, router, min_conf=0.6, log_path=None):
        self.by_tier = {t: [p for p in providers if p.cfg.tier == t] for t in TIERS}
        self.counters = {t: 0 for t in TIERS}
        self.router, self.min_conf = router, min_conf
        self.log_path = Path(log_path) if log_path else None

    def _order(self, tier):
        i = TIERS.index(tier)
        # escalate upward first, fall back to lower tiers only as a last resort
        return TIERS[i:] + TIERS[:i][::-1]

    def answer(self, history, state, forced_tier=None):
        probs = None
        if forced_tier:
            tier, why = forced_tier, "forced"
        else:
            probs = self.router.classify(state)
            tier, why = pick_tier(probs, self.min_conf)

        attempts = []  # (tier, model, error)
        for t in self._order(tier):
            provs = self.by_tier[t]
            if not provs:
                continue
            start = self.counters[t] % len(provs)  # round robin a tier
            self.counters[t] += 1
            for k in range(len(provs)):
                p = provs[(start + k) % len(provs)]
                t0 = time.time()
                try:
                    r = p.ask(history)
                except Exception as e:  # rate limit, timeout, auth, outage
                    attempts.append((t, p.cfg.name, f"{type(e).__name__}: {e}"))
                    continue
                r.latency = time.time() - t0
                info = {
                    "chosen_tier": tier,
                    "answered_tier": t,
                    "model": p.cfg.name,
                    "probs": probs,
                    "why": why,
                    "failed": attempts,
                }
                self._log(info, r)
                return r, info
        raise AllFailed(attempts)

    def _log(self, info, r):
        if not self.log_path:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": time.time(),
            **info,
            "latency": round(r.latency, 2),
            "in": r.input_tokens,
            "out": r.output_tokens,
        }
        with self.log_path.open("a") as f:
            f.write(json.dumps(row) + "\n")
