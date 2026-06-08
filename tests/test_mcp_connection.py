import os
import urllib.request
from urllib.error import URLError
import pytest
from dotenv import load_dotenv

# Load env variables if .env exists
load_dotenv()

def test_env_file_variables():
    """Verify that env config file placeholders or actual variables exist."""
    # If .env is not present, we can check .env.example keys
    assert os.path.exists(".env.example"), ".env.example must exist"
    
    # Check that required keys are documented
    with open(".env.example", "r") as f:
        content = f.read()
        assert "GEMINI_API_KEY" in content
        assert "DOCS_MCP_SERVER_URL" in content
        assert "GMAIL_MCP_SERVER_URL" in content

@pytest.mark.skip(reason="MCP servers might not be running during initial setup")
def test_mcp_servers_connectivity():
    """Ping MCP server URLs to verify they are active."""
    docs_url = os.getenv("DOCS_MCP_SERVER_URL", "http://localhost:3010")
    gmail_url = os.getenv("GMAIL_MCP_SERVER_URL", "http://localhost:3011")
    
    # Try connecting to Docs MCP
    try:
        response = urllib.request.urlopen(docs_url, timeout=2)
        assert response.status in [200, 404, 405, 400] # Standard HTTP response indicating server is active
    except URLError as e:
        pytest.fail(f"Could not connect to Google Docs MCP Server at {docs_url}: {e}")
        
    # Try connecting to Gmail MCP
    try:
        response = urllib.request.urlopen(gmail_url, timeout=2)
        assert response.status in [200, 404, 405, 400]
    except URLError as e:
        pytest.fail(f"Could not connect to Gmail MCP Server at {gmail_url}: {e}")
