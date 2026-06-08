#!/usr/bin/env python3
"""
Phase 1: Ingestion, Filtering, and Anonymization
Processes raw reviews through the ingestion pipeline.
"""

import sys
import json
from datetime import datetime, timezone
from agent.ingestion import (
    load_reviews, 
    filter_reviews_by_date, 
    process_and_anonymize_reviews,
    clean_and_filter_reviews
)

def run_phase1(input_csv: str = "data/play_store_reviews.csv", 
               weeks_ago_start: int = 12,
               weeks_ago_end: int = 0,
               min_words: int = 6,
               remove_emoji: bool = True,
               english_only: bool = True):
    """
    Executes Phase 1: Load → Filter → Anonymize → Clean
    """
    print(f"[PHASE 1] Starting ingestion pipeline...")
    print(f"  Input: {input_csv}")
    print(f"  Date window: {weeks_ago_start} - {weeks_ago_end} weeks ago")
    print(f"  Filters: min_words={min_words}, remove_emoji={remove_emoji}, english_only={english_only}")
    print()
    
    # Step 1: Load reviews
    print("[Step 1] Loading reviews from CSV...")
    df = load_reviews(input_csv)
    print(f"  ✓ Loaded {len(df)} total reviews")
    print(f"  Columns: {list(df.columns)}")
    print()
    
    # Step 2: Filter by date window
    print(f"[Step 2] Filtering by date window ({weeks_ago_start}-{weeks_ago_end} weeks)...")
    current_date = datetime.now(timezone.utc)
    df_filtered = filter_reviews_by_date(df, weeks_ago_start=weeks_ago_start, 
                                         weeks_ago_end=weeks_ago_end, 
                                         current_date=current_date)
    print(f"  ✓ Filtered to {len(df_filtered)} reviews in date window")
    if len(df_filtered) > 0:
        print(f"    Date range: {df_filtered['date'].min()} to {df_filtered['date'].max()}")
    print()
    
    # Step 3: Clean and filter (emoji, word count, language)
    print("[Step 3] Cleaning and filtering reviews...")
    print(f"  (emoji removal, minimum word count, language detection)")
    df_cleaned = clean_and_filter_reviews(
        df_filtered,
        min_words=min_words,
        remove_emoji=remove_emoji,
        english_only=english_only
    )
    print()
    
    # Step 4: Anonymize PII
    print("[Step 4] Anonymizing PII (emails, phones, handles, IDs)...")
    df_anonymized = process_and_anonymize_reviews(df_cleaned)
    print(f"  ✓ PII anonymization complete")
    print()
    
    # Save outputs
    print("[Step 5] Saving outputs...")
    output_dir = "outputs"
    
    # Raw filtered data
    filtered_path = f"{output_dir}/01_filtered_reviews.csv"
    df_filtered.to_csv(filtered_path, index=False)
    print(f"  ✓ Saved filtered reviews to: {filtered_path}")
    
    # Cleaned & anonymized data
    anonymized_path = f"{output_dir}/02_anonymized_reviews.csv"
    df_anonymized.to_csv(anonymized_path, index=False)
    print(f"  ✓ Saved anonymized & cleaned reviews to: {anonymized_path}")
    
    # Summary stats
    summary = {
        "phase": 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_reviews_loaded": len(df),
        "reviews_after_date_filter": len(df_filtered),
        "reviews_after_cleaning": len(df_cleaned),
        "reviews_after_anonymization": len(df_anonymized),
        "filtering_stats": {
            "emoji_removed": remove_emoji,
            "min_words": min_words,
            "english_only": english_only,
            "retention_rate": f"{100 * len(df_anonymized) / len(df):.1f}%"
        },
        "date_range": {
            "start": df_filtered['date'].min().isoformat() if len(df_filtered) > 0 else None,
            "end": df_filtered['date'].max().isoformat() if len(df_filtered) > 0 else None
        },
        "rating_distribution": df_anonymized['rating'].value_counts().to_dict() if len(df_anonymized) > 0 else {},
        "sources": df_anonymized['source'].unique().tolist() if len(df_anonymized) > 0 else []
    }
    
    stats_path = f"{output_dir}/phase1_summary.json"
    with open(stats_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  ✓ Saved phase 1 summary to: {stats_path}")
    print()
    
    print("[PHASE 1] Complete!")
    print(f"Ready for Phase 2 analysis with {len(df_anonymized)} anonymized reviews")
    
    return df_filtered, df_anonymized

if __name__ == "__main__":
    run_phase1()
