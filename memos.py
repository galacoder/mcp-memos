import requests
from typing import List, Dict, Any


class MemosException(Exception):
    """Custom exception for Memos API errors"""

    pass


class Memos:
    def __init__(self, memos_url, memos_api_key):
        """
        Initialize a Memos client.

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
            # Use the auth/status endpoint to get current user info
            response = requests.get(
                f"{self.memos_url}/api/v1/auth/status", headers=self.headers
            )
            response.raise_for_status()

            # Extract the user ID from the response
            user_data = response.json()
            user_id = user_data.get("name")

            if not user_id:
                raise MemosException("Could not retrieve user ID from auth status")

            return user_id
        except requests.RequestException as e:
            raise MemosException(f"Error getting user ID: {e}")

    def search_memos(self, query: str) -> List[Dict[str, Any]]:
        """
        Search memos using the Memos API.

        Args:
            query: Search query string

        Returns:
            A list of memo objects matching the query

        Raises:
            MemosException: If there is an error searching memos
        """
        try:
            # Try the global memos endpoint first
            response = requests.get(
                f"{self.memos_url}/api/v1/memos",
                headers=self.headers,
            )
            response.raise_for_status()

            if response.status_code == 200:
                memos = response.json().get("memos", [])
                # Filter by query if provided
                if query:
                    filtered_memos = [memo for memo in memos if query.lower() in memo.get("content", "").lower()]
                    return filtered_memos
                return memos
            else:
                raise MemosException(f"Error searching memos: {response.status_code}")
        except requests.RequestException as e:
            raise MemosException(f"Error searching memos: {e}")

    def get_latest_memos(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get the latest memos using pagination.

        Args:
            limit: Number of latest memos to retrieve (default: 3)

        Returns:
            A list of the latest memo objects

        Raises:
            MemosException: If there is an error getting memos
        """
        try:
            params = {"pageSize": limit}
            response = requests.get(
                f"{self.memos_url}/api/v1/memos",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()

            if response.status_code == 200:
                return response.json().get("memos", [])
            else:
                raise MemosException(f"Error getting latest memos: {response.status_code}")
        except requests.RequestException as e:
            raise MemosException(f"Error getting latest memos: {e}")

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

    def get_memos_by_tag(self, tag: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memos that contain a specific tag.

        Args:
            tag: The tag to search for (with or without #)
            limit: Maximum number of memos to return (default: 10)

        Returns:
            A list of memo objects containing the tag

        Raises:
            MemosException: If there is an error getting memos
        """
        # Normalize the tag - add # if not present
        if not tag.startswith("#"):
            tag = f"#{tag}"

        try:
            # Get all memos first (with a reasonable limit)
            params = {"pageSize": min(limit * 5, 100)}  # Get more than needed to filter
            response = requests.get(
                f"{self.memos_url}/api/v1/memos",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()

            if response.status_code == 200:
                all_memos = response.json().get("memos", [])
                # Filter memos that contain the tag
                tagged_memos = []
                for memo in all_memos:
                    # Check if tag is in the tags array
                    if tag.lstrip("#") in memo.get("tags", []):
                        tagged_memos.append(memo)
                    # Also check if tag appears in content
                    elif tag in memo.get("content", ""):
                        tagged_memos.append(memo)
                    
                    # Stop if we have enough
                    if len(tagged_memos) >= limit:
                        break
                
                return tagged_memos[:limit]
            else:
                raise MemosException(f"Error getting memos by tag: {response.status_code}")
        except requests.RequestException as e:
            raise MemosException(f"Error getting memos by tag: {e}")

    def create_memo(self, content: str, tags: List[str] = []) -> Dict[str, Any]:
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
