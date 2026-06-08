import os
import sys
import pandas as pd
from datetime import datetime, timezone, timedelta
from google_play_scraper import reviews, Sort

def pull_recent_reviews(app_id: str = "com.nextbillion.groww", max_weeks: int = 12) -> pd.DataFrame:
    """
    Pulls user reviews for the given app ID from the Google Play Store
    spanning back to max_weeks ago (default 12 weeks).
    """
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(weeks=max_weeks)
    print(f"Fetching reviews for app: {app_id}...")
    print(f"Cutoff date (12 weeks ago): {cutoff_date.isoformat()}")

    all_reviews = []
    continuation_token = None
    page = 1
    reached_cutoff = False

    # Fetch in pages of 200 reviews
    batch_size = 200

    while not reached_cutoff:
        print(f"Fetching page {page}...")
        if continuation_token:
            result, continuation_token = reviews(
                app_id,
                continuation_token=continuation_token
            )
        else:
            result, continuation_token = reviews(
                app_id,
                lang='en',
                country='in',
                sort=Sort.NEWEST,
                count=batch_size
            )

        if not result:
            print("No more reviews returned.")
            break

        print(f"Fetched {len(result)} reviews in page {page}.")
        
        page_reviews = []
        for r in result:
            review_date = r.get("at")
            if isinstance(review_date, datetime):
                if review_date.tzinfo is None:
                    review_date = review_date.replace(tzinfo=timezone.utc)
            else:
                # Fallback parse
                try:
                    review_date = pd.to_datetime(review_date).to_pydatetime()
                    if review_date.tzinfo is None:
                        review_date = review_date.replace(tzinfo=timezone.utc)
                except Exception:
                    review_date = now # Default to now if unparseable

            # Check if this review is older than the cutoff
            if review_date < cutoff_date:
                reached_cutoff = True
                # We can still add this if we want, but we should stop fetching next pages
                continue

            # Play Store reviews do not have separate titles, we use the first few words of the content
            content = r.get("content", "")
            words = content.split()
            title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")

            page_reviews.append({
                "id": r.get("reviewId"),
                "rating": r.get("score"),
                "title": title,
                "text": content,
                "date": review_date.isoformat(),
                "source": "google_play"
            })

        all_reviews.extend(page_reviews)
        print(f"Total reviews matching criteria so far: {len(all_reviews)}")

        if not continuation_token:
            print("No continuation token. End of reviews.")
            break

        page += 1

    return pd.DataFrame(all_reviews)

if __name__ == "__main__":
    max_weeks = 12
    if len(sys.argv) > 1:
        try:
            max_weeks = int(sys.argv[1])
        except ValueError:
            pass
            
    df = pull_recent_reviews("com.nextbillion.groww", max_weeks=max_weeks)
    if not df.empty:
        output_dir = "data"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "play_store_reviews.csv")
        df.to_csv(output_path, index=False)
        print(f"Saved {len(df)} reviews to: {output_path}")
