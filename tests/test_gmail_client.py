"""
Tests for Gmail MCP integration client.
"""

import json
import os
from agent.gmail_client import GmailClient


def test_parse_recipients_from_env(monkeypatch):
    monkeypatch.setenv('EMAIL_RECIPIENTS', 'alice@example.com, bob@example.com')
    client = GmailClient()

    assert client.recipients == ['alice@example.com', 'bob@example.com']


def test_format_email_body_includes_doc_link():
    client = GmailClient(recipients=['alice@example.com'])
    pulse_data = {
        'title': 'Groww Weekly Pulse Report',
        'timestamp': '2026-06-08T12:00:00',
        'summary': {'total_reviews': 10, 'sampled_reviews': 5, 'date_range': '2026-06-01 to 2026-06-08'},
        'themes': [{'theme': 'Onboarding', 'count': 3, 'quotes': ['Great experience']}],
        'action_items': [{'title': 'Fix onboarding', 'description': 'Simplify flow', 'priority': 'High'}],
    }
    contents = client.format_email_body(pulse_data, doc_url='https://docs.google.com/document/d/123/edit')

    assert 'https://docs.google.com/document/d/123/edit' in contents['text_body']
    assert '<a href="https://docs.google.com/document/d/123/edit">' in contents['html_body']
    assert 'Groww Weekly Pulse Report' in contents['html_body']


def test_create_draft_via_mcp_posts_payload(monkeypatch):
    sent = {}

    class DummyResponse:
        status_code = 200
        def json(self):
            return {'status': 'success'}

    def fake_post(url, json=None, timeout=None):
        sent['url'] = url
        sent['json'] = json
        sent['timeout'] = timeout
        return DummyResponse()

    monkeypatch.setenv('GMAIL_MCP_SERVER_URL', 'https://mcp-server-production-e580.up.railway.app')
    monkeypatch.setattr('agent.gmail_client.requests.post', fake_post)

    client = GmailClient(recipients=['alice@example.com'], cc=['bob@example.com'])
    success = client.create_draft_via_mcp(
        subject='Test Subject',
        html_body='<p>Hello</p>',
        text_body='Hello',
    )

    assert success is True
    assert sent['url'] == 'https://mcp-server-production-e580.up.railway.app/create_draft'
    assert sent['json']['to'] == ['alice@example.com']
    assert sent['json']['cc'] == ['bob@example.com']
    assert sent['json']['subject'] == 'Test Subject'
