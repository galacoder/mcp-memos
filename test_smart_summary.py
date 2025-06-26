#!/usr/bin/env python3
"""Test script for smart content summarization features"""

import json
import os
from enhanced_memos import EnhancedMemos, EnhancedMemosSearchParams, ResponseFormat


def test_smart_summarization():
    """Test smart summarization functionality"""
    # Get credentials from environment
    memos_url = os.getenv("MEMOS_URL", "https://memos.galatek.dev")
    memos_api_key = os.getenv("MEMOS_API_KEY", "")
    
    if not memos_api_key:
        print("Error: MEMOS_API_KEY not set")
        return
    
    # Initialize client
    client = EnhancedMemos(memos_url, memos_api_key)
    
    print("Testing Smart Content Summarization\n" + "="*50)
    
    # Test 1: Search with snippet extraction
    print("\nTest 1: Search with Snippet Extraction")
    params = EnhancedMemosSearchParams(
        query="mcp",
        limit=5,
        response_format=ResponseFormat.SUMMARY,
        summary_only=True,
        content_max_length=300
    )
    
    try:
        response = client.search_memos_enhanced(params)
        print(f"Found {response.total_count} memos containing 'mcp'")
        
        for i, memo in enumerate(response.memos[:3]):
            print(f"\n{i+1}. Memo ID: {memo['id']}")
            print(f"   Relevance Score: {memo.get('relevance_score', 0):.2f}")
            
            # Show match snippets
            if 'match_snippets' in memo:
                print("   Match Snippets:")
                for j, snippet in enumerate(memo['match_snippets']):
                    print(f"     {j+1}: {snippet}")
            
            # Show smart summary
            print(f"   Smart Summary: {memo.get('content', '')[:150]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Compare with and without smart summarization
    print("\n\nTest 2: Smart Summary vs Regular Truncation")
    
    # Regular truncation
    params_regular = EnhancedMemosSearchParams(
        query="",
        limit=1,
        response_format=ResponseFormat.SUMMARY,
        summary_only=False,
        content_max_length=200
    )
    
    # Smart summary
    params_smart = EnhancedMemosSearchParams(
        query="",
        limit=1,
        response_format=ResponseFormat.SUMMARY,
        summary_only=True,
        content_max_length=200
    )
    
    try:
        response_regular = client.search_memos_enhanced(params_regular)
        response_smart = client.search_memos_enhanced(params_smart)
        
        if response_regular.memos and response_smart.memos:
            print("Regular Truncation:")
            print(response_regular.memos[0].get('content', '')[:200])
            print("\nSmart Summary (prioritizes headers/lists):")
            print(response_smart.memos[0].get('content', '')[:200])
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Relevance scoring
    print("\n\nTest 3: Relevance Scoring for Search Results")
    params = EnhancedMemosSearchParams(
        query="notion",
        limit=10,
        response_format=ResponseFormat.SUMMARY,
        summary_only=True
    )
    
    try:
        response = client.search_memos_enhanced(params)
        print(f"Search results for 'notion' (sorted by relevance):")
        
        for i, memo in enumerate(response.memos[:5]):
            score = memo.get('relevance_score', 0)
            print(f"\n{i+1}. Score: {score:.2f} - {memo['id']}")
            
            # Show why it's relevant
            if 'match_snippets' in memo and memo['match_snippets']:
                print(f"   First match: {memo['match_snippets'][0][:100]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Token reduction with smart summaries
    print("\n\nTest 4: Token Reduction Analysis")
    
    # Get a memo with full content
    params_full = EnhancedMemosSearchParams(
        query="",
        limit=5,
        response_format=ResponseFormat.FULL
    )
    
    params_smart = EnhancedMemosSearchParams(
        query="",
        limit=5,
        response_format=ResponseFormat.SUMMARY,
        summary_only=True,
        content_max_length=200
    )
    
    try:
        response_full = client.search_memos_enhanced(params_full)
        response_smart = client.search_memos_enhanced(params_smart)
        
        full_size = len(json.dumps(response_full.memos))
        smart_size = len(json.dumps(response_smart.memos))
        
        print(f"Full content size: {full_size:,} chars")
        print(f"Smart summary size: {smart_size:,} chars")
        print(f"Reduction: {((full_size - smart_size) / full_size * 100):.1f}%")
        
        # Show character savings per memo
        if response_full.memos and response_smart.memos:
            for i in range(min(3, len(response_full.memos))):
                full_memo_size = len(json.dumps(response_full.memos[i]))
                smart_memo_size = len(json.dumps(response_smart.memos[i]))
                print(f"\nMemo {i+1}: {full_memo_size:,} -> {smart_memo_size:,} chars "
                      f"({((full_memo_size - smart_memo_size) / full_memo_size * 100):.1f}% reduction)")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Highlighting in search results
    print("\n\nTest 5: Search Term Highlighting")
    params = EnhancedMemosSearchParams(
        query="task",
        limit=3,
        response_format=ResponseFormat.SUMMARY,
        summary_only=True
    )
    
    try:
        response = client.search_memos_enhanced(params)
        print(f"Searching for 'task' with highlighting:")
        
        for i, memo in enumerate(response.memos):
            print(f"\n{i+1}. {memo['id']}")
            if 'match_snippets' in memo:
                for snippet in memo['match_snippets'][:2]:
                    # The snippet should have **task** highlighted
                    print(f"   → {snippet}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_smart_summarization()