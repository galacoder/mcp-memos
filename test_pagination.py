#!/usr/bin/env python3
"""Test script for enhanced Memos pagination and response formatting"""

import json
import os
from enhanced_memos import EnhancedMemos, EnhancedMemosSearchParams, ResponseFormat, SearchResponse


def test_pagination():
    """Test pagination functionality"""
    # Get credentials from environment
    memos_url = os.getenv("MEMOS_URL", "https://memos.galatek.dev")
    memos_api_key = os.getenv("MEMOS_API_KEY", "")
    
    if not memos_api_key:
        print("Error: MEMOS_API_KEY not set")
        return
    
    # Initialize client
    client = EnhancedMemos(memos_url, memos_api_key)
    
    print("Testing Enhanced Memos Pagination\n" + "="*50)
    
    # Test 1: Basic pagination with limit
    print("\nTest 1: Basic Pagination (limit=5)")
    params = EnhancedMemosSearchParams(
        query="",
        limit=5,
        offset=0,
        response_format=ResponseFormat.MINIMAL
    )
    
    try:
        response = client.search_memos_enhanced(params)
        print(f"Total memos: {response.total_count}")
        print(f"Returned: {len(response.memos)}")
        print(f"Has more: {response.has_more}")
        print(f"Next offset: {response.next_offset}")
        print(f"Sample memo (minimal format): {json.dumps(response.memos[0] if response.memos else {}, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Pagination with offset
    print("\n\nTest 2: Pagination with Offset (limit=3, offset=5)")
    params = EnhancedMemosSearchParams(
        query="",
        limit=3,
        offset=5,
        response_format=ResponseFormat.SUMMARY
    )
    
    try:
        response = client.search_memos_enhanced(params)
        print(f"Returned: {len(response.memos)}")
        print(f"Content truncated to {params.content_max_length} chars")
        if response.memos:
            memo = response.memos[0]
            print(f"Sample content length: {len(memo.get('content', ''))}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Response formats comparison
    print("\n\nTest 3: Response Format Comparison")
    
    formats = [ResponseFormat.ID_ONLY, ResponseFormat.MINIMAL, ResponseFormat.SUMMARY, ResponseFormat.FULL]
    
    for fmt in formats:
        params = EnhancedMemosSearchParams(
            query="",
            limit=1,
            response_format=fmt
        )
        try:
            response = client.search_memos_enhanced(params)
            if response.memos:
                memo = response.memos[0]
                memo_json = json.dumps(memo, indent=2)
                print(f"\n{fmt.value.upper()} format (size: {len(memo_json)} chars):")
                if len(memo_json) > 200:
                    print(memo_json[:200] + "...")
                else:
                    print(memo_json)
        except Exception as e:
            print(f"Error with {fmt.value}: {e}")
    
    # Test 4: Search with pagination
    print("\n\nTest 4: Search with Pagination")
    params = EnhancedMemosSearchParams(
        query="mcp",  # Search for MCP-related memos
        limit=5,
        response_format=ResponseFormat.SUMMARY
    )
    
    try:
        response = client.search_memos_enhanced(params)
        print(f"Found {response.total_count} memos containing 'mcp'")
        print(f"Showing first {len(response.memos)} results")
        
        for i, memo in enumerate(response.memos[:3]):
            print(f"\n{i+1}. ID: {memo['id']}")
            print(f"   Content preview: {memo.get('content', '')[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Token usage estimation
    print("\n\nTest 5: Token Usage Estimation")
    
    # Full response (old method simulation)
    all_memos = client.search_memos("")  # Old method returns all
    full_size = len(json.dumps(all_memos))
    
    # New paginated response
    params = EnhancedMemosSearchParams(
        query="",
        limit=10,
        response_format=ResponseFormat.SUMMARY,
        content_max_length=200
    )
    response = client.search_memos_enhanced(params)
    paginated_size = len(json.dumps(response.memos))
    
    print(f"Full response size: {full_size:,} chars")
    print(f"Paginated response size: {paginated_size:,} chars")
    print(f"Reduction: {((full_size - paginated_size) / full_size * 100):.1f}%")
    
    # Test 6: Backward compatibility
    print("\n\nTest 6: Backward Compatibility")
    try:
        # Old method should still work
        old_results = client.search_memos("test")
        print(f"Old search_memos() still works: {len(old_results)} results")
        
        latest = client.get_latest_memos(3)
        print(f"get_latest_memos() returns: {len(latest)} memos")
    except Exception as e:
        print(f"Backward compatibility error: {e}")


if __name__ == "__main__":
    test_pagination()