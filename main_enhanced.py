from typing import Any, List, Dict, Optional
import os
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import (
    ErrorData,
    INTERNAL_ERROR,
)
from enhanced_memos import EnhancedMemos, EnhancedMemosSearchParams, ResponseFormat, MemosException

# Initialize FastMCP server
mcp = FastMCP("memos")

# Constants
MEMOS_URL = os.getenv("MEMOS_URL")
MEMOS_API_KEY = os.getenv("MEMOS_ACCESS_TOKEN") or os.getenv("MEMOS_API_KEY")
DEFAULT_TAG = os.getenv("DEFAULT_TAG", "#MCP")  # Default to #MCP if not set

# Validate environment variables
if not MEMOS_URL:
    raise ValueError("MEMOS_URL environment variable is required")
if not MEMOS_API_KEY:
    raise ValueError("MEMOS_ACCESS_TOKEN or MEMOS_API_KEY environment variable is required")

# Initialize Enhanced Memos client
memos_client = EnhancedMemos(MEMOS_URL, MEMOS_API_KEY)


@mcp.tool()
def search_memos_enhanced(
    query: str = "",
    limit: int = 10,
    offset: int = 0,
    response_format: str = "summary",
    content_max_length: int = 500,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tags_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Enhanced search memos with pagination and smart summarization.
    
    Args:
        query: Search query string (optional)
        limit: Number of results to return (default: 10, max: 50)
        offset: Number of results to skip (default: 0)
        response_format: Format for responses - 'id_only', 'minimal', 'summary', 'full' (default: 'summary')
        content_max_length: Maximum content length for summaries (default: 500)
        date_from: Filter memos created after this date (ISO format)
        date_to: Filter memos created before this date (ISO format)
        tags_filter: List of tags to filter by
        
    Returns:
        A dictionary containing:
        - memos: List of formatted memo objects
        - total_count: Total number of matching memos
        - has_more: Whether more results are available
        - next_offset: Offset for next page (-1 if no more)
        - query_metadata: Information about the query
    """
    try:
        # Convert string format to enum
        format_map = {
            "id_only": ResponseFormat.ID_ONLY,
            "minimal": ResponseFormat.MINIMAL,
            "summary": ResponseFormat.SUMMARY,
            "full": ResponseFormat.FULL
        }
        format_enum = format_map.get(response_format.lower(), ResponseFormat.SUMMARY)
        
        # Create enhanced parameters
        params = EnhancedMemosSearchParams(
            query=query,
            limit=min(limit, 50),  # Cap at 50
            offset=offset,
            response_format=format_enum,
            content_max_length=content_max_length,
            date_from=date_from,
            date_to=date_to,
            tags_filter=tags_filter or [],
            summary_only=format_enum == ResponseFormat.SUMMARY
        )
        
        # Execute enhanced search
        response = memos_client.search_memos_enhanced(params)
        
        # Return structured response
        return {
            "memos": response.memos,
            "total_count": response.total_count,
            "has_more": response.has_more,
            "next_offset": response.next_offset,
            "query_metadata": response.query_metadata
        }
        
    except MemosException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


# Keep backward compatible search_memos
@mcp.tool()
def search_memos(query: str) -> List[Dict[str, Any]]:
    """
    Search memos using the Memos API (backward compatible).
    
    Args:
        query: Search query string
        
    Returns:
        A list of memo objects matching the query
    """
    try:
        # Use enhanced search with backward compatible settings
        params = EnhancedMemosSearchParams(
            query=query,
            limit=20,
            response_format=ResponseFormat.FULL
        )
        response = memos_client.search_memos_enhanced(params)
        return response.memos
    except MemosException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


@mcp.tool()
def get_latest_memos(limit: int = 3, response_format: str = "summary") -> List[Dict[str, Any]]:
    """
    Get the latest memos with enhanced formatting options.
    
    Args:
        limit: Number of latest memos to retrieve (default: 3, max: 20)
        response_format: Format for responses - 'minimal', 'summary', 'full' (default: 'summary')
        
    Returns:
        A list of the latest memo objects
    """
    if limit > 20:
        limit = 20
    
    try:
        # Use enhanced search for latest memos
        format_map = {
            "minimal": ResponseFormat.MINIMAL,
            "summary": ResponseFormat.SUMMARY,
            "full": ResponseFormat.FULL
        }
        format_enum = format_map.get(response_format.lower(), ResponseFormat.SUMMARY)
        
        params = EnhancedMemosSearchParams(
            query="",
            limit=limit,
            response_format=format_enum,
            content_max_length=300  # Shorter for latest memos
        )
        response = memos_client.search_memos_enhanced(params)
        return response.memos
    except MemosException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


@mcp.tool()
def get_memos_by_tag(tag: str, limit: int = 10, response_format: str = "summary") -> List[Dict[str, Any]]:
    """
    Get memos that contain a specific tag with enhanced formatting.
    
    Args:
        tag: The tag to search for (with or without #)
        limit: Maximum number of memos to return (default: 10, max: 20)
        response_format: Format for responses - 'minimal', 'summary', 'full' (default: 'summary')
        
    Returns:
        A list of memo objects containing the tag
    """
    if limit > 20:
        limit = 20
    
    try:
        # Normalize tag
        if not tag.startswith("#"):
            tag = f"#{tag}"
            
        format_map = {
            "minimal": ResponseFormat.MINIMAL,
            "summary": ResponseFormat.SUMMARY,
            "full": ResponseFormat.FULL
        }
        format_enum = format_map.get(response_format.lower(), ResponseFormat.SUMMARY)
        
        params = EnhancedMemosSearchParams(
            query="",
            limit=limit,
            tags_filter=[tag.replace("#", "")],
            response_format=format_enum,
            content_max_length=400
        )
        response = memos_client.search_memos_enhanced(params)
        return response.memos
    except MemosException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


# Keep all other methods unchanged for backward compatibility
@mcp.tool()
def get_memo_by_id(memo_id: str) -> Dict[str, Any]:
    """
    Get a specific memo by its ID.
    
    Args:
        memo_id: The memo ID (can be full name like 'memos/XXX' or just 'XXX')
        
    Returns:
        The memo object with full details
    """
    try:
        return memos_client.get_memo_by_id(memo_id)
    except MemosException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


@mcp.tool()
def update_memo(memo_id: str, content: str, tags: List[str] = []) -> Dict[str, Any]:
    """
    Update an existing memo.
    
    Args:
        memo_id: The memo ID (can be full name like 'memos/XXX' or just 'XXX')
        content: New content for the memo
        tags: List of tags for the memo
        
    Returns:
        The updated memo object
    """
    try:
        return memos_client.update_memo(memo_id, content, tags)
    except MemosException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


@mcp.tool()
def delete_memo(memo_id: str) -> Dict[str, Any]:
    """
    Delete a memo by its ID.
    
    Args:
        memo_id: The memo ID (can be full name like 'memos/XXX' or just 'XXX')
        
    Returns:
        A success message
    """
    try:
        return memos_client.delete_memo(memo_id)
    except MemosException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


@mcp.tool()
def create_memo(content: str, tags: List[str] = []) -> Dict[str, Any]:
    """
    Create a new memo with the Memos API.
    
    Args:
        content: Content of the memo
        tags: List of tags for the memo (will always include the default tag)
        
    Returns:
        The created memo object
    """
    # Make sure default tag is included
    tags_with_default = list(tags)
    if DEFAULT_TAG not in tags_with_default:
        tags_with_default.append(DEFAULT_TAG)
    
    try:
        return memos_client.create_memo(content, tags_with_default)
    except MemosException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


def main():
    # Initialize and run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()