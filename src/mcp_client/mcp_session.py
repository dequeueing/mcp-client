"""MCP Session Management - handles connection and basic MCP operations"""

import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPSession:
    """Manages MCP server connection and basic operations"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None
    
    async def connect(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()
        
        # Print connection summary
        await self._print_connection_info()
    
    async def _print_connection_info(self):
        """Print information about available MCP capabilities"""
        # Tools
        tools_response = await self.session.list_tools()
        tools = tools_response.tools
        
        # Resources  
        try:
            resources_response = await self.session.list_resources()
            resources = resources_response.resources
        except Exception:
            resources = []
        
        # Prompts
        try:
            prompts_response = await self.session.list_prompts()
            prompts = prompts_response.prompts
        except Exception:
            prompts = []
        
        print(f"\nConnected to server with {len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts")
        
        # Print detailed info for each capability
        if tools:
            print("\nTools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
        
        if resources:
            print("\nResources:")
            for resource in resources:
                print(f"  - {resource.name} ({resource.uri})")
                if resource.description:
                    print(f"    {resource.description}")
        
        if prompts:
            print("\nPrompts:")
            for prompt in prompts:
                print(f"  - {prompt.name}")
                if prompt.description:
                    print(f"    {prompt.description}")
    
    async def list_tools(self):
        """List available tools"""
        response = await self.session.list_tools()
        return response.tools
    
    async def call_tool(self, name: str, arguments: dict):
        """Call a tool with given arguments"""
        return await self.session.call_tool(name, arguments)
    
    async def cleanup(self):
        """Clean up session resources"""
        await self.exit_stack.aclose()
