import pandas as pd

from agent.phase2 import assign_theme, sample_reviews, sentiment_bucket, run_phase2


def test_assign_theme_keyword_match():
    assert assign_theme("I am stuck in KYC verification process") == "KYC"
    assert assign_theme("Payment failed while depositing funds") == "Payments"
    assert assign_theme("Unable to withdraw money from account") == "Withdrawals"
    assert assign_theme("Need help with login and OTP") == "Onboarding"
    assert assign_theme("My portfolio statement is incorrect") == "Statements"


def test_sentiment_bucket():
    assert sentiment_bucket(1) == "negative"
    assert sentiment_bucket(2) == "negative"
    assert sentiment_bucket(3) == "neutral"
    assert sentiment_bucket(4) == "positive"
    assert sentiment_bucket(5) == "positive"


def test_sample_reviews_prioritizes_negative_reviews():
    df = pd.DataFrame([
        {"id": "1", "text": "payment failed", "rating": 1, "title": "", "date": pd.Timestamp("2026-06-01"), "source": "google_play"},
        {"id": "2", "text": "great app", "rating": 5, "title": "", "date": pd.Timestamp("2026-06-01"), "source": "google_play"},
        {"id": "3", "text": "withdraw request not processed", "rating": 1, "title": "", "date": pd.Timestamp("2026-06-01"), "source": "google_play"},
        {"id": "4", "text": "nice experience", "rating": 4, "title": "", "date": pd.Timestamp("2026-06-01"), "source": "google_play"},
    ])
    sampled = sample_reviews(df, target_size=2)
    assert len(sampled) == 2
    assert "1" in sampled["id"].astype(str).values
    assert "3" in sampled["id"].astype(str).values


def test_run_phase2_dry_run_creates_summary(tmp_path, monkeypatch):
    # Create a small anonymized CSV sample for Phase 2
    csv_path = tmp_path / "sample_reviews.csv"
    df = pd.DataFrame([
        {"id": "1", "rating": 1, "title": "Poor payment", "text": "payment failed with charges", "date": "2026-06-01", "source": "google_play"},
        {"id": "2", "rating": 5, "title": "Great app", "text": "app is very easy to use", "date": "2026-06-02", "source": "google_play"},
    ])
    df.to_csv(csv_path, index=False)

    output = run_phase2(input_csv=str(csv_path), output_dir=str(tmp_path), sample_size=10, dry_run=True)
    assert output["phase"] == 2
    assert output["review_count"] == 2
    assert output["sampled_count"] == 2
    assert "theme_analysis" in output
    assert "summary" in output
    assert output["summary"]["dry_run"] is True
