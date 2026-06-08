"""
Phase 3: Google Docs Integration Example

This script demonstrates how to use the Google Docs client to:
1. Create a new Google Document
2. Format and publish a pulse report
3. Organize documents in Google Drive folders

Usage:
    python phase3_example.py --dry-run              # Test without publishing
    python phase3_example.py --doc-id <doc_id>      # Append to existing doc
    python phase3_example.py                        # Create new doc and publish
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from agent.gdocs_client import GoogleDocsClient, create_pulse_document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_pulse_data() -> dict:
    """Create sample pulse data for demonstration"""
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
                'sentiment_breakdown': {
                    'positive': 15,
                    'neutral': 45,
                    'negative': 174
                },
                'key_words': ['signup', 'kyc', 'verification', 'documents', 'rejected', 'confusing'],
                'quotes': [
                    'The KYC process is too complicated and requires too many documents',
                    'Document verification takes forever and keeps getting rejected',
                    'Why do I need so many different proofs for a simple investment app?',
                    'The form validation is unclear - it keeps saying my documents are invalid'
                ]
            },
            {
                'theme': 'Payment & Fund Transfer',
                'count': 198,
                'sentiment_breakdown': {
                    'positive': 42,
                    'neutral': 58,
                    'negative': 98
                },
                'key_words': ['payment failed', 'transaction', 'fund transfer', 'timeout', 'pending'],
                'quotes': [
                    'Payment failed without any error message - money still deducted',
                    'Fund transfer is stuck in pending for 3 days',
                    'Charges are applied but transaction shows failed status',
                    'Why do I get charged multiple times when transaction fails?'
                ]
            },
            {
                'theme': 'Portfolio & Statements',
                'count': 156,
                'sentiment_breakdown': {
                    'positive': 78,
                    'neutral': 52,
                    'negative': 26
                },
                'key_words': ['statement', 'portfolio', 'holdings', 'export', 'pdf', 'detailed'],
                'quotes': [
                    'Would love to download statements as PDF for tax purposes',
                    'Portfolio view is great but need more detailed breakdown',
                    'Can we export transaction history in CSV format?',
                    'Monthly statements should be available for download'
                ]
            },
            {
                'theme': 'Withdrawals & Payouts',
                'count': 142,
                'sentiment_breakdown': {
                    'positive': 35,
                    'neutral': 47,
                    'negative': 60
                },
                'key_words': ['withdrawal', 'payout', 'bank account', 'process', 'delay'],
                'quotes': [
                    'Withdrawal takes too long - sometimes more than 24 hours',
                    'Need to verify bank account every time for withdrawal',
                    'Withdrawal fee is not clearly mentioned upfront',
                    'Can we add multiple payout accounts for flexibility?'
                ]
            },
            {
                'theme': 'App Performance & UI/UX',
                'count': 127,
                'sentiment_breakdown': {
                    'positive': 45,
                    'neutral': 42,
                    'negative': 40
                },
                'key_words': ['app crashes', 'slow', 'ui', 'confusing', 'battery'],
                'quotes': [
                    'App crashes when checking portfolio during market hours',
                    'Navigation is confusing - takes too many taps to reach features',
                    'App is too heavy and drains battery quickly',
                    'Charts and real-time data loading is very slow'
                ]
            }
        ],
        'action_items': [
            {
                'title': 'Streamline KYC Process',
                'description': 'Reduce required documents from 5 to 3, add document pre-validation, and implement progressive KYC for faster onboarding',
                'priority': 'Critical',
                'owner': 'Product',
                'estimated_effort': '3 weeks'
            },
            {
                'title': 'Improve Payment Error Handling',
                'description': 'Implement detailed error messages, automatic retry logic, and transaction monitoring to prevent duplicate charges',
                'priority': 'Critical',
                'owner': 'Engineering',
                'estimated_effort': '2 weeks'
            },
            {
                'title': 'Add Statement Export Feature',
                'description': 'Enable PDF/CSV export of statements and transactions with configurable date ranges for tax compliance',
                'priority': 'High',
                'owner': 'Product',
                'estimated_effort': '2 weeks'
            },
            {
                'title': 'Optimize Fund Transfer Flow',
                'description': 'Add real-time status tracking, reduce processing time from 24h to <1h, and implement transparent fee display',
                'priority': 'High',
                'owner': 'Engineering',
                'estimated_effort': '4 weeks'
            },
            {
                'title': 'Fix App Performance Issues',
                'description': 'Profile memory usage, optimize chart rendering, and implement code splitting to reduce app size and crashes',
                'priority': 'Medium',
                'owner': 'Engineering',
                'estimated_effort': '3 weeks'
            }
        ],
        'insights': [
            'Negative sentiment concentrates in onboarding and payments - these are critical user friction points',
            'KYC rejection rate is affecting user retention - consider UX improvements and clearer validation rules',
            'Users value transparency in fees and processing times - add this information prominently in UI',
            'Performance issues indicate app size and optimization problems - prioritize technical debt'
        ],
        'notes': 'Report generated from 500 randomly sampled reviews from Groww user base for the week of June 1-8, 2026. Focus on addressing critical paths that impact user experience and retention.'
    }


def dry_run(pulse_data: dict) -> None:
    """Run in dry-run mode: format data without publishing"""
    logger.info("=== DRY RUN MODE ===")
    logger.info("Formatting pulse data without publishing to Google Docs...")
    
    client = GoogleDocsClient(use_mcp_only=True)
    formatted = client.format_pulse_for_docs(pulse_data)
    
    logger.info("\n=== FORMATTED OUTPUT ===")
    print(formatted)
    
    logger.info("\n=== DRY RUN COMPLETE ===")
    logger.info("To publish, run without --dry-run flag")


def publish_to_doc(pulse_data: dict, 
                  doc_id: str = None,
                  doc_title: str = None,
                  mcp_server_url: str = None) -> None:
    """Publish pulse data to Google Doc"""
    logger.info("=== GOOGLE DOCS PUBLISHING ===")
    
    # Generate title if not provided
    if not doc_title:
        timestamp = datetime.now()
        week_num = timestamp.isocalendar()[1]
        year = timestamp.year
        doc_title = f"Groww Weekly Pulse - {year}-W{week_num:02d}"
    
    # If doc_id is not provided explicitly, try environment variable fallback
    if not doc_id:
        doc_id = os.getenv('GOOGLE_DOC_ID')

    if doc_id:
        logger.info(f"Using doc_id: {doc_id}")
        pulse_data['doc_id'] = doc_id
    
    logger.info(f"Document title: {doc_title}")
    logger.info(f"Timestamp: {pulse_data.get('timestamp')}")
    logger.info(f"Themes to publish: {len(pulse_data.get('themes', []))}")
    logger.info(f"Action items: {len(pulse_data.get('action_items', []))}")
    
    # Publish
    success, returned_doc_id = create_pulse_document(
        pulse_data=pulse_data,
        doc_title=doc_title,
        mcp_server_url=mcp_server_url,
        use_mcp_only=False
    )
    
    if success:
        logger.info("✅ Successfully published pulse report!")
        logger.info(f"Document ID: {returned_doc_id}")
        logger.info(f"View in Google Docs: https://docs.google.com/document/d/{returned_doc_id}/edit")
    else:
        logger.error("❌ Failed to publish pulse report")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Phase 3: Google Docs Integration for Groww Weekly Review Agent'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Format data without publishing to Google Docs'
    )
    parser.add_argument(
        '--doc-id',
        type=str,
        help='Existing Google Doc ID to append content to'
    )
    parser.add_argument(
        '--doc-title',
        type=str,
        help='Title for the new document (auto-generated if not provided)'
    )
    parser.add_argument(
        '--mcp-server-url',
        type=str,
        help='MCP server URL (defaults to DOCS_MCP_SERVER_URL env var)'
    )
    parser.add_argument(
        '--sample-data',
        type=str,
        choices=['minimal', 'full'],
        default='full',
        help='Use minimal or full sample data'
    )
    
    args = parser.parse_args()
    
    # Create sample pulse data
    logger.info("Creating sample pulse data...")
    pulse_data = create_sample_pulse_data()
    
    if args.sample_data == 'minimal':
        pulse_data = {
            'title': 'Groww Weekly Pulse - Minimal Test',
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_reviews': 100,
                'sampled_reviews': 50,
                'date_range': '2026-06-01 to 2026-06-08'
            },
            'themes': [
                {
                    'theme': 'User Experience',
                    'count': 50,
                    'quotes': ['App is slow', 'Interface is confusing']
                }
            ]
        }
    
    logger.info(f"Pulse data created with {len(pulse_data.get('themes', []))} themes")
    
    # Execute based on mode
    if args.dry_run:
        dry_run(pulse_data)
    else:
        publish_to_doc(
            pulse_data=pulse_data,
            doc_id=args.doc_id,
            doc_title=args.doc_title,
            mcp_server_url=args.mcp_server_url
        )


if __name__ == '__main__':
    main()
