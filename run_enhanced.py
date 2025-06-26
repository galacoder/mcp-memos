#!/usr/bin/env python3
"""Wrapper script to run the enhanced Memos MCP server"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the enhanced main
from main import main

if __name__ == "__main__":
    main()