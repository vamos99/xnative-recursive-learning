import pytest

from xnative.evaluation import TextBenchmarkExample, benchmark_text_classifiers


def _examples() -> list[TextBenchmarkExample]:
    return [
        TextBenchmarkExample("Gol pozisyonu ve tribün baskısı", "football", "2026-01-01T10:00:00Z"),
        TextBenchmarkExample("Yeni telefon kamerası tanıtıldı", "other", "2026-01-01T10:01:00Z"),
        TextBenchmarkExample(
            "Transfer iddiası taraftarı hareketlendirdi",
            "football",
            "2026-01-01T10:02:00Z",
        ),
        TextBenchmarkExample("Bulut maliyet raporu açıklandı", "other", "2026-01-01T10:03:00Z"),
        TextBenchmarkExample(
            "Hakem kararı maçın ritmini bozdu",
            "football",
            "2026-01-01T10:04:00Z",
        ),
        TextBenchmarkExample("Kahve zinciri yeni menü deniyor", "other", "2026-01-01T10:05:00Z"),
        TextBenchmarkExample(
            "Saha içi pres ve skor beklentisi",
            "football",
            "2026-01-01T10:06:00Z",
        ),
        TextBenchmarkExample("Yerel seçim anketi yayınlandı", "other", "2026-01-01T10:07:00Z"),
    ]


def test_text_benchmark_runs_classic_models_with_time_split() -> None:
    report = benchmark_text_classifiers(
        _examples(),
        train_fraction=0.5,
        learning_curve_fractions=(0.5, 0.75),
    )

    assert report.feature_version == "text-benchmark-v1"
    assert report.class_counts == {"football": 4, "other": 4}
    assert report.leakage_audit["split_strategy"] == "time_ordered"
    assert report.leakage_audit["train_until"] == "2026-01-01T10:03:00Z"
    assert report.leakage_audit["test_from"] == "2026-01-01T10:04:00Z"
    assert report.leakage_audit["overlap_text_hash_count"] == 0
    assert {result.model_name for result in report.results} == {
        "tfidf_multinomial_nb",
        "tfidf_logistic_regression",
        "hashing_sgd_logistic",
    }
    for result in report.results:
        assert result.train_size == 4
        assert result.test_size == 4
        assert result.skipped_reason is None
        assert len(result.predictions) == 4
        assert 0.0 <= result.accuracy <= 1.0
        assert 0.0 <= result.macro_f1 <= 1.0
    assert [point.train_fraction for point in report.learning_curve] == [0.5, 0.75]
    assert [point.train_size for point in report.learning_curve] == [4, 6]
    assert all(point.best_model_name for point in report.learning_curve)
    assert all(0.0 <= point.best_macro_f1 <= 1.0 for point in report.learning_curve)
    assert report.as_dict()["learning_curve"]


def test_text_benchmark_reports_duplicate_text_leakage_warning() -> None:
    examples = _examples()
    examples[-1] = TextBenchmarkExample(
        text=examples[0].text,
        label="football",
        observed_at="2026-01-01T10:07:00Z",
    )

    report = benchmark_text_classifiers(
        examples,
        train_fraction=0.5,
        learning_curve_fractions=(0.5,),
    )

    assert report.leakage_audit["overlap_text_hash_count"] == 1
    assert report.leakage_audit["leakage_warning"] is True


def test_text_benchmark_requires_enough_examples() -> None:
    with pytest.raises(ValueError, match="at least four examples"):
        benchmark_text_classifiers(_examples()[:3])
