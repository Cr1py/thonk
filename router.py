from .config import TIERS

# Laya answers a typed question about the text and returns a probability
QUESTIONS = {
    "difficulty": {
        "type": "choice",
        "instructions": "Classify the question into one of three difficulty tiers: easy, medium, or hard.",
        "criteria": {
            "easy": "simple fact, definition, greeting, or short lookup",
            "medium": "explanation, summary, routine code, or a standard multi-part task",
            "hard": "multi-step reasoning, complex math, system design, debugging, or deep analysis",
        },
    }
}


class LayaRouter:
    def __init__(self, checkpoint="convaiinnovations/laya", subfolder=None):
        import laya  # heavy import: torch + transformers

        kw = {"subfolder": subfolder} if subfolder else {}
        self.agent = laya.load(checkpoint, **kw)
        self.agent.predict("warm up", QUESTIONS)  # first call compiles kernels

    def classify(self, state: str) -> dict[str, float]:
        res = self.agent.predict(state, QUESTIONS)
        probs = res["answers"]["difficulty"]["probabilities"]
        return {t: float(probs.get(t, 0.0)) for t in TIERS}


class HeuristicRouter:
    """no model fallback (good for testing the rest of the pipeline)"""

    HARD_WORDS = (
        "why does",
        "can you",
        "how to",
        "explain",
        "step by step",
        "algorithm",
        "refactor",
        "debug",
        "design",
        "architecture",
        "optimize",
        "optimise",
        "analyze",
        "analyse",
    )

    def classify(self, state: str) -> dict[str, float]:
        text = state.split("\n\nContext:")[0].lower()
        n = len(text.split())
        score = 2 if n > 80 else 1 if n > 30 else 0
        score += sum(w in text for w in self.HARD_WORDS) + ("```" in text)
        if score >= 3:
            return {"easy": 0.05, "medium": 0.25, "hard": 0.70}
        if score >= 1:
            return {"easy": 0.20, "medium": 0.65, "hard": 0.15}
        return {"easy": 0.80, "medium": 0.15, "hard": 0.05}


def pick_tier(probs: dict[str, float], min_conf: float) -> tuple[str, str]:
    best = max(TIERS, key=lambda t: probs[t])
    if probs[best] < min_conf and best != "hard":
        up = TIERS[TIERS.index(best) + 1]
        return up, f"low confidence ({probs[best]:.2f}) in {best}, bumped to {up}"
    return best, f"top tier {best} ({probs[best]:.2f})"


def build_state(history: list[dict], message: str) -> str:
    """new message first (Laya favors the front), then a little recent context"""
    prior = [m["content"][:200] for m in history if m["role"] == "user"][-2:]
    state = message[:1200]
    if prior:
        state += "\n\nContext: " + " | ".join(prior)
    return state
