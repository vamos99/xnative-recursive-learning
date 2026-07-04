from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

from xnative.nlp.text_cleaner import clean_text


@dataclass(frozen=True)
class TextBenchmarkExample:
    text: str
    label: str
    observed_at: str
    source_id: str = ""


@dataclass(frozen=True)
class TextModelResult:
    model_name: str
    accuracy: float
    macro_f1: float
    train_seconds: float
    predict_seconds: float
    train_size: int
    test_size: int
    predictions: tuple[str, ...]
    skipped_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "model_name": self.model_name,
            "accuracy": self.accuracy,
            "macro_f1": self.macro_f1,
            "train_seconds": self.train_seconds,
            "predict_seconds": self.predict_seconds,
            "train_size": self.train_size,
            "test_size": self.test_size,
            "predictions": list(self.predictions),
            "skipped_reason": self.skipped_reason,
        }


@dataclass(frozen=True)
class TextBenchmarkReport:
    feature_version: str
    train_fraction: float
    class_counts: dict[str, int]
    leakage_audit: dict[str, object]
    results: tuple[TextModelResult, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "feature_version": self.feature_version,
            "train_fraction": self.train_fraction,
            "class_counts": self.class_counts,
            "leakage_audit": self.leakage_audit,
            "results": [result.as_dict() for result in self.results],
        }


def _normalized_hash(text: str) -> str:
    normalized = clean_text(text).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _time_ordered_split(
    examples: Sequence[TextBenchmarkExample],
    train_fraction: float,
) -> tuple[list[TextBenchmarkExample], list[TextBenchmarkExample]]:
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")
    if len(examples) < 4:
        raise ValueError("at least four examples are required for a time split")

    ordered = sorted(enumerate(examples), key=lambda item: (item[1].observed_at, item[0]))
    ordered_examples = [example for _, example in ordered]
    train_size = round(len(ordered_examples) * train_fraction)
    train_size = min(max(2, train_size), len(ordered_examples) - 1)
    return ordered_examples[:train_size], ordered_examples[train_size:]


def _leakage_audit(
    train_examples: Sequence[TextBenchmarkExample],
    test_examples: Sequence[TextBenchmarkExample],
) -> dict[str, object]:
    train_hashes = {_normalized_hash(example.text) for example in train_examples}
    test_hashes = {_normalized_hash(example.text) for example in test_examples}
    overlap = train_hashes & test_hashes
    return {
        "split_strategy": "time_ordered",
        "train_until": train_examples[-1].observed_at,
        "test_from": test_examples[0].observed_at,
        "overlap_text_hash_count": len(overlap),
        "leakage_warning": bool(overlap),
    }


def _model_specs(random_state: int) -> tuple[tuple[str, Any], ...]:
    return (
        (
            "tfidf_multinomial_nb",
            make_pipeline(
                TfidfVectorizer(ngram_range=(1, 2), min_df=1),
                MultinomialNB(),
            ),
        ),
        (
            "tfidf_logistic_regression",
            make_pipeline(
                TfidfVectorizer(ngram_range=(1, 2), min_df=1),
                LogisticRegression(max_iter=1000, random_state=random_state),
            ),
        ),
        (
            "hashing_sgd_logistic",
            make_pipeline(
                HashingVectorizer(
                    n_features=2**12,
                    alternate_sign=False,
                    ngram_range=(1, 2),
                ),
                SGDClassifier(
                    loss="log_loss",
                    alpha=0.0001,
                    max_iter=2000,
                    random_state=random_state,
                    tol=1e-3,
                ),
            ),
        ),
    )


def benchmark_text_classifiers(
    examples: Sequence[TextBenchmarkExample],
    *,
    train_fraction: float = 0.67,
    random_state: int = 13,
) -> TextBenchmarkReport:
    train_examples, test_examples = _time_ordered_split(examples, train_fraction)
    train_texts = [example.text for example in train_examples]
    train_labels = [example.label for example in train_examples]
    test_texts = [example.text for example in test_examples]
    test_labels = [example.label for example in test_examples]
    class_counts = dict(Counter(example.label for example in examples))
    train_class_count = len(set(train_labels))
    results: list[TextModelResult] = []

    for model_name, estimator in _model_specs(random_state):
        if train_class_count < 2:
            results.append(
                TextModelResult(
                    model_name=model_name,
                    accuracy=0.0,
                    macro_f1=0.0,
                    train_seconds=0.0,
                    predict_seconds=0.0,
                    train_size=len(train_examples),
                    test_size=len(test_examples),
                    predictions=(),
                    skipped_reason="train_split_has_single_class",
                )
            )
            continue

        train_start = perf_counter()
        estimator.fit(train_texts, train_labels)
        train_seconds = perf_counter() - train_start
        predict_start = perf_counter()
        predictions = tuple(str(label) for label in estimator.predict(test_texts))
        predict_seconds = perf_counter() - predict_start
        results.append(
            TextModelResult(
                model_name=model_name,
                accuracy=float(accuracy_score(test_labels, predictions)),
                macro_f1=float(
                    f1_score(test_labels, predictions, average="macro", zero_division=0)
                ),
                train_seconds=train_seconds,
                predict_seconds=predict_seconds,
                train_size=len(train_examples),
                test_size=len(test_examples),
                predictions=predictions,
            )
        )

    return TextBenchmarkReport(
        feature_version="text-benchmark-v1",
        train_fraction=train_fraction,
        class_counts=class_counts,
        leakage_audit=_leakage_audit(train_examples, test_examples),
        results=tuple(results),
    )
