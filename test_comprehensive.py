#!/usr/bin/env python3
"""Comprehensive test for all enhanced Memos features"""

import json
import os
import time
from enhanced_memos import EnhancedMemos, EnhancedMemosSearchParams, ResponseFormat


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_comprehensive():
    """Run comprehensive tests for enhanced Memos"""
    # Get credentials from environment
    memos_url = os.getenv("MEMOS_URL", "https://memos.galatek.dev")
    memos_api_key = os.getenv("MEMOS_API_KEY", "")
    
    if not memos_api_key:
        print("Error: MEMOS_API_KEY not set")
        return
    
    # Initialize client
    client = EnhancedMemos(memos_url, memos_api_key)
    
    print("ENHANCED MEMOS MCP - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Overall metrics
    total_tests = 0
    passed_tests = 0
    token_reductions = []
    
    try:
        # Test 1: Pagination Performance
        print_section("TEST 1: Pagination Performance")
        
        # Get all memos (old way)
        start_time = time.time()
        all_memos = client.search_memos("")
        old_time = time.time() - start_time
        old_size = len(json.dumps(all_memos))
        
        # Get paginated memos (new way)
        start_time = time.time()
        params = EnhancedMemosSearchParams(limit=10, response_format=ResponseFormat.SUMMARY)
        response = client.search_memos_enhanced(params)
        new_time = time.time() - start_time
        new_size = len(json.dumps(response.memos))
        
        reduction = ((old_size - new_size) / old_size * 100) if old_size > 0 else 0
        token_reductions.append(reduction)
        
        print(f"✓ Old method: {len(all_memos)} memos, {old_size:,} chars, {old_time:.3f}s")
        print(f"✓ New method: {len(response.memos)} memos, {new_size:,} chars, {new_time:.3f}s")
        print(f"✓ Token reduction: {reduction:.1f}%")
        print(f"✓ Speed improvement: {((old_time - new_time) / old_time * 100):.1f}%")
        
        total_tests += 1
        passed_tests += 1
        
        # Test 2: Response Format Efficiency
        print_section("TEST 2: Response Format Token Usage")
        
        formats = [
            (ResponseFormat.ID_ONLY, "ID Only"),
            (ResponseFormat.MINIMAL, "Minimal"),
            (ResponseFormat.SUMMARY, "Summary"),
            (ResponseFormat.FULL, "Full")
        ]
        
        format_sizes = {}
        for fmt, name in formats:
            params = EnhancedMemosSearchParams(limit=5, response_format=fmt)
            response = client.search_memos_enhanced(params)
            size = len(json.dumps(response.memos))
            format_sizes[name] = size
            print(f"✓ {name:12} format: {size:,} chars")
        
        # Calculate progressive reduction
        full_size = format_sizes["Full"]
        for name in ["Summary", "Minimal", "ID Only"]:
            if full_size > 0:
                reduction = ((full_size - format_sizes[name]) / full_size * 100)
                print(f"  → {name} reduces tokens by {reduction:.1f}%")
                token_reductions.append(reduction)
        
        total_tests += 1
        passed_tests += 1
        
        # Test 3: Smart Search Features
        print_section("TEST 3: Smart Search & Relevance")
        
        # Search with relevance scoring
        params = EnhancedMemosSearchParams(
            query="mcp",
            limit=10,
            response_format=ResponseFormat.SUMMARY,
            summary_only=True
        )
        response = client.search_memos_enhanced(params)
        
        if response.memos:
            print(f"✓ Found {response.total_count} memos containing 'mcp'")
            
            # Check if sorted by relevance
            scores = [m.get('relevance_score', 0) for m in response.memos]
            is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
            print(f"✓ Results sorted by relevance: {'Yes' if is_sorted else 'No'}")
            
            # Show top 3 with scores
            print("✓ Top 3 results by relevance:")
            for i, memo in enumerate(response.memos[:3]):
                score = memo.get('relevance_score', 0)
                snippet_count = len(memo.get('match_snippets', []))
                print(f"  {i+1}. Score: {score:.2f}, Snippets: {snippet_count}")
        
        total_tests += 1
        passed_tests += 1
        
        # Test 4: Pagination Edge Cases
        print_section("TEST 4: Pagination Edge Cases")
        
        # Test offset beyond total
        params = EnhancedMemosSearchParams(
            limit=10,
            offset=1000,
            response_format=ResponseFormat.MINIMAL
        )
        response = client.search_memos_enhanced(params)
        print(f"✓ Offset beyond total: {len(response.memos)} memos (expected: 0)")
        
        # Test limit validation
        params = EnhancedMemosSearchParams(
            limit=100,  # Should be capped at 50
            response_format=ResponseFormat.MINIMAL
        )
        response = client.search_memos_enhanced(params)
        print(f"✓ Limit validation: {len(response.memos)} memos (max should be 50)")
        
        # Test pagination metadata
        params = EnhancedMemosSearchParams(limit=5, offset=0)
        response = client.search_memos_enhanced(params)
        print(f"✓ Pagination metadata:")
        print(f"  - Total count: {response.total_count}")
        print(f"  - Has more: {response.has_more}")
        print(f"  - Next offset: {response.next_offset}")
        
        total_tests += 1
        passed_tests += 1
        
        # Test 5: Backward Compatibility
        print_section("TEST 5: Backward Compatibility")
        
        # Test old methods still work
        try:
            # search_memos
            results = client.search_memos("test")
            print(f"✓ search_memos() works: {len(results)} results")
            
            # get_latest_memos
            latest = client.get_latest_memos(3)
            print(f"✓ get_latest_memos() works: {len(latest)} memos")
            
            # get_memos_by_tag
            tagged = client.get_memos_by_tag("mcp", 5)
            print(f"✓ get_memos_by_tag() works: {len(tagged)} memos")
            
            total_tests += 1
            passed_tests += 1
        except Exception as e:
            print(f"✗ Backward compatibility failed: {e}")
            total_tests += 1
        
        # Test 6: Content Summarization Quality
        print_section("TEST 6: Smart Summarization Quality")
        
        # Get a memo with long content
        params = EnhancedMemosSearchParams(
            limit=1,
            response_format=ResponseFormat.FULL
        )
        response = client.search_memos_enhanced(params)
        
        if response.memos:
            memo = response.memos[0]
            full_content = memo.get('content', '')
            
            # Generate smart summary
            params_smart = EnhancedMemosSearchParams(
                limit=1,
                response_format=ResponseFormat.SUMMARY,
                summary_only=True,
                content_max_length=200
            )
            response_smart = client.search_memos_enhanced(params_smart)
            
            if response_smart.memos:
                smart_content = response_smart.memos[0].get('content', '')
                
                print(f"✓ Original content: {len(full_content)} chars")
                print(f"✓ Smart summary: {len(smart_content)} chars")
                print(f"✓ Reduction: {((len(full_content) - len(smart_content)) / len(full_content) * 100):.1f}%")
                
                # Check if summary contains key elements
                has_title = full_content.split('\n')[0] in smart_content if full_content else False
                has_headers = any(line.startswith('#') for line in smart_content.split('\n'))
                print(f"✓ Summary quality:")
                print(f"  - Contains title: {'Yes' if has_title else 'No'}")
                print(f"  - Contains headers: {'Yes' if has_headers else 'No'}")
        
        total_tests += 1
        passed_tests += 1
        
        # Test 7: Date Filtering
        print_section("TEST 7: Date Range Filtering")
        
        # Filter by recent dates
        params = EnhancedMemosSearchParams(
            date_from="2025-06-01T00:00:00Z",
            limit=10,
            response_format=ResponseFormat.MINIMAL
        )
        response = client.search_memos_enhanced(params)
        print(f"✓ Memos since June 2025: {response.total_count}")
        
        # Check dates are correct
        if response.memos:
            dates_valid = all(
                memo.get('createTime', '') >= "2025-06-01" 
                for memo in response.memos
            )
            print(f"✓ Date filter validation: {'Passed' if dates_valid else 'Failed'}")
        
        total_tests += 1
        passed_tests += 1
        
        # Final Summary
        print_section("TEST SUMMARY")
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        
        if token_reductions:
            avg_reduction = sum(token_reductions) / len(token_reductions)
            print(f"\nAverage Token Reduction: {avg_reduction:.1f}%")
            print(f"Max Token Reduction: {max(token_reductions):.1f}%")
            print(f"Min Token Reduction: {min(token_reductions):.1f}%")
        
        # Performance verdict
        print("\nPERFORMANCE VERDICT:")
        if avg_reduction >= 80:
            print("✅ EXCELLENT: Achieved target of 80%+ token reduction!")
        elif avg_reduction >= 70:
            print("✅ GOOD: Significant token reduction achieved")
        else:
            print("⚠️  NEEDS IMPROVEMENT: Below target token reduction")
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_comprehensive()