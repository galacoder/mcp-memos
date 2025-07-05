# Memos MCP Setup Instructions

## Current Status
Memos MCP is already configured in Claude Desktop but needs your credentials.

## Steps to Complete Setup:

### 1. Get Your Memos Credentials

1. **Open your Memos instance** (e.g., https://your-memos.com)
2. **Go to Settings** → **Access Tokens**
3. **Create a new access token**:
   - Give it a descriptive name (e.g., "Claude MCP")
   - Copy the generated token

### 2. Update Claude Desktop Config

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

Replace these placeholders in the "memos" section:
- `YOUR_MEMOS_URL` → Your Memos instance URL (e.g., "https://memos.example.com")
- `YOUR_MEMOS_API_KEY` → Your access token from step 1

Example:
```json
"memos": {
  "command": "python3",
  "args": [
    "/Users/sangle/Dev/action/projects/mcp-servers/tools/memos/main.py"
  ],
  "env": {
    "MEMOS_URL": "https://memos.example.com",
    "MEMOS_API_KEY": "your-actual-token-here",
    "DEFAULT_TAG": "#mcp"
  }
}
```

### 3. Restart Claude Desktop

After updating, restart Claude Desktop for changes to take effect.

## Available Memos Tools

Once configured, you'll have access to:
- `mcp__memos__search_memos` - Search your memos
- `mcp__memos__get_latest_memos` - Get recent memos
- `mcp__memos__get_memo_by_id` - Get specific memo
- `mcp__memos__update_memo` - Update existing memo
- `mcp__memos__delete_memo` - Delete a memo
- `mcp__memos__get_memos_by_tag` - Get memos with specific tag
- `mcp__memos__create_memo` - Create new memo

## Testing

After restart, type `/mcp` in Claude Desktop. You should see all the Memos tools listed above.