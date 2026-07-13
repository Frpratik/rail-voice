import pytest

from app.ai.categorizer import issue_categorizer
from app.ai.duplicate import effective_duplicate_threshold
from app.ai.embeddings import embedding_service
from app.ai.spam import spam_detector
from app.ai.summarizer import issue_summarizer
from app.ai.trending import compute_trending_score
from datetime import datetime, timezone, timedelta


def test_embedding_paraphrase_beats_unrelated():
    text_a = "There should be a dustbin near Platform 2 bridge at Bandra."
    text_b = "Garbage bins are missing beside the foot over bridge on Bandra Platform 2"
    unrelated_text = "Train delay on Central line due to signal failure at Kurla."

    from app.ai.duplicate import _combined_similarity

    a = embedding_service._local_embedding(text_a)
    b = embedding_service._local_embedding(text_b)
    u = embedding_service._local_embedding(unrelated_text)

    paraphrase_sim = _combined_similarity(a, b, text_a, text_b)
    unrelated_sim = _combined_similarity(a, u, text_a, unrelated_text)
    assert paraphrase_sim > unrelated_sim
    assert paraphrase_sim >= effective_duplicate_threshold()


def test_categorizer_dustbin():
    result = issue_categorizer.predict(
        "Garbage bins are missing beside the foot over bridge on Bandra Platform 2"
    )
    assert result.category_code == "station_infrastructure"
    assert result.confidence > 0.5


def test_spam_detector_clean():
    result = spam_detector.predict(
        "The escalator at Andheri station east side has been broken for two weeks.",
        is_anonymous=False,
    )
    assert result.is_auto_hold is False
    assert result.spam_score < 0.5


def test_spam_detector_spam():
    result = spam_detector.predict("buy now click here http://spam.com free money")
    assert result.spam_score >= 0.5


def test_summarizer():
    text = "Broken lift near ticket counter. Passengers with luggage cannot access platform."
    summary = issue_summarizer.summarize(text)
    assert len(summary) <= 160
    assert "lift" in summary.lower() or "Broken" in summary


def test_trending_score():
    now = datetime.now(timezone.utc)
    score = compute_trending_score(
        support_count=100,
        supports_24h=30,
        supports_7d=60,
        created_at=now - timedelta(hours=6),
    )
    assert 0 < score <= 1.0
