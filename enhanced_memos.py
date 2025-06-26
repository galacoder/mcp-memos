import requests
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class MemosException(Exception):
    """Custom exception for Memos API errors"""
    pass


class ResponseFormat(Enum):
    """Response format options for memo content"""
    FULL = "full"
    SUMMARY = "summary"
    MINIMAL = "minimal"
    ID_ONLY = "id_only"


@dataclass
class EnhancedMemosSearchParams:
    """Enhanced search parameters with pagination and filtering"""
    query: str = ""
    limit: int = 10
    offset: int = 0
    fields: List[str] = field(default_factory=lambda: ['id', 'content', 'tags', 'createTime'])
    summary_only: bool = False
    content_max_length: int = 500
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    tags_filter: List[str] = field(default_factory=list)
    response_format: ResponseFormat = ResponseFormat.SUMMARY
    group_by_tag: bool = False
    
    def __post_init__(self):
        """Validate parameters after initialization"""
        if self.limit > 50:
            self.limit = 50  # Max limit to prevent token overflow
        if self.limit < 1:
            self.limit = 1
        if self.offset < 0:
            self.offset = 0
        if self.content_max_length < 50:
            self.content_max_length = 50
        if self.content_max_length > 2000:
            self.content_max_length = 2000


@dataclass
class SearchResponse:
    """Response structure with pagination metadata"""
    memos: List[Dict[str, Any]]
    total_count: int
    has_more: bool
    next_offset: int
    query_metadata: Dict[str, Any]


class EnhancedMemos:
    def __init__(self, memos_url, memos_api_key):
        """
        Initialize an Enhanced Memos client with pagination support.
        
        Args:
            memos_url: The URL of the Memos API
            memos_api_key: API key for authentication
        """
        self.memos_url = memos_url
        self.memos_api_key = memos_api_key
        self.headers = {
            "Authorization": f"Bearer {self.memos_api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    
    def get_user_id(self) -> str:
        """
        Get the user ID of the authenticated user by checking auth status.
        
        Returns:
            str: The user ID of the authenticated user
            
        Raises:
            MemosException: If there is an error retrieving the user ID
        """
        try:
            response = requests.get(
                f"{self.memos_url}/api/v1/auth/status", headers=self.headers
            )
            response.raise_for_status()
            
            user_data = response.json()
            user_id = user_data.get("name")
            
            if not user_id:
                raise MemosException("Could not retrieve user ID from auth status")
            
            return user_id
        except requests.RequestException as e:
            raise MemosException(f"Error getting user ID: {e}")
    
    def _apply_response_format(self, memo: Dict[str, Any], params: EnhancedMemosSearchParams, query: str = "") -> Dict[str, Any]:
        """
        Apply response format to a memo based on parameters.
        
        Args:
            memo: The raw memo data
            params: Search parameters including response format
            query: Search query for smart summarization
            
        Returns:
            Formatted memo data
        """
        # Always include memo ID
        memo_id = memo.get("name", "")
        
        if params.response_format == ResponseFormat.ID_ONLY:
            return {"id": memo_id}
        
        # Extract basic fields
        formatted = {
            "id": memo_id,
            "createTime": memo.get("createTime", ""),
            "updateTime": memo.get("updateTime", ""),
        }
        
        # Add content based on format
        content = memo.get("content", "")
        
        if params.response_format == ResponseFormat.MINIMAL:
            # Minimal: just first line of content and tags
            first_line = content.split('\n')[0][:100] if content else ""
            formatted["snippet"] = first_line
            formatted["tags"] = memo.get("tags", [])
            
        elif params.response_format == ResponseFormat.SUMMARY:
            # Summary: smart summary with highlighted matches
            if params.summary_only or query:
                # Use smart summarization
                formatted["content"] = self._generate_smart_summary(memo, query, params.content_max_length)
                
                # Add match snippets if searching
                if query:
                    snippets = self._extract_snippet_around_match(content, query, context_chars=50)
                    if snippets:
                        formatted["match_snippets"] = snippets[:3]  # Top 3 matches
                    
                    # Add relevance score
                    formatted["relevance_score"] = self._calculate_relevance_score(
                        content, query, memo.get("tags", [])
                    )
            else:
                # Regular truncation
                truncated_content = content[:params.content_max_length]
                if len(content) > params.content_max_length:
                    truncated_content += "..."
                formatted["content"] = truncated_content
            
            formatted["tags"] = memo.get("tags", [])
            formatted["snippet"] = memo.get("snippet", "")
            
        else:  # FULL format
            # Include all fields requested
            for field in params.fields:
                if field in memo:
                    formatted[field] = memo[field]
        
        # Remove verbose node structures unless specifically requested
        if "nodes" in formatted and params.response_format != ResponseFormat.FULL:
            del formatted["nodes"]
        
        return formatted
    
    def _paginate_results(self, all_items: List[Dict[str, Any]], params: EnhancedMemosSearchParams) -> Tuple[List[Dict[str, Any]], bool, int]:
        """
        Apply pagination to results.
        
        Args:
            all_items: All items before pagination
            params: Search parameters including limit and offset
            
        Returns:
            Tuple of (paginated items, has_more, total_count)
        """
        total_count = len(all_items)
        
        # Apply offset and limit
        start_idx = params.offset
        end_idx = start_idx + params.limit
        
        paginated_items = all_items[start_idx:end_idx]
        has_more = end_idx < total_count
        
        return paginated_items, has_more, total_count
    
    def search_memos_enhanced(self, params: EnhancedMemosSearchParams) -> SearchResponse:
        """
        Enhanced search memos with pagination and response formatting.
        
        Args:
            params: Enhanced search parameters
            
        Returns:
            SearchResponse with paginated and formatted results
            
        Raises:
            MemosException: If there is an error searching memos
        """
        try:
            # Fetch all memos first (we'll optimize this later with API pagination)
            response = requests.get(
                f"{self.memos_url}/api/v1/memos",
                headers=self.headers,
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                all_memos = response.json().get("memos", [])
                
                # Apply search filter if query provided
                if params.query:
                    filtered_memos = [
                        memo for memo in all_memos 
                        if params.query.lower() in memo.get("content", "").lower()
                    ]
                else:
                    filtered_memos = all_memos
                
                # Apply tag filter if specified
                if params.tags_filter:
                    filtered_memos = [
                        memo for memo in filtered_memos
                        if any(tag in memo.get("tags", []) for tag in params.tags_filter)
                    ]
                
                # Apply date filters if specified
                if params.date_from or params.date_to:
                    filtered_memos = self._apply_date_filter(filtered_memos, params.date_from, params.date_to)
                
                # Sort by creation time (newest first)
                filtered_memos.sort(key=lambda x: x.get("createTime", ""), reverse=True)
                
                # Apply pagination
                paginated_memos, has_more, total_count = self._paginate_results(filtered_memos, params)
                
                # Apply response format to each memo
                formatted_memos = [
                    self._apply_response_format(memo, params, params.query) 
                    for memo in paginated_memos
                ]
                
                # Sort by relevance if searching
                if params.query and any('relevance_score' in memo for memo in formatted_memos):
                    formatted_memos.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                
                # Calculate next offset
                next_offset = params.offset + params.limit if has_more else -1
                
                return SearchResponse(
                    memos=formatted_memos,
                    total_count=total_count,
                    has_more=has_more,
                    next_offset=next_offset,
                    query_metadata={
                        "query": params.query,
                        "limit": params.limit,
                        "offset": params.offset,
                        "format": params.response_format.value,
                        "filtered_count": total_count,
                        "returned_count": len(formatted_memos)
                    }
                )
            else:
                raise MemosException(f"Error searching memos: {response.status_code}")
        except requests.RequestException as e:
            raise MemosException(f"Error searching memos: {e}")
    
    def _apply_date_filter(self, memos: List[Dict[str, Any]], date_from: Optional[str], date_to: Optional[str]) -> List[Dict[str, Any]]:
        """Apply date range filtering to memos."""
        filtered = memos
        
        if date_from:
            filtered = [
                memo for memo in filtered
                if memo.get("createTime", "") >= date_from
            ]
        
        if date_to:
            filtered = [
                memo for memo in filtered
                if memo.get("createTime", "") <= date_to
            ]
        
        return filtered
    
    def _extract_snippet_around_match(self, content: str, query: str, context_chars: int = 50) -> List[str]:
        """
        Extract snippets around matched keywords.
        
        Args:
            content: Full content to search
            query: Search query
            context_chars: Number of characters to include before/after match
            
        Returns:
            List of snippets with context around matches
        """
        if not query or not content:
            return []
        
        snippets = []
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Find all occurrences of the query
        start = 0
        while True:
            pos = content_lower.find(query_lower, start)
            if pos == -1:
                break
            
            # Extract snippet with context
            snippet_start = max(0, pos - context_chars)
            snippet_end = min(len(content), pos + len(query) + context_chars)
            
            # Extend to word boundaries
            while snippet_start > 0 and content[snippet_start - 1].isalnum():
                snippet_start -= 1
            while snippet_end < len(content) and content[snippet_end].isalnum():
                snippet_end += 1
            
            snippet = content[snippet_start:snippet_end]
            
            # Add ellipsis if needed
            if snippet_start > 0:
                snippet = "..." + snippet
            if snippet_end < len(content):
                snippet = snippet + "..."
            
            # Highlight the match (using markdown bold)
            highlighted = snippet.replace(
                content[pos:pos + len(query)],
                f"**{content[pos:pos + len(query)]}**"
            )
            
            snippets.append(highlighted)
            start = pos + 1
        
        return snippets
    
    def _calculate_relevance_score(self, content: str, query: str, tags: List[str] = None) -> float:
        """
        Calculate relevance score based on match frequency and position.
        
        Args:
            content: Memo content
            query: Search query
            tags: Memo tags
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not query:
            return 0.5  # Default score for no query
        
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Count occurrences
        match_count = content_lower.count(query_lower)
        
        # Bonus for title matches (first line)
        first_line = content.split('\n')[0] if content else ""
        title_bonus = 2.0 if query_lower in first_line.lower() else 0.0
        
        # Bonus for tag matches
        tag_bonus = 1.0 if tags and any(query_lower in tag.lower() for tag in tags) else 0.0
        
        # Calculate position score (earlier matches are better)
        first_match = content_lower.find(query_lower)
        position_score = 1.0 - (first_match / len(content)) if first_match != -1 else 0.0
        
        # Combine scores
        raw_score = match_count + title_bonus + tag_bonus + position_score
        
        # Normalize to 0-1 range
        return min(1.0, raw_score / 10.0)
    
    def _generate_smart_summary(self, memo: Dict[str, Any], query: str = "", max_length: int = 500) -> str:
        """
        Generate intelligent summary of memo content.
        
        Args:
            memo: The memo object
            query: Search query (if any)
            max_length: Maximum summary length
            
        Returns:
            Smart summary of the memo
        """
        content = memo.get("content", "")
        
        if not content:
            return ""
        
        # If there's a query, prioritize snippets around matches
        if query:
            snippets = self._extract_snippet_around_match(content, query)
            if snippets:
                # Join top snippets
                summary = " [...] ".join(snippets[:3])
                if len(summary) > max_length:
                    summary = summary[:max_length] + "..."
                return summary
        
        # Otherwise, create a general summary
        lines = content.split('\n')
        summary_parts = []
        
        # Always include the title/first line
        if lines:
            summary_parts.append(lines[0])
        
        # Include important sections (headers, lists)
        remaining_length = max_length - len(summary_parts[0]) if summary_parts else max_length
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            # Prioritize headers and list items
            if line.startswith('#') or line.startswith('-') or line.startswith('*') or line.startswith('1.'):
                if len(' '.join(summary_parts)) + len(line) < remaining_length:
                    summary_parts.append(line)
        
        # If still under limit, add regular content
        if len(' '.join(summary_parts)) < max_length * 0.7:
            for line in lines[1:]:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    if len(' '.join(summary_parts)) + len(line) < remaining_length:
                        summary_parts.append(line)
        
        summary = '\n'.join(summary_parts)
        
        # Truncate if needed
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(' ', 1)[0] + "..."
        
        return summary
    
    # Backward compatible method that uses enhanced version internally
    def search_memos(self, query: str) -> List[Dict[str, Any]]:
        """
        Backward compatible search method.
        
        Args:
            query: Search query string
            
        Returns:
            A list of memo objects matching the query
        """
        params = EnhancedMemosSearchParams(
            query=query,
            limit=20,  # Default backward compatible limit
            response_format=ResponseFormat.FULL  # Full format for backward compatibility
        )
        response = self.search_memos_enhanced(params)
        return response.memos
    
    def get_latest_memos(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get the latest memos with pagination support.
        
        Args:
            limit: Number of latest memos to retrieve (default: 3)
            
        Returns:
            A list of the latest memo objects
        """
        params = EnhancedMemosSearchParams(
            query="",
            limit=limit,
            response_format=ResponseFormat.SUMMARY
        )
        response = self.search_memos_enhanced(params)
        return response.memos
    
    def get_memos_by_tag(self, tag: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memos that contain a specific tag with enhanced filtering.
        
        Args:
            tag: The tag to search for (with or without #)
            limit: Maximum number of memos to return (default: 10)
            
        Returns:
            A list of memo objects containing the tag
        """
        # Normalize the tag - add # if not present
        if not tag.startswith("#"):
            tag = f"#{tag}"
        
        params = EnhancedMemosSearchParams(
            query="",
            limit=limit,
            tags_filter=[tag.replace("#", "")],  # API uses tags without #
            response_format=ResponseFormat.SUMMARY
        )
        response = self.search_memos_enhanced(params)
        return response.memos
    
    # Keep all other methods unchanged for backward compatibility
    def create_memo(self, content: str, tags: List[str] = None) -> Dict[str, Any]:
        """
        Create a new memo using the Memos API.
        
        Args:
            content: Content of the memo
            tags: List of tags for the memo
            
        Returns:
            The created memo object
            
        Raises:
            MemosException: If there is an error creating the memo
        """
        # Format content to include tags
        formatted_content = content
        if tags:
            # Append tags to the end of content
            formatted_content += "\n\n" + " ".join(tags)
        
        # Prepare payload
        payload = {
            "content": formatted_content,
            "visibility": "PRIVATE",  # Default to private memos
        }
        
        try:
            response = requests.post(
                f"{self.memos_url}/api/v1/memos", headers=self.headers, json=payload
            )
            response.raise_for_status()
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                raise MemosException(f"Error creating memo: {response.status_code}")
        except requests.RequestException as e:
            raise MemosException(f"Error creating memo: {e}")
    
    def get_memo_by_id(self, memo_id: str) -> Dict[str, Any]:
        """
        Get a specific memo by its ID.
        
        Args:
            memo_id: The memo ID (can be full name like 'memos/XXX' or just 'XXX')
            
        Returns:
            The memo object
            
        Raises:
            MemosException: If there is an error retrieving the memo
        """
        # Handle both full name format and short ID format
        if memo_id.startswith("memos/"):
            memo_name = memo_id.split("/")[1]
        else:
            memo_name = memo_id
        
        try:
            response = requests.get(
                f"{self.memos_url}/api/v1/memos/{memo_name}",
                headers=self.headers,
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.json()
            else:
                raise MemosException(f"Error getting memo: {response.status_code}")
        except requests.RequestException as e:
            raise MemosException(f"Error getting memo: {e}")
    
    def update_memo(self, memo_id: str, content: str, tags: List[str] = []) -> Dict[str, Any]:
        """
        Update an existing memo.
        
        Args:
            memo_id: The memo ID (can be full name like 'memos/XXX' or just 'XXX')
            content: New content for the memo
            tags: List of tags for the memo
            
        Returns:
            The updated memo object
            
        Raises:
            MemosException: If there is an error updating the memo
        """
        # Handle both full name format and short ID format
        if memo_id.startswith("memos/"):
            memo_name = memo_id.split("/")[1]
        else:
            memo_name = memo_id
        
        # Format content to include tags
        formatted_content = content
        if tags:
            # Append tags to the end of content
            formatted_content += "\n\n" + " ".join(tags)
        
        # Prepare payload
        payload = {
            "content": formatted_content,
        }
        
        try:
            response = requests.patch(
                f"{self.memos_url}/api/v1/memos/{memo_name}",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.json()
            else:
                raise MemosException(f"Error updating memo: {response.status_code}")
        except requests.RequestException as e:
            raise MemosException(f"Error updating memo: {e}")
    
    def delete_memo(self, memo_id: str) -> Dict[str, Any]:
        """
        Delete a memo by its ID.
        
        Args:
            memo_id: The memo ID (can be full name like 'memos/XXX' or just 'XXX')
            
        Returns:
            A success message
            
        Raises:
            MemosException: If there is an error deleting the memo
        """
        # Handle both full name format and short ID format
        if memo_id.startswith("memos/"):
            memo_name = memo_id.split("/")[1]
        else:
            memo_name = memo_id
        
        try:
            response = requests.delete(
                f"{self.memos_url}/api/v1/memos/{memo_name}",
                headers=self.headers,
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                return {"message": f"Memo {memo_id} deleted successfully"}
            else:
                raise MemosException(f"Error deleting memo: {response.status_code}")
        except requests.RequestException as e:
            raise MemosException(f"Error deleting memo: {e}")