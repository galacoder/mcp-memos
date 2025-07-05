#!/bin/bash
# Memos MCP Wrapper for Claude Desktop
# This wrapper ensures the correct Python with dependencies is used

# Change to the mcp-server-memos directory
cd /Users/sangle/Dev/action/projects/mcp-servers/tools/memos

# Force set environment variables
export MEMOS_URL="https://memos.galatek.dev"
export MEMOS_ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJuYW1lIjoiIiwiaXNzIjoibWVtb3MiLCJzdWIiOiIxIiwiYXVkIjpbInVzZXIuYWNjZXNzLXRva2VuIl0sImV4cCI6NDkwMzIwNzc3OSwiaWF0IjoxNzQ5NjA3Nzk5fQ.R2owAia5reyIaYKpzATcOaUJ-cM08z5jJlSha9MA7zs"
export MEMOS_API_KEY="$MEMOS_ACCESS_TOKEN"
export DEFAULT_TAG="#MCP"

# Use the full path to pyenv Python which has the dependencies
exec /Users/sangle/.pyenv/shims/python3 main.py "$@"