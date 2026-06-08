# Phase 3: Google Docs Integration

## Overview

Phase 3 implements the Google Docs integration layer for the Groww Weekly Review AI Agent. This phase publishes generated pulse reports directly to Google Docs using the MCP server, with optional support for direct Google Docs API integration for advanced features.

## Architecture

```
┌─────────────────────────────┐
│  Pulse Report Data (JSON)   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   GoogleDocsClient          │
│  - Format content           │
│  - Create documents         │
│  - Manage folders           │
└──────────────┬──────────────┘
               │
        ┌──────┴───────┐
        ▼              ▼
┌──────────────┐ ┌─────────────────┐
│ Google Docs  │ │  MCP Server     │
│ API (direct) │ │ /append_to_doc  │
└──────────────┘ └─────────────────┘
        │              │
        └──────┬───────┘
               ▼
        ┌─────────────────┐
        │  Google Drive   │
        │  Google Docs    │
        └─────────────────┘
```

## Components

### 1. GoogleDocsClient (`agent/gdocs_client.py`)

Main client class for Google Docs integration.

#### Key Features:

- **Document Creation**: Creates new Google Documents with formatted titles
- **Content Formatting**: Transforms JSON pulse data into structured Google Docs format
- **Folder Management**: Organizes documents in Google Drive folders
- **MCP Integration**: Communicates with MCP server for content appending
- **Error Handling**: Graceful fallback and logging for all operations
- **Health Checks**: Verifies MCP server availability

#### Methods:

##### `create_document(title: str, folder_id: str = None) -> Optional[str]`
Creates a new blank Google Document.

```python
client = GoogleDocsClient()
doc_id = client.create_document(
    title="Groww Weekly Pulse - 2026-W23",
    folder_id="folder_id_from_drive"
)
```

##### `append_via_mcp(doc_id: str, content: str) -> bool`
Appends formatted content to a document via MCP server.

```python
success = client.append_via_mcp(
    doc_id="document_id",
    content="Formatted pulse report content"
)
```

##### `format_pulse_for_docs(pulse_data: Dict) -> str`
Converts JSON pulse data into formatted text content.

```python
formatted = client.format_pulse_for_docs(pulse_data)
# Returns structured text with headers, lists, etc.
```

##### `publish_pulse_report(pulse_data: Dict, doc_title: str = None, doc_id: str = None) -> Tuple[bool, Optional[str]]`
Main method to create and publish a complete pulse report.

```python
success, doc_id = client.publish_pulse_report(
    pulse_data=pulse_data,
    doc_title="Groww Weekly Pulse - 2026-W23"
)
```

##### `health_check() -> bool`
Verifies MCP server is healthy and responsive.

```python
if client.health_check():
    print("MCP server is available")
```

### 2. Convenience Function (`agent/gdocs_client.py`)

#### `create_pulse_document(pulse_data, doc_title=None, mcp_server_url=None, use_mcp_only=True) -> Tuple[bool, Optional[str]]`

Simplified entry point for publishing pulse reports.

```python
from agent.gdocs_client import create_pulse_document

success, doc_id = create_pulse_document(
    pulse_data=my_pulse_data,
    doc_title="Custom Title",
    use_mcp_only=True
)

if success:
    print(f"Published to: https://docs.google.com/document/d/{doc_id}/edit")
```

## Usage Examples

### Example 1: Basic Publication (MCP-Only Mode)

```python
from agent.gdocs_client import GoogleDocsClient
from datetime import datetime

# Initialize client
client = GoogleDocsClient(
    mcp_server_url="https://mcp-server-production-e580.up.railway.app",
    use_mcp_only=True
)

# Prepare pulse data
pulse_data = {
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
            'quotes': ['Quote 1', 'Quote 2']
        }
    ],
    'action_items': [
        {
            'title': 'Improve KYC Process',
            'description': 'Simplify verification steps',
            'priority': 'High'
        }
    ]
}

# Publish
success, doc_id = client.publish_pulse_report(
    pulse_data=pulse_data,
    doc_title="Groww Weekly Pulse - 2026-W23"
)

if success:
    print(f"✅ Published! View at: https://docs.google.com/document/d/{doc_id}/edit")
```

### Example 2: Using Convenience Function

```python
from agent.gdocs_client import create_pulse_document

success, doc_id = create_pulse_document(
    pulse_data=pulse_data,
    doc_title="Weekly Review",
    mcp_server_url="https://mcp-server-production-e580.up.railway.app"
)
```

### Example 3: Dry-Run Mode (No Publishing)

```python
from agent.gdocs_client import GoogleDocsClient

client = GoogleDocsClient(use_mcp_only=True)
formatted_content = client.format_pulse_for_docs(pulse_data)
print(formatted_content)  # View formatted output without publishing
```

### Example 4: Append to Existing Document

```python
# Append to an existing Google Doc
client = GoogleDocsClient()
success = client.append_via_mcp(
    doc_id="existing_doc_id_from_google_docs",
    content=formatted_content
)
```

## Input Data Schema

### Pulse Data Structure

```json
{
  "title": "Groww Weekly Pulse Report",
  "timestamp": "2026-06-08T12:00:00.000000",
  "summary": {
    "total_reviews": 1247,
    "sampled_reviews": 500,
    "date_range": "2026-06-01 to 2026-06-08"
  },
  "themes": [
    {
      "theme": "Onboarding",
      "count": 234,
      "sentiment_breakdown": {
        "positive": 30,
        "neutral": 50,
        "negative": 154
      },
      "key_words": ["signup", "kyc", "verification"],
      "quotes": [
        "Quote 1",
        "Quote 2",
        "Quote 3"
      ]
    }
  ],
  "action_items": [
    {
      "title": "Action Title",
      "description": "Detailed description",
      "priority": "High"
    }
  ],
  "notes": "Additional notes for context"
}
```

## Output Format

The formatted Google Docs content follows this structure:

```
Groww Weekly Pulse Report

Generated: 2026-06-08T12:00:00

SUMMARY STATISTICS
Total Reviews Analyzed: 1247
Reviews Sampled: 500
Date Range: 2026-06-01 to 2026-06-08

TOP THEMES

1. ONBOARDING
   Count: 234 reviews
   Sentiment: Positive 30 | Neutral 50 | Negative 154
   Key Words: signup, kyc, verification, documents, rejected
   Representative Quotes:
   - "Quote 1"
   - "Quote 2"
   - "Quote 3"

... (additional themes)

RECOMMENDED ACTIONS

1. Simplify KYC Process
   Reduce required documents from 5 to 3
   Priority: High

... (additional actions)

NOTES
Report context and insights.
```

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# MCP Server
DOCS_MCP_SERVER_URL=https://mcp-server-production-e580.up.railway.app

# Google Docs API (Optional - for direct document creation)
# Uncomment to use service account for document creation
# GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/credentials.json
```

### Setup Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure MCP Server**
   - Update `DOCS_MCP_SERVER_URL` in `.env` file
   - Verify server is accessible: `curl https://mcp-server-production-e580.up.railway.app/`

3. **Optional: Setup Google Docs API** (for direct document creation)
   - Create Google Cloud project
   - Enable Google Docs and Drive APIs
   - Create OAuth credentials or service account
   - Download credentials JSON
   - Set `GOOGLE_SERVICE_ACCOUNT_JSON` in `.env`

## MCP Server Integration

### Supported Endpoints

#### POST `/append_to_doc`
Appends content to a Google Document.

**Request:**
```json
{
  "doc_id": "google_doc_id",
  "content": "Content to append"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Content appended to document",
  "document_id": "google_doc_id"
}
```

### Health Check

```bash
curl https://mcp-server-production-e580.up.railway.app/
```

## Testing

### Run Unit Tests

```bash
pytest tests/test_gdocs_client.py -v
```

### Run Integration Example

```bash
# Dry-run mode (format without publishing)
python phase3_example.py --dry-run

# Create new document and publish
python phase3_example.py

# Append to existing document
python phase3_example.py --doc-id YOUR_DOC_ID

# Custom title
python phase3_example.py --doc-title "My Custom Title"
```

## Error Handling

The client gracefully handles various error scenarios:

### 1. MCP Server Unavailable
```
→ Logs error and returns False
→ Suggests checking server URL and connectivity
```

### 2. Invalid Document ID
```
→ MCP server returns error status
→ Logs and propagates error
```

### 3. Missing Credentials
```
→ If using MCP-only mode: works fine
→ If trying direct API: falls back to MCP mode
```

### 4. Network Timeouts
```
→ 30-second timeout on all HTTP requests
→ Logs timeout error and returns False
```

## Logging

All operations are logged to Python logger with appropriate levels:

```python
import logging
logging.basicConfig(level=logging.INFO)

# View logs
logger = logging.getLogger('agent.gdocs_client')
```

## Troubleshooting

### Issue: MCP server connection refused

**Solution:**
1. Verify server URL is correct: `DOCS_MCP_SERVER_URL`
2. Check server is running: `curl https://mcp-server-production-e580.up.railway.app/`
3. Verify network connectivity

### Issue: Permission denied appending to document

**Solution:**
1. Verify document ID is correct
2. Ensure authenticated user has edit access to document
3. Check MCP server logs for detailed error

### Issue: Document creation fails

**Solution:**
1. Ensure `use_mcp_only=False` and Google API credentials are configured
2. Check `GOOGLE_SERVICE_ACCOUNT_JSON` path is correct
3. Verify Google Docs API is enabled in Google Cloud Console

## Future Enhancements

1. **Advanced Formatting**: Support for tables, charts, and embedded images
2. **Document Templates**: Pre-defined layout templates for different report types
3. **Batch Operations**: Publish multiple documents in parallel
4. **Version Control**: Track document versions and changes over time
5. **Email Notifications**: Automatically send notification emails when documents are published
6. **Custom Styling**: User-configurable fonts, colors, and layouts
7. **Scheduled Publishing**: Automatic weekly/monthly publication schedule

## Related Documentation

- [Phase 2: Thematic Analysis](../Docs1/implementationplan.md#phase-2)
- [Phase 4: Email Distribution](../Docs1/implementationplan.md#phase-4)
- [MCP Server Documentation](https://github.com/saksham20189575/saksham-mcp-server)
- [Google Docs API Documentation](https://developers.google.com/docs)

## Verification Checklist

- ✅ GoogleDocsClient initializes without errors
- ✅ Health check passes for MCP server
- ✅ Document creation succeeds (when Google API available)
- ✅ Content formatting produces clean, readable output
- ✅ MCP append_to_doc call succeeds
- ✅ Proper error handling for all failure scenarios
- ✅ Logging captures all operations
- ✅ Integration example runs without errors
- ✅ Test suite passes
