"""
Groww Weekly Review AI Agent - Phase 3 Integration Guide

This document provides quick reference for integrating Phase 3 (Google Docs)
into your complete pipeline.
"""

# Phase 1: Data Ingestion & Anonymization
# ==========================================
from agent.ingestion import load_reviews
from agent.anonymizer import anonymize_reviews

reviews = load_reviews('data/play_store_reviews.csv')
anonymized_reviews = anonymize_reviews(reviews)

# Phase 2: Thematic Analysis
# ===========================
from agent.phase2 import analyze_themes_with_llm

theme_analysis = analyze_themes_with_llm(anonymized_reviews)
pulse_summary = theme_analysis['summary']

# Phase 3: Google Docs Integration
# =================================
from agent.gdocs_client import GoogleDocsClient
from datetime import datetime

# Initialize the Google Docs client
docs_client = GoogleDocsClient(
    mcp_server_url="https://mcp-server-production-e580.up.railway.app",
    use_mcp_only=True  # Set to False if you have Google API credentials
)

# Verify MCP server is healthy
if not docs_client.health_check():
    print("Error: MCP server is not accessible")
    exit(1)

# Prepare pulse data for publishing
pulse_data = {
    'title': 'Groww Weekly Pulse Report',
    'timestamp': datetime.now().isoformat(),
    'summary': pulse_summary,
    'themes': theme_analysis.get('themes', []),
    'action_items': theme_analysis.get('action_items', []),
    'notes': 'Auto-generated from Phase 2 analysis'
}

# Generate document title (e.g., "Groww Weekly Pulse - 2026-W23")
timestamp = datetime.now()
week_num = timestamp.isocalendar()[1]
year = timestamp.year
doc_title = f"Groww Weekly Pulse - {year}-W{week_num:02d}"

# Publish to Google Docs
success, doc_id = docs_client.publish_pulse_report(
    pulse_data=pulse_data,
    doc_title=doc_title
)

if success:
    print(f"✅ Published to Google Docs!")
    print(f"Document ID: {doc_id}")
    print(f"View at: https://docs.google.com/document/d/{doc_id}/edit")
else:
    print("❌ Failed to publish to Google Docs")
    exit(1)

# Phase 4: Email Distribution (Next Phase)
# =========================================
# The Gmail integration will use the doc_id returned above
# to create a draft email with a link to the published document

print(f"\nPhase 3 complete! Document published with ID: {doc_id}")
