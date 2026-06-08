#!/usr/bin/env python3
"""
Phase 3 Integration Test Script

This script validates Phase 3 implementation and can be run to:
1. Check MCP server connectivity
2. Test document formatting
3. Verify end-to-end publishing flow
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.gdocs_client import GoogleDocsClient


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_mcp_connectivity():
    """Test MCP server connectivity"""
    print_section("1. MCP Server Connectivity Test")
    
    client = GoogleDocsClient(use_mcp_only=True)
    
    print(f"MCP Server URL: {client.mcp_server_url}")
    print("Checking connectivity...")
    
    if client.health_check():
        print("✅ MCP server is healthy and accessible")
        return True
    else:
        print("❌ MCP server is not responding")
        print("   Please verify:")
        print("   - Server URL is correct")
        print("   - Server is running")
        print("   - Network connectivity is available")
        return False


def test_content_formatting():
    """Test content formatting"""
    print_section("2. Content Formatting Test")
    
    client = GoogleDocsClient(use_mcp_only=True)
    
    # Sample pulse data
    pulse_data = {
        'title': 'Groww Weekly Pulse - Test',
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_reviews': 500,
            'sampled_reviews': 250,
            'date_range': '2026-06-01 to 2026-06-08'
        },
        'themes': [
            {
                'theme': 'User Onboarding',
                'count': 120,
                'sentiment_breakdown': {'positive': 30, 'neutral': 40, 'negative': 50},
                'key_words': ['signup', 'kyc', 'verification'],
                'quotes': ['The signup is too long', 'KYC process is confusing']
            },
            {
                'theme': 'Payments',
                'count': 100,
                'sentiment_breakdown': {'positive': 40, 'neutral': 30, 'negative': 30},
                'key_words': ['payment', 'transaction', 'failed'],
                'quotes': ['Payment failed without error', 'Charges are not transparent']
            }
        ],
        'action_items': [
            {
                'title': 'Simplify KYC',
                'description': 'Reduce required documents',
                'priority': 'High'
            },
            {
                'title': 'Fix Payment Errors',
                'description': 'Add better error messages',
                'priority': 'High'
            }
        ]
    }
    
    print("Formatting pulse data...")
    formatted = client.format_pulse_for_docs(pulse_data)
    
    # Verify structure
    checks = [
        ('Title', 'Groww Weekly Pulse - Test' in formatted),
        ('Summary', 'SUMMARY STATISTICS' in formatted),
        ('Themes', 'TOP THEMES' in formatted),
        ('Actions', 'RECOMMENDED ACTIONS' in formatted),
        ('Theme 1', 'USER ONBOARDING' in formatted or 'User Onboarding' in formatted),
        ('Theme 2', 'PAYMENTS' in formatted or 'Payments' in formatted),
        ('Quotes', 'signup is too long' in formatted),
        ('Actions', 'Simplify KYC' in formatted),
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        all_passed = all_passed and result
    
    print(f"\n📄 Formatted output preview (first 500 chars):")
    print("-" * 60)
    print(formatted[:500] + "...\n")
    
    return all_passed


def test_error_handling():
    """Test error handling"""
    print_section("3. Error Handling Test")
    
    client = GoogleDocsClient(use_mcp_only=True)
    
    tests = []
    
    # Test 1: Invalid doc_id
    print("Testing invalid document ID...")
    result = client.append_via_mcp("invalid_doc_id_12345", "Test content")
    tests.append(("Invalid doc_id handling", not result))
    print(f"✅ Handled gracefully (returned {result})")
    
    # Test 2: Empty content
    print("\nTesting with empty content...")
    try:
        formatted = client.format_pulse_for_docs({})
        tests.append(("Empty data handling", isinstance(formatted, str)))
        print("✅ Handled gracefully (returned formatted string)")
    except Exception as e:
        print(f"❌ Failed with error: {e}")
        tests.append(("Empty data handling", False))
    
    # Test 3: Missing optional fields
    print("\nTesting with missing optional fields...")
    minimal_data = {
        'title': 'Minimal Report'
    }
    try:
        formatted = client.format_pulse_for_docs(minimal_data)
        tests.append(("Missing fields handling", 'Minimal Report' in formatted))
        print("✅ Handled gracefully")
    except Exception as e:
        print(f"❌ Failed with error: {e}")
        tests.append(("Missing fields handling", False))
    
    all_passed = all(result for _, result in tests)
    return all_passed


def test_client_initialization():
    """Test client initialization"""
    print_section("0. Client Initialization Test")
    
    print("Testing GoogleDocsClient initialization...")
    
    try:
        client1 = GoogleDocsClient(use_mcp_only=True)
        print("✅ MCP-only mode initialization successful")
    except Exception as e:
        print(f"❌ MCP-only mode failed: {e}")
        return False
    
    try:
        client2 = GoogleDocsClient()
        print("✅ Default mode initialization successful")
    except Exception as e:
        print(f"❌ Default mode failed: {e}")
        return False
    
    return True


def print_summary(results: dict):
    """Print test summary"""
    print_section("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 3 implementation is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return False


def main():
    """Run all tests"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  Phase 3: Google Docs Integration - Validation Script     ║
    ║  Groww Weekly Review AI Agent                             ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'Client Initialization': test_client_initialization(),
        'MCP Connectivity': test_mcp_connectivity(),
        'Content Formatting': test_content_formatting(),
        'Error Handling': test_error_handling(),
    }
    
    success = print_summary(results)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
