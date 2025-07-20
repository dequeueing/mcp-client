"""MCP Client Package

A modular implementation of an MCP (Model Context Protocol) client with support for:
- Tools: Execute server-provided functions
- Resources: Access server-provided data and context  
- Prompts: Use server-provided prompt templates
- LLM Integration: Communicate with language models via OpenRouter
"""

from .mcp_session import MCPSession
from .tool_manager import ToolManager
from .resource_manager import ResourceManager
from .prompt_manager import PromptManager
from .llm_client import LLMClient
from .chat_processor import ChatProcessor

__version__ = "1.0.0"
__author__ = "MCP Client Team"

__all__ = [
    "MCPSession",
    "ToolManager", 
    "ResourceManager",
    "PromptManager",
    "LLMClient",
    "ChatProcessor"
]
