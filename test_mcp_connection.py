#!/usr/bin/env python3
"""
Test MCP server connection
Helps troubleshoot 403 Forbidden errors
"""
import requests
import json
import sys
from typing import Dict, Any, Optional

def test_connection(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """Test connection to MCP server."""
    result = {
        "url": url,
        "method": method,
        "status_code": None,
        "headers": {},
        "response": None,
        "error": None,
        "success": False
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=timeout
            )
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        result["status_code"] = response.status_code
        result["headers"] = dict(response.headers)
        result["success"] = response.status_code < 400
        
        # Try to parse JSON response
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:500]  # First 500 chars
        
        if response.status_code == 403:
            result["error"] = "403 Forbidden - Check authentication and CORS"
        elif response.status_code == 401:
            result["error"] = "401 Unauthorized - Authentication required"
        elif response.status_code == 404:
            result["error"] = "404 Not Found - Endpoint may not exist"
        elif response.status_code >= 500:
            result["error"] = f"{response.status_code} Server Error - Server issue"
            
    except requests.exceptions.Timeout:
        result["error"] = "Timeout - Server not responding"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection Error - Cannot reach server"
    except Exception as e:
        result["error"] = str(e)
    
    return result

def main():
    """Main test function."""
    url = "https://zingy-profiterole-f31cb8.netlify.app/mcp"
    
    print("=" * 60)
    print("MCP Server Connection Test")
    print("=" * 60)
    print(f"URL: {url}\n")
    
    # Test 1: GET request
    print("Test 1: GET request (no auth)")
    print("-" * 60)
    result1 = test_connection(url, method="GET")
    print(f"Status: {result1['status_code']}")
    if result1['error']:
        print(f"Error: {result1['error']}")
    if result1['headers']:
        print(f"CORS Headers: {result1['headers'].get('Access-Control-Allow-Origin', 'Not set')}")
    print()
    
    # Test 2: POST request (MCP typically uses POST)
    print("Test 2: POST request (no auth)")
    print("-" * 60)
    result2 = test_connection(
        url,
        method="POST",
        headers={"Content-Type": "application/json"},
        data={"jsonrpc": "2.0", "method": "initialize", "params": {}}
    )
    print(f"Status: {result2['status_code']}")
    if result2['error']:
        print(f"Error: {result2['error']}")
    if result2['headers']:
        print(f"CORS Headers: {result2['headers'].get('Access-Control-Allow-Origin', 'Not set')}")
    print()
    
    # Test 3: POST with common auth headers
    print("Test 3: POST request (with common auth headers)")
    print("-" * 60)
    result3 = test_connection(
        url,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token",
            "User-Agent": "MCP-Client/1.0"
        },
        data={"jsonrpc": "2.0", "method": "initialize", "params": {}}
    )
    print(f"Status: {result3['status_code']}")
    if result3['error']:
        print(f"Error: {result3['error']}")
    print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if result2['status_code'] == 200:
        print("✅ Server is accessible and responding")
    elif result2['status_code'] == 403:
        print("❌ 403 Forbidden - Authentication or CORS issue")
        print("\nPossible solutions:")
        print("1. Check if API key is required")
        print("2. Verify CORS configuration on server")
        print("3. Check if endpoint path is correct")
        print("4. Verify server is configured to accept MCP requests")
    elif result2['status_code'] == 401:
        print("❌ 401 Unauthorized - Authentication required")
        print("\nPossible solutions:")
        print("1. Get an API key from server administrator")
        print("2. Add Authorization header to requests")
        print("3. Check server documentation for auth requirements")
    elif result2['status_code'] == 404:
        print("❌ 404 Not Found - Endpoint may not exist")
        print("\nPossible solutions:")
        print("1. Verify the URL path is correct")
        print("2. Check if server is deployed correctly")
        print("3. Verify Netlify function is configured")
    else:
        print(f"❌ Status {result2['status_code']} - Check server logs")
    
    # Save results
    output_file = "mcp_connection_test.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "test1_get": result1,
            "test2_post": result2,
            "test3_post_auth": result3
        }, f, indent=2)
    print(f"\n📄 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

