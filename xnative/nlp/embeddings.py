from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimilarityIndex:
    """Small local similarity index. Uses TF-IDF fallback by default."""

    def __init__(self, texts: list[str] | None = None):
        self.texts = texts or []
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.matrix = self.vectorizer.fit_transform(self.texts) if self.texts else None

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float, str]]:
        if not self.texts or self.matrix is None:
            return []
        q = self.vectorizer.transform([query])
        sims = cosine_similarity(q, self.matrix)[0]
        ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)[:top_k]
        return [(i, float(s), self.texts[i]) for i, s in ranked]
