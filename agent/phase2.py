import json
import os
import random
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd

from agent.llm_client import LLMClient
from agent.assembler import assemble_final_pulse, build_output_payload

THEME_KEYWORDS = {
    "Onboarding": ["login", "signup", "sign up", "otp", "onboarding", "user id", "create account", "sign in"],
    "KYC": ["kyc", "document", "verification", "aadhar", "pan", "identity", "id proof", "kyc verification"],
    "Payments": ["payment", "charges", "refund", "deposit", "fund", "transaction", "upi", "bank", "collect"],
    "Statements": ["statement", "report", "portfolio", "balance", "holdings", "positions", "expense", "pnl"],
    "Withdrawals": ["withdraw", "withdrawal", "payout", "redeem", "transfer", "exit", "settlement"],
}

SENTIMENT_BUCKETS = {
    "negative": [1, 2],
    "neutral": [3],
    "positive": [4, 5],
}

BATCH_TOKEN_LIMIT = 1500
DEFAULT_SAMPLE_SIZE = 1000
MIN_QUOTES_PER_THEME = 2
MAX_QUOTES_PER_THEME = 3


def load_anonymized_reviews(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Anonymized review file not found: {file_path}")
    df = pd.read_csv(file_path, parse_dates=["date"])
    return df


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text.strip())


def estimate_tokens_for_prompt(prompt_text: str) -> int:
    return max(1, len(prompt_text.split()))


def sentiment_bucket(rating: int) -> str:
    for bucket, values in SENTIMENT_BUCKETS.items():
        if rating in values:
            return bucket
    return "neutral"


def theme_score(text: str) -> Dict[str, int]:
    text_lower = text.lower()
    scores = {}
    for theme, keywords in THEME_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                score += text_lower.count(keyword)
        scores[theme] = score
    return scores


def assign_theme(text: str) -> str:
    scores = theme_score(text)
    top_theme = max(scores, key=scores.get)
    if scores[top_theme] == 0:
        return "Other"
    return top_theme


def select_representative_quotes(df: pd.DataFrame, theme: str, max_quotes: int = MAX_QUOTES_PER_THEME) -> List[Dict]:
    theme_reviews = df[df["theme"] == theme].copy()
    if theme_reviews.empty:
        return []

    theme_reviews["length"] = theme_reviews["text"].astype(str).apply(lambda t: len(t.split()))
    theme_reviews["priority"] = theme_reviews.apply(
        lambda row: ((3 - row["rating"]) * 10) + row["length"], axis=1
    )
    theme_reviews = theme_reviews.sort_values(by=["priority", "rating"], ascending=[False, True])
    quotes = []
    seen_texts = set()
    for _, row in theme_reviews.iterrows():
        text = normalize_text(row["text"])
        if text in seen_texts:
            continue
        seen_texts.add(text)
        quotes.append({
            "id": row["id"],
            "rating": int(row["rating"]),
            "sentiment": sentiment_bucket(int(row["rating"])),
            "text": text,
        })
        if len(quotes) >= max_quotes:
            break
    return quotes


def build_theme_counts(df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
    theme_counts = {}
    for theme in list(THEME_KEYWORDS.keys()) + ["Other"]:
        theme_df = df[df["theme"] == theme]
        theme_counts[theme] = {
            "negative": int((theme_df["rating"].isin(SENTIMENT_BUCKETS["negative"])) .sum()),
            "neutral": int((theme_df["rating"].isin(SENTIMENT_BUCKETS["neutral"])) .sum()),
            "positive": int((theme_df["rating"].isin(SENTIMENT_BUCKETS["positive"])) .sum()),
            "total": int(len(theme_df)),
        }
    return theme_counts


def extract_top_terms(df: pd.DataFrame, top_n: int = 5) -> List[str]:
    words = Counter()
    for text in df["text"].astype(str).tolist():
        tokens = re.findall(r"[A-Za-z']+", text.lower())
        words.update([tok for tok in tokens if len(tok) > 3])
    return [word for word, _ in words.most_common(top_n)]


def sample_reviews(df: pd.DataFrame, target_size: int = DEFAULT_SAMPLE_SIZE) -> pd.DataFrame:
    df = df.copy()
    df["word_count"] = df["text"].astype(str).apply(lambda t: len(str(t).split()))
    keywords = [k for v in THEME_KEYWORDS.values() for k in v]
    df["keyword_hits"] = df["text"].astype(str).apply(
        lambda p: sum(p.lower().count(k) for k in keywords)
    )
    df["importance"] = df.apply(
        lambda row: ((3 - row["rating"]) * 20) + row["keyword_hits"] * 5 + row["word_count"],
        axis=1,
    )
    df = df.sort_values(by=["importance", "rating", "word_count"], ascending=[False, True, False])
    sampled = df.head(target_size).copy()
    return sampled.drop(columns=["word_count", "keyword_hits", "importance"])


def build_theme_payload(theme: str, df: pd.DataFrame) -> Dict:
    theme_df = df[df["theme"] == theme]
    quotes = select_representative_quotes(df, theme, max_quotes=MAX_QUOTES_PER_THEME)
    top_terms = extract_top_terms(theme_df)
    counts = {
        "negative": int((theme_df["rating"].isin(SENTIMENT_BUCKETS["negative"])) .sum()),
        "neutral": int((theme_df["rating"].isin(SENTIMENT_BUCKETS["neutral"])) .sum()),
        "positive": int((theme_df["rating"].isin(SENTIMENT_BUCKETS["positive"])) .sum()),
        "total": int(len(theme_df)),
    }
    return {
        "theme": theme,
        "counts": counts,
        "top_terms": top_terms,
        "quotes": quotes,
    }


def build_batch_payloads(theme_payloads: List[Dict], token_limit: int = BATCH_TOKEN_LIMIT) -> List[List[Dict]]:
    batches = []
    current_batch = []
    current_tokens = 0
    for payload in theme_payloads:
        payload_text = json.dumps(payload, ensure_ascii=False)
        estimate = estimate_tokens_for_prompt(payload_text)
        if current_batch and current_tokens + estimate > token_limit:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0
        current_batch.append(payload)
        current_tokens += estimate
    if current_batch:
        batches.append(current_batch)
    return batches


def load_prompt_template(filename: str) -> Optional[str]:
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", filename)
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as prompt_file:
            return prompt_file.read().strip()
    return None


def build_theme_summary_prompt(theme_payload: Dict) -> str:
    template = load_prompt_template("phase2_theme_prompt.txt")
    quotes_text = "\n".join([f"- [{quote['sentiment']}] {quote['text']}" for quote in theme_payload["quotes"]])
    if template:
        return template + "\n\n" + (
            f"Theme: {theme_payload['theme']}\n"
            f"Counts: negative={theme_payload['counts']['negative']}, neutral={theme_payload['counts']['neutral']}, positive={theme_payload['counts']['positive']}, total={theme_payload['counts']['total']}\n"
            f"Top terms: {', '.join(theme_payload['top_terms'])}\n"
            f"Quotes:\n{quotes_text}\n"
        )
    return (
        "Write a concise summary (1-2 sentences) for the theme and a short recommendation for the product team. "
        "Use the provided counts and quotes.\n\n"
        f"Theme: {theme_payload['theme']}\n"
        f"Counts: negative={theme_payload['counts']['negative']}, neutral={theme_payload['counts']['neutral']}, positive={theme_payload['counts']['positive']}, total={theme_payload['counts']['total']}\n"
        f"Top terms: {', '.join(theme_payload['top_terms'])}\n"
        f"Quotes:\n{quotes_text}\n\n"
        "Output format:\nSummary: <short summary>\nRecommendation: <single sentence recommendation>"
    )


def analyze_theme_payloads(llm_client: LLMClient, theme_payloads: List[Dict]) -> List[Dict]:
    theme_results = []
    for payload in theme_payloads:
        prompt_text = build_theme_summary_prompt(payload)
        estimated_tokens = estimate_tokens_for_prompt(prompt_text)
        response_text = llm_client.send_prompt(prompt_text, estimated_tokens=estimated_tokens)
        theme_results.append({
            "theme": payload["theme"],
            "counts": payload["counts"],
            "top_terms": payload["top_terms"],
            "quotes": payload["quotes"],
            "summary": normalize_text(response_text),
        })
    return theme_results


def build_action_prompt(theme_summaries: List[Dict]) -> str:
    template = load_prompt_template("phase2_action_prompt.txt")
    summary_blocks = []
    for theme in theme_summaries:
        summary_blocks.append(
            f"Theme: {theme['theme']}\nSummary: {theme['summary']}\nQuotes:\n" + "\n".join([f"- {q['text']}" for q in theme['quotes']])
        )
    payload = "\n\n".join(summary_blocks)
    if template:
        return template + "\n\n" + payload
    return (
        "Generate 3 highly specific, technical action items for the product and engineering teams, based on the themes, counts, and representative quotes below. "
        "Keep each action short, specific, and measurable.\n\n"
        + payload
        + "\n\nOutput: 1. ... 2. ... 3. ..."
    )


def analyze_actions(llm_client: LLMClient, theme_summaries: List[Dict]) -> List[str]:
    prompt_text = build_action_prompt(theme_summaries)
    estimated_tokens = estimate_tokens_for_prompt(prompt_text)
    response_text = llm_client.send_prompt(prompt_text, estimated_tokens=estimated_tokens)
    lines = [line.strip() for line in response_text.splitlines() if line.strip()]
    actions = []
    for line in lines:
        if line[0].isdigit() and (line[1] == '.' or line[1] == ')'):
            actions.append(line.split('.', 1)[1].strip())
        else:
            actions.append(line)
        if len(actions) >= 3:
            break
    return actions[:3]


def run_phase2(
    input_csv: str = "outputs/02_anonymized_reviews.csv",
    output_dir: str = "outputs",
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    dry_run: bool = True,
    max_batch_tokens: int = BATCH_TOKEN_LIMIT,
) -> Dict:
    df = load_anonymized_reviews(input_csv)
    review_count = len(df)
    if review_count == 0:
        raise ValueError("No reviews available for Phase 2 analysis.")

    df = df.copy()
    df["title"] = df["title"].astype(str).apply(normalize_text)
    df["text"] = df["text"].astype(str).apply(normalize_text)
    df["theme"] = df["text"].apply(assign_theme)
    df["sentiment"] = df["rating"].apply(sentiment_bucket)

    sampled_df = sample_reviews(df, target_size=min(sample_size, review_count))
    sampled_count = len(sampled_df)

    theme_payloads = [build_theme_payload(theme, sampled_df) for theme in sorted(set(sampled_df["theme"]))]
    theme_payloads = [payload for payload in theme_payloads if payload["counts"]["total"] > 0]

    llm_client = LLMClient(dry_run=dry_run)
    theme_results = analyze_theme_payloads(llm_client, theme_payloads)
    actions = analyze_actions(llm_client, theme_results)

    pulse = assemble_final_pulse(theme_results)
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": "llama-3.3-70b-versatile",
        "dry_run": dry_run,
        "actions": actions,
        "pulse_word_count": pulse["word_count"],
    }
    output = build_output_payload(
        phase=2,
        review_count=review_count,
        sampled_count=sampled_count,
        theme_analysis=theme_results,
        summary={**summary, "pulse_text": pulse["pulse_text"]},
    )

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "phase2_summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return output
