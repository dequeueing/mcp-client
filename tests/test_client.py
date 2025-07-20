"""Test script for the refactored MCP client"""

import asyncio
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_client import MCPSession, ToolManager, ResourceManager, PromptManager, LLMClient, ChatProcessor


class MCPClient:
    """Simple test client"""
    def __init__(self):
        self.session = MCPSession()
        self.llm_client = LLMClient()
        self.tool_manager = None
        self.resource_manager = None
        self.prompt_manager = None
        self.chat_processor = None
        
    async def connect_to_server(self, server_script_path: str):
        await self.session.connect(server_script_path)
        self.tool_manager = ToolManager(self.session)
        self.resource_manager = ResourceManager(self.session)
        self.prompt_manager = PromptManager(self.session)
        self.chat_processor = ChatProcessor(self.llm_client, self.tool_manager)
    
    async def _handle_list_resources(self):
        resources = await self.resource_manager.list_resources()
        output = self.resource_manager.format_resources_list(resources)
        print("\\n" + output)
        
    async def _handle_list_prompts(self):
        prompts = await self.prompt_manager.list_prompts()
        output = self.prompt_manager.format_prompts_list(prompts)
        print("\\n" + output)
        
    async def cleanup(self):
        await self.session.cleanup()


async def test_refactored_client():
    """Test the refactored client with the weather server"""
    client = MCPClient()
    
    try:
        # Connect to weather server
        server_path = os.path.join(os.path.dirname(__file__), '..', 'servers', 'weather', 'weather.py')
        await client.connect_to_server(server_path)
        
        # Test a simple query
        print("\\n" + "="*50)
        print("Testing weather query...")
        response = await client.process_query("What's the weather forecast for New York?")
        print("Response:", response)
        
        # Test resources
        print("\\n" + "="*50)
        print("Testing resource listing...")
        await client._handle_list_resources()
        
        # Test prompts
        print("\\n" + "="*50)
        print("Testing prompt listing...")
        await client._handle_list_prompts()
        
        print("\\n" + "="*50)
        print("Refactored client test completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(test_refactored_client())
