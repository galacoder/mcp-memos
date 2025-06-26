#!/usr/bin/env python3
"""Direct test of enhanced Memos MCP server"""

import os
import json
from enhanced_memos import EnhancedMemos, EnhancedMemosSearchParams, ResponseFormat

# Set up environment
memos_url = "https://memos.galatek.dev"
memos_api_key = "eyJhbGciOiJIUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJuYW1lIjoiIiwiaXNzIjoibWVtb3MiLCJzdWIiOiIxIiwiYXVkIjpbInVzZXIuYWNjZXNzLXRva2VuIl0sImV4cCI6NDkwMzIwNzc3OSwiaWF0IjoxNzQ5NjA3Nzc5fQ.R2owAia5reyIaYKpzATcOaUJ-cM08z5jJlSha9MA7zs"

# Initialize client
client = EnhancedMemos(memos_url, memos_api_key)

print("Testing Enhanced Memos Direct Connection\n" + "="*40)

# Test 1: Get latest with minimal format
print("\n1. Testing get_latest_memos with MINIMAL format:")
try:
    params = EnhancedMemosSearchParams(
        limit=3,
        response_format=ResponseFormat.MINIMAL
    )
    response = client.search_memos_enhanced(params)
    print(f"Found {response.total_count} total memos")
    print(f"Returned {len(response.memos)} memos")
    print(f"Response size: {len(json.dumps(response.memos))} chars")
    
    if response.memos:
        print("\nFirst memo (minimal):")
        print(json.dumps(response.memos[0], indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 2: Search with smart summary
print("\n\n2. Testing search with SUMMARY format:")
try:
    params = EnhancedMemosSearchParams(
        query="mcp",
        limit=5,
        response_format=ResponseFormat.SUMMARY,
        summary_only=True,
        content_max_length=200
    )
    response = client.search_memos_enhanced(params)
    print(f"Found {response.total_count} memos containing 'mcp'")
    
    if response.memos:
        print("\nFirst result:")
        memo = response.memos[0]
        print(f"ID: {memo['id']}")
        print(f"Relevance: {memo.get('relevance_score', 0):.2f}")
        print(f"Content: {memo.get('content', '')[:150]}...")
except Exception as e:
    print(f"Error: {e}")

print("\n✅ Direct test complete!")