"""
Netlify serverless function wrapper for OAuth MCP bridge.

This wraps the FastAPI app for Netlify's serverless function environment.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from http_mcp_oauth_bridge import app
from mangum import Mangum

# Wrap FastAPI app with Mangum for AWS Lambda/Netlify compatibility
handler = Mangum(app)

def lambda_handler(event, context):
    """AWS Lambda handler for Netlify Functions."""
    return handler(event, context)

