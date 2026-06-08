# Phase 3: Google Docs Integration - Quick Reference Card

## Installation & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
export DOCS_MCP_SERVER_URL=https://mcp-server-production-e580.up.railway.app

# Validate
python phase3_validate.py
```

## Basic Usage

```python
from agent.gdocs_client import GoogleDocsClient
from datetime import datetime

# Create client
client = GoogleDocsClient()

# Prepare data
pulse_data = {
    'title': 'Groww Weekly Pulse',
    'timestamp': datetime.now().isoformat(),
    'summary': {'total_reviews': 1000, 'sampled_reviews': 500},
    'themes': [
        {'theme': 'Onboarding', 'count': 150, 'quotes': ['...']},
    ],
    'action_items': [
        {'title': 'Action', 'description': 'Do this', 'priority': 'High'},
    ]
}

# Publish
success, doc_id = client.publish_pulse_report(pulse_data)
print(f"https://docs.google.com/document/d/{doc_id}/edit")
```

## Common Operations

### Format Without Publishing
```python
formatted = client.format_pulse_for_docs(pulse_data)
print(formatted)  # View formatted text
```

### Append to Existing Document
```python
client.append_via_mcp(doc_id="existing_id", content="More content")
```

### Check Server Health
```python
if client.health_check():
    print("✅ MCP server is ready")
```

### Create with Custom Title
```python
success, doc_id = client.publish_pulse_report(
    pulse_data=pulse_data,
    doc_title="Custom Title",
    folder_name="My Folder"
)
```

## CLI Commands

```bash
# Dry-run (no publishing)
python phase3_example.py --dry-run

# Create new document
python phase3_example.py

# Append to existing
python phase3_example.py --doc-id YOUR_DOC_ID

# Custom title
python phase3_example.py --doc-title "My Title"

# Validate everything
python phase3_validate.py

# Run tests
pytest tests/test_gdocs_client.py -v
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Check `DOCS_MCP_SERVER_URL` and network |
| Invalid doc_id | Copy full ID from Google Docs URL |
| Permission denied | Ensure authenticated user has edit access |
| Formatting looks wrong | Verify pulse_data structure matches schema |

## Data Schema Checklist

```python
pulse_data = {
    'title': str,                      # ✓ Required
    'timestamp': str,                  # ✓ Required (ISO format)
    'summary': {
        'total_reviews': int,          # ✓ Required
        'sampled_reviews': int,        # ✓ Required
        'date_range': str,             # Optional
    },
    'themes': [                        # ✓ Required (at least 1)
        {
            'theme': str,              # ✓ Required
            'count': int,              # Optional
            'sentiment_breakdown': {},  # Optional
            'key_words': [],           # Optional
            'quotes': [],              # Optional
        }
    ],
    'action_items': [                  # Optional
        {
            'title': str,              # Required if action_items present
            'description': str,        # Optional
            'priority': str,           # Optional
        }
    ],
    'notes': str,                      # Optional
}
```

## API Endpoints (MCP Server)

```
Health Check:
  GET /

Append Content:
  POST /append_to_doc
  {
    "doc_id": "...",
    "content": "..."
  }
```

## Key Methods

| Method | Returns | Use Case |
|--------|---------|----------|
| `publish_pulse_report()` | (bool, doc_id) | Publish new/existing doc |
| `format_pulse_for_docs()` | str | Format without publishing |
| `append_via_mcp()` | bool | Add to existing doc |
| `create_document()` | str \| None | Create blank doc |
| `health_check()` | bool | Verify server |

## Environment Variables

```bash
# Production URL (pre-configured)
DOCS_MCP_SERVER_URL=https://mcp-server-production-e580.up.railway.app

# Optional: Google API credentials
GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/credentials.json
```

## Performance SLOs

- Health Check: <1 second
- Format Content: <100ms
- Append to Doc: 1-3 seconds  
- Create Document: 1-2 seconds
- Full Publish: 3-5 seconds

## Testing

```bash
# All tests
pytest tests/test_gdocs_client.py

# Specific test
pytest tests/test_gdocs_client.py::TestGoogleDocsClient

# With coverage
pytest tests/test_gdocs_client.py --cov

# Verbose
pytest tests/test_gdocs_client.py -v -s
```

## File Structure

```
agent/
  ├── gdocs_client.py          # Main implementation
  └── __init__.py              # Exports

tests/
  └── test_gdocs_client.py     # Tests

/
  ├── phase3_example.py        # CLI examples
  ├── phase3_validate.py       # Validation script
  ├── PHASE3_README.md         # Full README
  ├── PHASE3_QUICKSTART.md     # Quick guide
  └── PHASE3_IMPLEMENTATION_SUMMARY.md
```

## Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed logs
client = GoogleDocsClient()
```

## Integration Points

```
Phase 2 Output (pulse_data)
    ↓
Phase 3 GoogleDocsClient
    ├── Create Document
    ├── Format Content
    └── Append via MCP
    ↓
Google Docs Document
    ↓
Return doc_id to Phase 4 (Email)
```

## Next Steps

1. Run validation: `python phase3_validate.py`
2. Try dry-run: `python phase3_example.py --dry-run`
3. Create document: `python phase3_example.py`
4. Use in pipeline: Import and call methods
5. Customize: Edit `format_pulse_for_docs()` for your needs

---

**Quick Links**
- [Full README](PHASE3_README.md)
- [Quick Start](PHASE3_QUICKSTART.md)
- [Implementation Summary](PHASE3_IMPLEMENTATION_SUMMARY.md)
- [Technical Docs](Docs1/phase3_integration.md)
