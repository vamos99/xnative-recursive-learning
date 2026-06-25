from __future__ import annotations

from xnative.core.config import settings


class OptionalLLMClient:
    """Optional free-tier/local refinement. Never required for MVP operation."""

    def available(self) -> bool:
        return settings.optional_llm_provider != "none" and bool(settings.optional_llm_api_key)

    def refine(self, text: str, context: str = "") -> tuple[str, str]:
        if not self.available():
            return text, "llm_unavailable_used_template_fallback"
        # No network call in default implementation. This keeps the project free/local-first.
        return text, "llm_disabled_in_safe_mvp"
