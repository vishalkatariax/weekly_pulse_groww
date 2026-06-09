"""
Phase 4: Gmail MCP Integration Example (Updated)

This script demonstrates how to:
1. Publish the pulse report to Google Docs via the Docs MCP server.
2. Draft an email summary via the Gmail MCP server.

Configuration is driven by environment variables in `.env`:
- `DOCS_MCP_SERVER_URL` – Docs MCP endpoint (defaults to the production server).
- `GMAIL_MCP_SERVER_URL` – Gmail MCP endpoint (defaults to the same production server).
- `EMAIL_RECIPIENTS` – Comma‑separated list of recipients for the email draft.
- `EMAIL_CC` – Optional CC list.
- `EMAIL_SUBJECT_PREFIX` – Prefix for the email subject line.

The script can be run in dry‑run mode to simply print the formatted email without calling any MCP services.
"""

import argparse
import logging
import os
import sys
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Ensure project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from agent.gdocs_client import create_pulse_document
from agent.gmail_client import GmailClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _parse_list(value: Optional[str]) -> Optional[List[str]]:
    """Parse a semicolon or comma separated list into a Python list."""
    if not value:
        return None
    return [item.strip() for item in value.replace(';', ',').split(',') if item.strip()]


def create_sample_pulse_data() -> dict:
    """Generate a synthetic pulse report used for demo purposes."""
    return {
        'title': 'Groww Weekly Pulse Report',
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_reviews': 1247,
            'sampled_reviews': 500,
            'date_range': '2026-06-01 to 2026-06-08',
            'top_rating': '1-2 stars (negative sentiment)'
        },
        'themes': [
            {
                'theme': 'Onboarding & KYC',
                'count': 234,
                'sentiment_breakdown': {'positive': 15, 'neutral': 45, 'negative': 174},
                'quotes': [
                    'The KYC process is too complicated and requires too many documents',
                    'Document verification takes forever and keeps getting rejected',
                    'The form validation is unclear - it keeps saying my documents are invalid'
                ]
            },
            {
                'theme': 'Payment & Fund Transfer',
                'count': 198,
                'sentiment_breakdown': {'positive': 42, 'neutral': 58, 'negative': 98},
                'quotes': [
                    'Payment failed without any error message - money still deducted',
                    'Fund transfer is stuck in pending for 3 days',
                    'Charges are applied but transaction shows failed status'
                ]
            },
            {
                'theme': 'Portfolio & Statements',
                'count': 156,
                'sentiment_breakdown': {'positive': 78, 'neutral': 52, 'negative': 26},
                'quotes': [
                    'Would love to download statements as PDF for tax purposes',
                    'Portfolio view is great but need more detailed breakdown',
                    'Monthly statements should be available for download'
                ]
            }
        ],
        'action_items': [
            {
                'title': 'Streamline KYC Process',
                'description': 'Reduce required documents from 5 to 3, add document pre‑validation, and implement progressive KYC for faster onboarding',
                'priority': 'Critical'
            },
            {
                'title': 'Improve Payment Error Handling',
                'description': 'Implement detailed error messages, automatic retry logic, and transaction monitoring to prevent duplicate charges',
                'priority': 'Critical'
            },
            {
                'title': 'Add Statement Export Feature',
                'description': 'Enable PDF/CSV export of statements and transactions with configurable date ranges for tax compliance',
                'priority': 'High'
            }
        ],
        'notes': 'Report generated from 500 randomly sampled reviews from Groww user base for the week of June 1‑8, 2026.'
    }


def create_real_pulse_data() -> dict:
    """Fetch raw Play Store reviews using the same pipeline as Phase 1.

    The function loads the raw CSV (or the path specified by PLAYSTORE_REVIEWS_CSV),
    applies the same date filtering, cleaning, and anonymization steps as
    `run_phase1` did, and then constructs a minimal pulse structure.
    If any step fails, it falls back to the synthetic sample data.
    """
    import os
    from pathlib import Path
    # Load raw reviews (mirrors Phase 1)
    try:
        from agent.ingestion import (
            load_reviews,
            filter_reviews_by_date,
            clean_and_filter_reviews,
            process_and_anonymize_reviews,
        )
        csv_path = os.getenv(
            "PLAYSTORE_REVIEWS_CSV",
            Path(__file__).parent.parent / "data" / "play_store_reviews.csv",
        )
        df_raw = load_reviews(str(csv_path))
    except Exception as e:
        logger.error(f"Failed to load raw reviews: {e}")
        return create_sample_pulse_data()

    # Apply the same filtering as Phase 1 (default 12‑0 weeks window)
    try:
        df_filtered = filter_reviews_by_date(df_raw, weeks_ago_start=12, weeks_ago_end=0)
        df_cleaned = clean_and_filter_reviews(df_filtered)
        df_anonymized = process_and_anonymize_reviews(df_cleaned)
    except Exception as e:
        logger.error(f"Error during Phase 1 processing steps: {e}")
        return create_sample_pulse_data()

    total_reviews = len(df_raw)
    sampled_reviews = len(df_anonymized)
    # Construct a simple pulse payload – detailed theme analysis is omitted for brevity
    pulse = {
        "title": "Groww Weekly Pulse Report",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_reviews": total_reviews,
            "sampled_reviews": sampled_reviews,
            "date_range": "2026-06-01 to 2026-06-08",
            "top_rating": "N/A",
        },
        "themes": [],
        "action_items": [],
        "notes": "Report generated from real Play Store reviews using Phase 1 pipeline.",
    }
    return pulse


def publish_and_draft_email(
        pulse_data: dict,
        doc_id: Optional[str] = None,
        doc_title: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        subject: Optional[str] = None,
        mcp_server_url: Optional[str] = None,
        gmail_mcp_server_url: Optional[str] = None,
        dry_run: bool = False) -> None:
    """Publish the pulse to Google Docs and optionally draft a Gmail message.

    Parameters are taken from CLI args or fall back to environment configuration.
    """
    # Resolve defaults from environment when not explicitly provided
    mcp_server_url = mcp_server_url or os.getenv('DOCS_MCP_SERVER_URL')
    gmail_mcp_server_url = gmail_mcp_server_url or os.getenv('GMAIL_MCP_SERVER_URL')
    if not recipients:
        recipients = _parse_list(os.getenv('EMAIL_RECIPIENTS'))
    if not cc:
        cc = _parse_list(os.getenv('EMAIL_CC'))

    # Build a sensible document title if none supplied
    if not doc_title:
        now = datetime.now()
        week_num = now.isocalendar()[1]
        doc_title = f"Groww Weekly Pulse - {now.year}-W{week_num:02d}"

    gmail_client = GmailClient(
        mcp_server_url=gmail_mcp_server_url,
        recipients=recipients,
        cc=cc
    )

    email_subject = subject or gmail_client.format_email_subject(pulse_data)

    if dry_run:
        logger.info("--- DRY RUN MODE ---")
        doc_url = "https://docs.google.com/document/d/MOCK_DOC_ID/edit"
        email_body = gmail_client.format_email_body(pulse_data, doc_url=doc_url)
        logger.info(f"Subject: {email_subject}")
        logger.info("--- TEXT BODY ---")
        print(email_body['text_body'])
        logger.info("--- HTML BODY ---")
        print(email_body['html_body'])
        logger.info("Dry‑run complete. No draft was created.")
        return

    # Publish to Google Docs via the MCP client
    # Use existing Google Doc ID from CLI argument, DOC_ID env var, or GOOGLE_DOC_ID env var
    doc_id_target = (doc_id or os.getenv('DOC_ID') or os.getenv('GOOGLE_DOC_ID') or '').strip()
    if doc_id_target:
        logger.info(f"Using Google Doc ID: {doc_id_target}")
        # Ensure pulse_data contains the doc_id for the convenience function
        pulse_data['doc_id'] = doc_id_target
        # Publish via MCP-only mode (will append to existing doc)
        success, returned_doc_id = create_pulse_document(
            pulse_data=pulse_data,
            doc_title=doc_title,
            mcp_server_url=mcp_server_url,
            use_mcp_only=True
        )
    else:
        logger.error("DOC_ID environment variable or --doc-id argument is required in MCP-only mode.")
        sys.exit(1)

    
    if not success or not returned_doc_id:
        logger.error("Failed to publish the pulse report to Google Docs.")
        sys.exit(1)
    logger.info(f"Published report to Google Docs ID: {returned_doc_id}")
    doc_url = f"https://docs.google.com/document/d/{returned_doc_id}/edit"

    if not recipients:
        logger.error("No email recipients configured. Set EMAIL_RECIPIENTS in .env or provide via --to.")
        sys.exit(1)

    draft_success = gmail_client.draft_pulse_report_email(
        pulse_data=pulse_data,
        doc_id=returned_doc_id,
        recipients=recipients,
        cc=cc,
        subject=email_subject
    )
    if draft_success:
        logger.info("✅ Gmail draft created successfully via MCP")
    else:
        logger.error("❌ Failed to create Gmail draft via MCP")
        sys.exit(1)


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Phase 4: Gmail MCP Integration for Groww Weekly Review Agent'
    )
    parser.add_argument('--dry-run', action='store_true', help='Render and print email content only')
    parser.add_argument('--subject', type=str, help='Email subject line')
    parser.add_argument('--use-real', action='store_true', help='Fetch real review data from Play Store (pre‑cleaned)')
    parser.add_argument('--mcp-server-url', type=str, help='Docs MCP server URL (overrides .env)')
    parser.add_argument('--gmail-mcp-server-url', type=str, help='Gmail MCP server URL (overrides .env)')
    parser.add_argument('--doc-id', type=str, help='Existing Google Doc ID to append content to')
    parser.add_argument('--to', type=str, help='Comma‑separated recipients for the email (overrides .env)')
    parser.add_argument('--cc', type=str, help='Comma‑separated CC recipients (overrides .env)')
    return parser.parse_args()


def main():
    args = parse_cli_args()
    # Choose data source based on flag
    if args.use_real:
        pulse_data = create_real_pulse_data()
    else:
        pulse_data = create_sample_pulse_data()
    publish_and_draft_email(
        pulse_data=pulse_data,
        doc_id=args.doc_id,
        recipients=_parse_list(args.to),
        cc=_parse_list(args.cc),
        subject=args.subject,
        mcp_server_url=args.mcp_server_url,
        gmail_mcp_server_url=args.gmail_mcp_server_url,
        dry_run=args.dry_run
    )

if __name__ == '__main__':
    main()
