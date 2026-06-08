"""
Groww Weekly Review AI Agent

Modules:
- ingestion: Data loading and preprocessing
- anonymizer: PII redaction and anonymization
- phase2: LLM-based thematic analysis
- llm_client: Groq API client with rate limiting
- gdocs_client: Google Docs integration via MCP
"""

__version__ = "0.1.0"
__author__ = "Groww AI Team"

from agent.gdocs_client import GoogleDocsClient, create_pulse_document
from agent.gmail_client import GmailClient

__all__ = [
    'GoogleDocsClient',
    'create_pulse_document',
    'GmailClient',
]
