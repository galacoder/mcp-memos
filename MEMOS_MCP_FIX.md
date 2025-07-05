# Memos MCP Fix Summary

## Problem
The Memos MCP server worked in Claude Code CLI but not in Claude Desktop due to Python environment differences:

- **Claude Code**: Has full PATH including `/Users/sangle/.pyenv/shims`, so `python3` resolves to pyenv Python with all dependencies
- **Claude Desktop**: Has limited PATH, so `python3` resolves to system Python at `/usr/bin/python3` which lacks MCP dependencies

## Solution
Created a new wrapper script specifically for Claude Desktop (`memos-desktop-wrapper.sh`) that:
1. Uses full path to pyenv Python: `/Users/sangle/.pyenv/shims/python3`
2. Hardcodes all required environment variables
3. Changes to the correct directory before execution

## Configuration
Updated Claude Desktop config to use the new wrapper:
```json
"memos": {
  "command": "/Users/sangle/Dev/action/projects/mcp-servers/tools/memos/memos-desktop-wrapper.sh",
  "args": []
}
```

## Result
Memos MCP now works in both Claude Code and Claude Desktop, using the same Python environment with all required dependencies installed.