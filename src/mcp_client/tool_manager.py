"""MCP Tools Management - handles tool-related operations"""

from typing import List, Dict, Any
from .mcp_session import MCPSession


class ToolManager:
    """Manages MCP tool operations"""
    
    def __init__(self, session: MCPSession):
        self.session = session
    
    async def list_tools(self):
        """List all available tools"""
        return await self.session.list_tools()
    
    async def get_tools_for_openai(self) -> List[Dict[str, Any]]:
        """Format tools for OpenAI API calls"""
        tools = await self.list_tools()
        return [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in tools]
    
    async def call_tool(self, name: str, arguments: dict):
        """Execute a tool call"""
        return await self.session.call_tool(name, arguments)
    
    def format_tool_result(self, tool_name: str, arguments: dict, result) -> str:
        """Format tool execution result for display"""
        return f"[Calling tool {tool_name} with args {arguments}]"
