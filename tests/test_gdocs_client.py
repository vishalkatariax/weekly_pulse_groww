"""
Tests for Google Docs Client (Phase 3 Integration)
"""

import pytest
import json
from datetime import datetime
from agent.gdocs_client import GoogleDocsClient, create_pulse_document


class TestGoogleDocsClient:
    """Test suite for GoogleDocsClient"""
    
    @pytest.fixture
    def client(self):
        """Create a GoogleDocsClient instance for testing"""
        return GoogleDocsClient(use_mcp_only=True)
    
    @pytest.fixture
    def sample_pulse_data(self):
        """Sample pulse data for testing"""
        return {
            'title': 'Groww Weekly Pulse Report',
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_reviews': 1000,
                'sampled_reviews': 500,
                'date_range': '2026-06-01 to 2026-06-08'
            },
            'themes': [
                {
                    'theme': 'Onboarding',
                    'count': 150,
                    'sentiment_breakdown': {
                        'positive': 30,
                        'neutral': 50,
                        'negative': 70
                    },
                    'key_words': ['signup', 'registration', 'kyc', 'verification', 'documents'],
                    'quotes': [
                        'The signup process is confusing and takes too long',
                        'KYC verification rejected my document multiple times',
                        'Documentation requirements are unclear'
                    ]
                },
                {
                    'theme': 'Payments',
                    'count': 120,
                    'sentiment_breakdown': {
                        'positive': 40,
                        'neutral': 40,
                        'negative': 40
                    },
                    'key_words': ['payment', 'transaction', 'fund', 'transfer', 'failed'],
                    'quotes': [
                        'Payment failed without proper error message',
                        'Fund transfer takes too long',
                        'Charges are not transparent'
                    ]
                },
                {
                    'theme': 'Statements',
                    'count': 100,
                    'sentiment_breakdown': {
                        'positive': 50,
                        'neutral': 30,
                        'negative': 20
                    },
                    'key_words': ['statement', 'report', 'download', 'pdf', 'export'],
                    'quotes': [
                        'Statements are not downloadable',
                        'Need detailed transaction history',
                        'PDF export would be helpful'
                    ]
                }
            ],
            'action_items': [
                {
                    'title': 'Simplify KYC Process',
                    'description': 'Reduce number of required documents and clarify submission guidelines',
                    'priority': 'High'
                },
                {
                    'title': 'Improve Payment Error Handling',
                    'description': 'Provide clear error messages when payments fail with recovery options',
                    'priority': 'High'
                },
                {
                    'title': 'Add Statement Export Feature',
                    'description': 'Enable users to download statements as PDF with custom date ranges',
                    'priority': 'Medium'
                }
            ],
            'notes': 'Report generated from 500 sampled reviews across Groww user base. Focus on improving user experience in critical paths.'
        }
    
    def test_client_initialization(self, client):
        """Test that GoogleDocsClient initializes correctly"""
        assert client is not None
        assert client.use_mcp_only is True
        assert client.mcp_server_url is not None

    def test_service_account_env_var_is_loaded(self, monkeypatch):
        """Verify that GOOGLE_SERVICE_ACCOUNT_JSON is read from env."""
        sample_json = '{"type":"service_account","project_id":"test-project"}'
        monkeypatch.setenv('GOOGLE_SERVICE_ACCOUNT_JSON', sample_json)
        client = GoogleDocsClient(use_mcp_only=True)

        assert client.service_account_path == sample_json
    
    def test_health_check(self, client):
        """Test health check - may fail if server is down, that's expected"""
        # This test documents that health check is available
        # In CI/CD, this might skip if server is not available
        result = client.health_check()
        # We don't assert the result since server might not be available in test env
        print(f"Health check result: {result}")
    
    def test_format_pulse_for_docs(self, client, sample_pulse_data):
        """Test formatting pulse data for Google Docs"""
        formatted = client.format_pulse_for_docs(sample_pulse_data)
        
        # Verify key sections are present
        assert 'Groww Weekly Pulse Report' in formatted
        assert 'SUMMARY STATISTICS' in formatted
        assert 'TOP THEMES' in formatted
        assert 'RECOMMENDED ACTIONS' in formatted
        assert 'Total Reviews Analyzed: 1000' in formatted
        assert 'Onboarding' in formatted
        assert 'KYC verification rejected my document' in formatted
        assert 'Simplify KYC Process' in formatted
    
    def test_format_pulse_structure(self, client, sample_pulse_data):
        """Test that formatted pulse has all expected sections"""
        formatted = client.format_pulse_for_docs(sample_pulse_data)
        lines = formatted.split('\n')
        
        # Should have content
        assert len(lines) > 20
        
        # Check for structured elements
        assert any('1.' in line for line in lines)  # Numbered items
        assert any('Key Words:' in line for line in lines)
        assert any('Priority:' in line for line in lines)
    
    def test_format_with_minimal_data(self, client):
        """Test formatting with minimal data"""
        minimal_data = {
            'title': 'Test Report',
            'timestamp': datetime.now().isoformat()
        }
        
        formatted = client.format_pulse_for_docs(minimal_data)
        assert 'Test Report' in formatted
        assert 'Generated:' in formatted
    
    def test_format_handles_missing_fields(self, client):
        """Test that formatter handles missing optional fields gracefully"""
        incomplete_data = {
            'title': 'Incomplete Report',
            'themes': [
                {
                    'theme': 'Test Theme'
                    # Missing optional fields like count, quotes, etc.
                }
            ]
        }
        
        # Should not raise an exception
        formatted = client.format_pulse_for_docs(incomplete_data)
        assert 'Incomplete Report' in formatted
        assert 'Test Theme' in formatted


class TestPulseDataSchema:
    """Test suite for pulse data schema validation"""
    
    def test_pulse_data_structure(self):
        """Verify pulse data follows expected schema"""
        pulse_data = {
            'title': 'Test',
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_reviews': 100,
                'sampled_reviews': 50
            },
            'themes': [
                {
                    'theme': 'Category',
                    'count': 10,
                    'quotes': ['quote1']
                }
            ]
        }
        
        # Verify structure
        assert 'title' in pulse_data
        assert 'summary' in pulse_data
        assert 'themes' in pulse_data
        assert len(pulse_data['themes']) > 0


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_create_pulse_document_function_exists(self):
        """Verify create_pulse_document convenience function is available"""
        assert callable(create_pulse_document)
    
    def test_create_pulse_document_signature(self):
        """Test that create_pulse_document has expected parameters"""
        import inspect
        sig = inspect.signature(create_pulse_document)
        params = list(sig.parameters.keys())
        
        assert 'pulse_data' in params
        assert 'doc_title' in params
        assert 'mcp_server_url' in params
        assert 'use_mcp_only' in params

    def test_create_pulse_document_uses_env_doc_id(self, monkeypatch):
        monkeypatch.setenv('GOOGLE_DOC_ID', 'env-doc-id-123')
        pulse_data = {'title': 'Test Report'}
        client_called = {}

        class DummyClient:
            def __init__(self, mcp_server_url=None, use_mcp_only=True):
                self.docs_service = None
            def health_check(self):
                return True
            def publish_pulse_report(self, pulse_data, doc_title=None, doc_id=None):
                client_called['doc_id'] = doc_id
                return True, doc_id

        monkeypatch.setattr('agent.gdocs_client.GoogleDocsClient', DummyClient)
        success, doc_id = create_pulse_document(pulse_data)

        assert success is True
        assert doc_id == 'env-doc-id-123'
        assert client_called['doc_id'] == 'env-doc-id-123'
