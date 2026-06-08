import os
import re
import pandas as pd
from datetime import datetime, timezone
from agent.anonymizer import anonymize_text
from langdetect import detect, LangDetectException

REQUIRED_COLUMNS = ["id", "rating", "title", "text", "date", "source"]

# Emoji pattern (Unicode ranges for emojis)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u2640-\u2642"
    "\u2600-\u2B55"
    "\u200d"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\ufe0f"  # dingbats
    "\u3030"
    "]+"
)

THEME_KEYWORDS = {
    "Onboarding": ["login", "signup", "sign up", "otp", "verification", "kyc", "onboarding"],
    "KYC": ["kyc", "document", "verification", "aadhar", "pan", "identity", "id proof"],
    "Payments": ["payment", "charges", "refund", "deposit", "fund", "transaction", "upi", "bank"],
    "Statements": ["statement", "report", "portfolio", "balance", "holdings", "positions"],
    "Withdrawals": ["withdraw", "withdrawal", "payout", "redeem", "transfer", "exit"],
}

MIN_QUOTE_WORDS = 6

def load_reviews(file_path: str) -> pd.DataFrame:
    """
    Loads app reviews from a CSV or JSON file and standardizes the schema.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Review file not found at: {file_path}")

    _, ext = os.path.splitext(file_path.lower())
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext == '.json':
        df = pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only CSV and JSON are supported.")

    # Ensure all required columns are present
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Keep only the required columns
    df = df[REQUIRED_COLUMNS]

    # Clean data: fill empty string for text/title, convert IDs to string
    df["title"] = df["title"].fillna("").astype(str)
    df["text"] = df["text"].fillna("").astype(str)
    df["source"] = df["source"].fillna("unknown").astype(str)
    df["rating"] = pd.to_numeric(df["rating"], errors='coerce').fillna(3).astype(int)

    # Standardize dates to UTC datetimes
    df["date"] = pd.to_datetime(df["date"], errors='coerce')
    # If tzinfo is missing, localize to UTC
    if df["date"].dt.tz is None:
        df["date"] = df["date"].dt.tz_localize(timezone.utc)
    else:
        df["date"] = df["date"].dt.tz_convert(timezone.utc)

    # Drop reviews that couldn't be parsed with a date
    df = df.dropna(subset=["date"])

    return df

def filter_reviews_by_date(df: pd.DataFrame, weeks_ago_start: int = 12, weeks_ago_end: int = 8, current_date: datetime = None) -> pd.DataFrame:
    """
    Filters reviews within a window of weeks ago from current_date.
    By default, filters for reviews between 12 weeks ago (start) and 8 weeks ago (end).
    """
    if current_date is None:
        # Defaults to UTC now
        current_date = datetime.now(timezone.utc)
    elif current_date.tzinfo is None:
        current_date = current_date.replace(tzinfo=timezone.utc)

    start_delta = pd.Timedelta(weeks=weeks_ago_start)
    end_delta = pd.Timedelta(weeks=weeks_ago_end)

    start_threshold = current_date - start_delta
    end_threshold = current_date - end_delta

    # Filter dataframe
    filtered_df = df[(df["date"] >= start_threshold) & (df["date"] <= end_threshold)]
    return filtered_df.copy()

def process_and_anonymize_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies PII anonymization to the title and text columns of the review dataframe.
    """
    df = df.copy()
    df["title"] = df["title"].apply(anonymize_text)
    df["text"] = df["text"].apply(anonymize_text)
    return df

def remove_emojis(text: str) -> str:
    """
    Removes emoji characters from text.
    """
    if not isinstance(text, str):
        return text
    return EMOJI_PATTERN.sub(r'', text).strip()

def is_english(text: str, confidence_threshold: float = 0.5) -> bool:
    """
    Detects if text is in English using langdetect.
    Returns True if language is English or confidence is below threshold (ambiguous).
    """
    if not isinstance(text, str) or len(text.strip()) == 0:
        return False
    
    try:
        lang = detect(text)
        return lang == 'en'
    except LangDetectException:
        # If detection fails, assume it's English (ambiguous text)
        return True

def has_minimum_words(text: str, min_words: int = 6) -> bool:
    """
    Checks if text has at least min_words words.
    """
    if not isinstance(text, str):
        return False
    word_count = len(text.split())
    return word_count >= min_words

def clean_and_filter_reviews(df: pd.DataFrame, min_words: int = 6, remove_emoji: bool = True, english_only: bool = True) -> pd.DataFrame:
    """
    Applies comprehensive filtering and cleaning:
    - Removes emojis (optional)
    - Filters by minimum word count
    - Filters by language (English only, optional)
    """
    df = df.copy()
    
    # Remove emojis from text and title
    if remove_emoji:
        print("  • Removing emojis from reviews...")
        df["text"] = df["text"].apply(remove_emojis)
        df["title"] = df["title"].apply(remove_emojis)
    
    # Track filtering stats
    initial_count = len(df)
    
    # Filter by minimum word count
    print(f"  • Filtering by minimum word count ({min_words} words)...")
    df = df[df["text"].apply(lambda x: has_minimum_words(x, min_words))].copy()
    after_word_count = len(df)
    removed_word_count = initial_count - after_word_count
    print(f"    Removed {removed_word_count} reviews with < {min_words} words")
    
    # Filter by language (English only)
    if english_only:
        print("  • Filtering by language (English only)...")
        df["is_english"] = df["text"].apply(is_english)
        after_english = len(df[df["is_english"]])
        removed_non_english = len(df) - after_english
        df = df[df["is_english"]].copy()
        df = df.drop(columns=["is_english"])
        print(f"    Removed {removed_non_english} non-English reviews")
    
    final_count = len(df)
    print(f"  • Cleaning complete: {initial_count} → {final_count} reviews")
    print(f"    ({100 * final_count / initial_count:.1f}% retained)")
    
    return df
