from __future__ import annotations

from dataclasses import dataclass

from .embeddings import SimilarityIndex


@dataclass
class StyleExample:
    text: str
    tone_tags: str = ""
    performance_score: float = 50.0


class StyleMemory:
    def __init__(self, examples: list[StyleExample] | None = None):
        self.examples = examples or []
        self._rebuild()

    def _rebuild(self) -> None:
        self.index = SimilarityIndex([e.text for e in self.examples])

    def add(self, text: str, tone_tags: str = "", performance_score: float = 50.0) -> None:
        self.examples.append(StyleExample(text, tone_tags, performance_score))
        self._rebuild()

    def retrieve(self, query: str, top_k: int = 5) -> list[StyleExample]:
        hits = self.index.search(query, top_k)
        return [self.examples[i] for i, _, _ in hits]
