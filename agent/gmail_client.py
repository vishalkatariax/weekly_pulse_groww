"""
Gmail MCP Integration Client for Groww Weekly Review AI Agent.

This module handles:
- formatting email subject, HTML body, and text body for pulse reports
- creating a draft via the Gmail MCP server
- parsing recipient and CC configuration from environment variables
"""

import os
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _parse_recipient_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [email.strip() for email in value.replace(';', ',').split(',') if email.strip()]


class GmailClient:
    """Client for creating email drafts through the Gmail MCP server."""

    def __init__(self,
                 mcp_server_url: str = None,
                 recipients: Optional[List[str]] = None,
                 cc: Optional[List[str]] = None,
                 sender: Optional[str] = None,
                 subject_prefix: Optional[str] = None,
                 draft_endpoint: str = None):
        self.mcp_server_url = mcp_server_url or os.getenv(
            'GMAIL_MCP_SERVER_URL',
            'https://mcp-server-production-e580.up.railway.app'
        )
        self.recipients = recipients or _parse_recipient_list(os.getenv('EMAIL_RECIPIENTS'))
        self.cc = cc or _parse_recipient_list(os.getenv('EMAIL_CC'))
        self.sender = sender or os.getenv('EMAIL_FROM')
        self.subject_prefix = subject_prefix or os.getenv('EMAIL_SUBJECT_PREFIX', 'Groww Weekly Pulse Report')
        self.draft_endpoint = draft_endpoint or os.getenv('GMAIL_MCP_DRAFT_ENDPOINT', '/create_email_draft')

    def format_email_subject(self, pulse_data: Dict) -> str:
        title = pulse_data.get('title', 'Groww Weekly Pulse Report')
        timestamp = pulse_data.get('timestamp')
        if timestamp:
            try:
                week_num = datetime.fromisoformat(timestamp).isocalendar()[1]
                year = datetime.fromisoformat(timestamp).year
                return f"{self.subject_prefix} - {year}-W{week_num:02d}"
            except Exception:
                pass
        return self.subject_prefix if self.subject_prefix else title

    def format_email_body(self, pulse_data: Dict, doc_url: Optional[str] = None) -> Dict[str, str]:
        title = pulse_data.get('title', 'Groww Weekly Pulse Report')
        timestamp = pulse_data.get('timestamp', datetime.now().isoformat())
        summary = pulse_data.get('summary', {})
        themes = pulse_data.get('themes', [])
        action_items = pulse_data.get('action_items', [])
        notes = pulse_data.get('notes', '')

        doc_line = f"Report link: {doc_url}" if doc_url else "Report link not available"

        html_lines = [f"<h1>{title}</h1>", f"<p><strong>Generated:</strong> {timestamp}</p>"]
        text_lines = [title, f"Generated: {timestamp}", ""]

        if summary:
            html_lines.append("<h2>Summary</h2>")
            text_lines.append("SUMMARY")
            if summary.get('total_reviews') is not None:
                html_lines.append(f"<p><strong>Total Reviews Analyzed:</strong> {summary['total_reviews']}</p>")
                text_lines.append(f"Total Reviews Analyzed: {summary['total_reviews']}")
            if summary.get('sampled_reviews') is not None:
                html_lines.append(f"<p><strong>Reviews Sampled:</strong> {summary['sampled_reviews']}</p>")
                text_lines.append(f"Reviews Sampled: {summary['sampled_reviews']}")
            if summary.get('date_range'):
                html_lines.append(f"<p><strong>Date Range:</strong> {summary['date_range']}</p>")
                text_lines.append(f"Date Range: {summary['date_range']}")
            html_lines.append("<br />")
            text_lines.append("")

        if themes:
            html_lines.append("<h2>Top Themes</h2>")
            text_lines.append("TOP THEMES")
            for theme in themes[:3]:
                name = theme.get('theme', 'Untitled Theme')
                count = theme.get('count', 'N/A')
                top_quote = None
                if theme.get('quotes'):
                    top_quote = theme['quotes'][0]
                html_lines.append(f"<h3>{name}</h3>")
                html_lines.append(f"<p><strong>Count:</strong> {count}</p>")
                text_lines.append(f"- {name} ({count})")
                if top_quote:
                    html_lines.append(f"<p><em>Representative quote:</em> {top_quote}</p>")
                    text_lines.append(f"  Quote: {top_quote}")
            html_lines.append("<br />")
            text_lines.append("")

        if action_items:
            html_lines.append("<h2>Recommended Actions</h2>")
            text_lines.append("RECOMMENDED ACTIONS")
            for item in action_items[:5]:
                action_title = item.get('title', 'Action Item')
                description = item.get('description', '')
                priority = item.get('priority', '')
                html_lines.append(f"<p><strong>{action_title}</strong><br />{description}")
                if priority:
                    html_lines.append(f"<br /><em>Priority:</em> {priority}")
                html_lines.append("</p>")
                text_lines.append(f"- {action_title}")
                if description:
                    text_lines.append(f"  {description}")
                if priority:
                    text_lines.append(f"  Priority: {priority}")
            html_lines.append("<br />")
            text_lines.append("")

        if notes:
            html_lines.append("<h2>Notes</h2>")
            html_lines.append(f"<p>{notes}</p>")
            text_lines.append("NOTES")
            text_lines.append(notes)
            text_lines.append("")

        if doc_url:
            html_lines.append(f"<p><a href=\"{doc_url}\">View the full report in Google Docs</a></p>")
            text_lines.append(doc_line)
        else:
            text_lines.append(doc_line)

        html_body = "\n".join(html_lines)
        text_body = "\n".join(text_lines)

        return {
            'html_body': html_body,
            'text_body': text_body
        }

    def create_draft_via_mcp(self,
                             subject: str,
                             to_addresses: Optional[List[str]] = None,
                             cc_addresses: Optional[List[str]] = None,
                             html_body: str = None,
                             text_body: str = None) -> bool:
        to_addresses = to_addresses or self.recipients
        cc_addresses = cc_addresses or self.cc

        if not to_addresses:
            logger.error("No email recipients provided. Set EMAIL_RECIPIENTS in .env or pass recipients explicitly.")
            return False

        url = f"{self.mcp_server_url.rstrip('/')}/{self.draft_endpoint.lstrip('/')}"
        payload = {
            'to': to_addresses,
            'cc': cc_addresses,
            'subject': subject,
            'html': html_body,
            'body': text_body,
        }
        if self.sender:
            payload['from'] = self.sender

        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info('Successfully created email draft via Gmail MCP')
                    return True
                logger.error(f"Gmail MCP draft failed: {result.get('message', 'Unknown error')}")
                return False
            logger.error(f"Gmail MCP server error: {response.status_code} - {response.text}")
            return False
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to Gmail MCP server at {self.mcp_server_url}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to Gmail MCP server at {self.mcp_server_url}")
            return False
        except Exception as e:
            logger.error(f"Error creating Gmail draft: {e}")
            return False

    def draft_pulse_report_email(self,
                                 pulse_data: Dict,
                                 doc_id: str,
                                 recipients: Optional[List[str]] = None,
                                 cc: Optional[List[str]] = None,
                                 subject: Optional[str] = None) -> bool:
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        subject = subject or self.format_email_subject(pulse_data)
        email_contents = self.format_email_body(pulse_data, doc_url=doc_url)

        return self.create_draft_via_mcp(
            subject=subject,
            to_addresses=recipients,
            cc_addresses=cc,
            html_body=email_contents['html_body'],
            text_body=email_contents['text_body']
        )
