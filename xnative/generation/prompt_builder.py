from typing import Any


def build_generation_context(event: dict[str, Any], style_examples: list[str]) -> str:
    examples = "\n".join(f"- {e}" for e in style_examples[:5])
    return (
        f"Event: {event}\nStyle examples:\n{examples}\n"
        "Rules: short Turkish X-native football language; no news tone."
    )
