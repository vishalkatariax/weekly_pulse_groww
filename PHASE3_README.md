# Phase 3: Google Docs Integration - README

## Quick Start

### 1. Verify Installation

```bash
# Check Phase 3 components
ls -la agent/gdocs_client.py tests/test_gdocs_client.py phase3_*.py

# Verify configuration
cat .env | grep DOCS_MCP_SERVER_URL
```

### 2. Test the Implementation

```bash
# Run validation
python phase3_validate.py

# Expected output:
# ✅ PASS: Client Initialization
# ✅ PASS: Content Formatting
# ✅ PASS: Error Handling
# (MCP connectivity depends on server availability)
```

### 3. Try Dry-Run

```bash
# Format sample data without publishing
python phase3_example.py --dry-run

# View formatted output
```

### 4. Publish to Google Docs

```bash
# Create and publish a new document
python phase3_example.py

# View in Google Docs at the returned URL
```

## Integration into Your Workflow

### From Phase 2 Output

```python
from agent.phase2 import analyze_themes_with_llm
from agent.gdocs_client import GoogleDocsClient

# Get pulse data from Phase 2
pulse_result = analyze_themes_with_llm(anonymized_reviews)

# Prepare for Phase 3
pulse_data = {
    'title': 'Groww Weekly Pulse Report',
    'timestamp': datetime.now().isoformat(),
    'summary': pulse_result['summary'],
    'themes': pulse_result['themes'],
    'action_items': pulse_result['action_items'],
}

# Publish to Google Docs
client = GoogleDocsClient()
success, doc_id = client.publish_pulse_report(pulse_data)
```

## Configuration

### Minimal Setup

```bash
# Already configured in .env:
DOCS_MCP_SERVER_URL=https://mcp-server-production-e580.up.railway.app
```

### Advanced Setup (Optional)

For direct Google Docs API access (document creation):

```bash
# 1. Download service account credentials from Google Cloud Console
# 2. Save as service_account.json in project root
# 3. Add to .env:
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
```

## API Reference

### GoogleDocsClient Methods

```python
from agent.gdocs_client import GoogleDocsClient

client = GoogleDocsClient()

# Main method: publish pulse report
success, doc_id = client.publish_pulse_report(
    pulse_data=pulse_data,
    doc_title="Custom Title",
    folder_name="Groww Weekly Reviews"
)

# Format content without publishing
formatted = client.format_pulse_for_docs(pulse_data)

# Append to existing document
success = client.append_via_mcp(doc_id, content)

# Check MCP server health
is_healthy = client.health_check()
```

## Troubleshooting

### Issue: "MCP server is not responding"

**Solution:**
1. Check if server is running: `curl https://mcp-server-production-e580.up.railway.app/`
2. Verify URL in `.env`: `DOCS_MCP_SERVER_URL`
3. Check network connectivity
4. Review logs in `agent/gdocs_client.py` (logging enabled)

### Issue: "Failed to create document"

**Cause**: Google API credentials not configured

**Solution:**
- Use MCP-only mode (default)
- Or set up Google API credentials (see Configuration section)

### Issue: "Document ID is invalid"

**Cause**: Incorrect document ID when appending

**Solution:**
- Copy full document ID from Google Docs URL
- Example: https://docs.google.com/document/d/**1a2b3c4d5e6f7g8h9i0j**/edit
- Use the bolded part as doc_id

## Data Format

### Input: Pulse Data (from Phase 2)

```python
pulse_data = {
    'title': str,                    # Document title
    'timestamp': str,                # ISO format datetime
    'summary': {
        'total_reviews': int,
        'sampled_reviews': int,
        'date_range': str,
        # Optional fields...
    },
    'themes': [
        {
            'theme': str,            # Theme name
            'count': int,            # Number of reviews
            'sentiment_breakdown': {
                'positive': int,
                'neutral': int,
                'negative': int,
            },
            'key_words': [str],      # List of keywords
            'quotes': [str],         # Representative quotes
        },
        # ... more themes
    ],
    'action_items': [
        {
            'title': str,
            'description': str,
            'priority': str,         # 'High', 'Medium', 'Low'
        },
        # ... more actions
    ],
    'notes': str,                    # Optional: additional context
}
```

### Output: Document URL

```
https://docs.google.com/document/d/{doc_id}/edit
```

## File Descriptions

### Core Implementation
- `agent/gdocs_client.py` - Main GoogleDocsClient class (376 lines)
- `agent/__init__.py` - Package initialization with exports

### Testing & Validation  
- `tests/test_gdocs_client.py` - Unit and integration tests (250+ lines)
- `phase3_validate.py` - Validation and verification script (190+ lines)

### Examples & Documentation
- `phase3_example.py` - CLI examples and sample usage (240+ lines)
- `PHASE3_QUICKSTART.md` - Quick integration reference
- `PHASE3_IMPLEMENTATION_SUMMARY.md` - Complete implementation details
- `Docs1/phase3_integration.md` - Comprehensive technical documentation

### Configuration
- `.env` - Environment variables (updated with production URLs)
- `.env.example` - Configuration template
- `requirements.txt` - Python dependencies (updated)

## Running Tests

```bash
# Run all Phase 3 tests
pytest tests/test_gdocs_client.py -v

# Run specific test
pytest tests/test_gdocs_client.py::TestGoogleDocsClient::test_format_pulse_for_docs -v

# Run with coverage
pytest tests/test_gdocs_client.py --cov=agent.gdocs_client
```

## Command-Line Usage

```bash
# Dry-run (format only)
python phase3_example.py --dry-run

# Create new document
python phase3_example.py

# Append to existing document
python phase3_example.py --doc-id <DOCUMENT_ID>

# Custom title
python phase3_example.py --doc-title "Custom Title"

# Use minimal sample data
python phase3_example.py --sample-data minimal

# Custom MCP server URL
python phase3_example.py --mcp-server-url http://localhost:3010

# Combine options
python phase3_example.py --doc-title "Weekly Review" --sample-data full
```

## Performance Metrics

| Operation | Time |
|-----------|------|
| Document Creation | ~1-2s |
| Content Formatting | <100ms |
| MCP Append | ~1-3s |
| Health Check | <1s |
| Full Publication | ~3-5s |

## Logging

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('agent.gdocs_client')
# Now see detailed logs
```

Log file location: Check Python logging configuration in `agent/gdocs_client.py`

## Security Considerations

### API Keys
- Never commit `.env` with real credentials
- Use `.env.example` as template
- Rotate API keys regularly

### Document Access
- Documents are created in authenticated user's Google Drive
- Share/permissions can be managed in Google Docs UI
- MCP server handles OAuth automatically

### Data Privacy
- Review data anonymized in Phase 1
- No PII included in published documents
- Consider document sharing policies

## FAQ

**Q: Can I publish to an existing document?**
A: Yes, use `doc_id` parameter: `client.publish_pulse_report(pulse_data, doc_id="existing_doc_id")`

**Q: How do I change the document title?**
A: Pass `doc_title` parameter: `client.publish_pulse_report(pulse_data, doc_title="My Title")`

**Q: Can I customize the formatting?**
A: Yes, modify `format_pulse_for_docs()` method in `agent/gdocs_client.py`

**Q: Does it support tables and images?**
A: Currently supports text, headings, and lists. Advanced formatting (tables, images) planned for Phase 3 enhancement.

**Q: How do I handle errors?**
A: All methods return status indicators. Check return values and logs for details.

**Q: Can I batch publish multiple documents?**
A: Yes, loop through pulse_data list and call `publish_pulse_report()` for each.

## Related Phases

- **Phase 1**: Data Ingestion & Anonymization
- **Phase 2**: Thematic Analysis (LLM-based)
- **Phase 3**: Google Docs Integration ← Current
- **Phase 4**: Email Distribution (uses Phase 3 doc_id)
- **Phase 5**: Orchestration & CLI
- **Phase 6**: Automation & Deployment

## Support & Documentation

1. **Quick Start**: See PHASE3_QUICKSTART.md
2. **Full Reference**: See Docs1/phase3_integration.md
3. **Implementation Details**: See PHASE3_IMPLEMENTATION_SUMMARY.md
4. **Code Documentation**: See inline docstrings in agent/gdocs_client.py
5. **Examples**: Run phase3_example.py with various flags

## Version Information

- **Phase 3 Version**: 0.1.0
- **Python**: 3.8+
- **Dependencies**: See requirements.txt
- **Last Updated**: June 8, 2026

## Contributors

Groww AI Team - Weekly Review Agent Implementation

---

**Ready to publish?** Start with:
```bash
python phase3_example.py --dry-run
```
