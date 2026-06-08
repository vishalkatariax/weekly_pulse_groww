import os
import pandas as pd
from datetime import datetime, timezone
import pytest

from agent.anonymizer import anonymize_text
from agent.ingestion import load_reviews, filter_reviews_by_date, process_and_anonymize_reviews

def test_anonymize_text_emails():
    text = "Contact me at test@example.com or support@groww.co.in"
    anonymized = anonymize_text(text)
    assert "[REDACTED_EMAIL]" in anonymized
    assert "@" not in anonymized

def test_anonymize_text_phones():
    text = "Call +91 9876543210 or 8877665544 for help"
    anonymized = anonymize_text(text)
    assert "[REDACTED_PHONE]" in anonymized
    assert "9876543210" not in anonymized

def test_anonymize_text_handles():
    text = "Ping @groww_support or @my_handle_123"
    anonymized = anonymize_text(text)
    assert "[REDACTED_USER]" in anonymized
    assert "@" not in anonymized

def test_anonymize_text_user_ids():
    cases = [
        "User ID: 1293819",
        "user id 9923",
        "ID-99238",
        "user_id: 11203"
    ]
    for case in cases:
        anonymized = anonymize_text(case)
        assert "[REDACTED_ID]" in anonymized
        assert any(char.isdigit() for char in case) # Original had digits
        # The anonymized string shouldn't contain the raw digits of the ID
        raw_digits = "".join(filter(str.isdigit, case))
        assert raw_digits not in anonymized

def test_load_reviews_schema():
    csv_path = "data/mock_reviews.csv"
    assert os.path.exists(csv_path), "mock_reviews.csv must exist"
    
    df = load_reviews(csv_path)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    
    # Check all columns exist
    expected_cols = ["id", "rating", "title", "text", "date", "source"]
    for col in expected_cols:
        assert col in df.columns

def test_filter_reviews_by_date():
    csv_path = "data/mock_reviews.csv"
    df = load_reviews(csv_path)
    
    # We will simulate a current run date of June 4, 2026
    current_date = datetime(2026, 6, 4, tzinfo=timezone.utc)
    
    # Filter 8 to 12 weeks ago (from Jun 4, 2026)
    # 12 weeks ago = Mar 12, 2026. 8 weeks ago = Apr 9, 2026.
    filtered = filter_reviews_by_date(df, weeks_ago_start=12, weeks_ago_end=8, current_date=current_date)
    
    # Let's verify that the dates fall in that range
    start_bound = datetime(2026, 3, 12, tzinfo=timezone.utc)
    end_bound = datetime(2026, 4, 9, tzinfo=timezone.utc)
    
    for dt in filtered["date"]:
        assert start_bound <= dt <= end_bound

def test_process_and_anonymize_reviews():
    csv_path = "data/mock_reviews.csv"
    df = load_reviews(csv_path)
    
    anonymized_df = process_and_anonymize_reviews(df)
    
    # Verify no emails, handles, or phone numbers in the text column
    for text in anonymized_df["text"]:
        assert "@" not in text
        assert "9876543210" not in text
        assert "User ID" not in text
