from typing import Any, List, Dict
import os
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import (
    ErrorData,
    INTERNAL_ERROR,
)
from memos import Memos, MemosException

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

# Initialize Memos client
memos_client = Memos(MEMOS_URL, MEMOS_API_KEY)


@mcp.tool()
def search_memos(query: str) -> List[Dict[str, Any]]:
    """
    Search memos using the Memos API.

    Args:
        query: Search query string

    Returns:
        A list of memo objects matching the query
    """
    try:
        return memos_client.search_memos(query)
    except MemosException as e:
        # Map the Memos exception to an MCP error
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


@mcp.tool()
def get_latest_memos(limit: int = 3) -> List[Dict[str, Any]]:
    """
    Get the latest memos using pagination.

    Args:
        limit: Number of latest memos to retrieve (default: 3, max: 20)

    Returns:
        A list of the latest memo objects
    """
    # Limit the maximum to prevent large responses
    if limit > 20:
        limit = 20
    
    try:
        return memos_client.get_latest_memos(limit)
    except MemosException as e:
        # Map the Memos exception to an MCP error
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


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
        # Map the Memos exception to an MCP error
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
        # Map the Memos exception to an MCP error
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
        # Map the Memos exception to an MCP error
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


@mcp.tool()
def get_memos_by_tag(tag: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get memos that contain a specific tag.

    Args:
        tag: The tag to search for (with or without #)
        limit: Maximum number of memos to return (default: 10, max: 20)

    Returns:
        A list of memo objects containing the tag
    """
    # Limit the maximum to prevent large responses
    if limit > 20:
        limit = 20
    
    try:
        return memos_client.get_memos_by_tag(tag, limit)
    except MemosException as e:
        # Map the Memos exception to an MCP error
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
        # Map the Memos exception to an MCP error
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))


def main():
    # Initialize and run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
