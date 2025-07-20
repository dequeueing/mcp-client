"""Refactored MCP Client - clean, modular implementation"""

import asyncio
import sys
import os
from typing import Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_client import (
    MCPSession,
    ToolManager,
    ResourceManager, 
    PromptManager,
    LLMClient,
    ChatProcessor
)


class MCPClient:
    """Main MCP Client with modular design"""
    
    def __init__(self, model: str = "anthropic/claude-3-5-sonnet-20241022"):
        # Initialize core components
        self.session = MCPSession()
        self.llm_client = LLMClient(model)
        
        # Initialize managers (will be set after connection)
        self.tool_manager: Optional[ToolManager] = None
        self.resource_manager: Optional[ResourceManager] = None
        self.prompt_manager: Optional[PromptManager] = None
        self.chat_processor: Optional[ChatProcessor] = None
        
        # Settings
        self.auto_include_resources = False
    
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server and initialize managers"""
        await self.session.connect(server_script_path)
        
        # Initialize managers after successful connection
        self.tool_manager = ToolManager(self.session)
        self.resource_manager = ResourceManager(self.session)
        self.prompt_manager = PromptManager(self.session)
        self.chat_processor = ChatProcessor(self.llm_client, self.tool_manager)
    
    async def process_query(self, query: str) -> str:
        """Process a user query"""
        if not self.chat_processor:
            raise RuntimeError("Must connect to server first")
        
        # Optionally enhance query with relevant resource context
        if self.auto_include_resources:
            enhanced_query = await self.resource_manager.add_resource_context(query)
        else:
            enhanced_query = query
        
        return await self.chat_processor.process_query(enhanced_query)
    
    async def use_prompt(self, prompt_name: str) -> str:
        """Use a specific prompt"""
        if not self.prompt_manager or not self.chat_processor:
            raise RuntimeError("Must connect to server first")
        
        # Get prompt definition
        prompts = await self.prompt_manager.list_prompts()
        prompt_def = None
        for p in prompts:
            if p.name == prompt_name:
                prompt_def = p
                break
        
        if not prompt_def:
            return f"Prompt '{prompt_name}' not found."
        
        # Collect arguments
        arguments = self.prompt_manager.collect_prompt_arguments(prompt_def)
        
        # Get the prompt with arguments
        prompt_result = await self.prompt_manager.get_prompt(prompt_name, arguments)
        if not prompt_result:
            return "Failed to get prompt."
        
        print(f"🎯 Using prompt: {prompt_name}")
        
        # Add prompt messages to conversation
        prompt_messages = self.prompt_manager.format_prompt_messages(prompt_result)
        self.llm_client.add_messages(prompt_messages)
        
        # Process the prompt
        return await self.chat_processor.process_from_existing_messages()
    
    def clear_chat_history(self):
        """Clear conversation history"""
        self.llm_client.clear_history()
        print("Chat history cleared!")
    
    def set_model(self, model: str):
        """Change the LLM model"""
        self.llm_client.set_model(model)
        print(f"Model changed to: {model}")
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\\nMCP Client Started!")
        print("Commands:")
        print("  - Type your queries for AI interaction")
        print("  - 'clear' to reset chat history")
        print("  - 'model <name>' to change LLM model")
        print("  - 'resources' to list available resources")
        print("  - 'read <uri>' to read a specific resource")
        print("  - 'prompts' to list available prompts")
        print("  - 'prompt <name>' to use a prompt")
        print("  - 'auto-resources on/off' to toggle automatic resource inclusion")
        print("  - 'quit' to exit")
        
        while True:
            try:
                query = input("\\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                elif query.lower() == 'clear':
                    self.clear_chat_history()
                    continue
                elif query.lower().startswith('model '):
                    model_name = query[6:].strip()
                    self.set_model(model_name)
                    continue
                elif query.lower() == 'resources':
                    await self._handle_list_resources()
                    continue
                elif query.lower().startswith('read '):
                    uri = query[5:].strip()
                    await self._handle_read_resource(uri)
                    continue
                elif query.lower() == 'prompts':
                    await self._handle_list_prompts()
                    continue
                elif query.lower().startswith('prompt '):
                    prompt_name = query[7:].strip()
                    response = await self.use_prompt(prompt_name)
                    print("\\n" + response)
                    continue
                elif query.lower().startswith('auto-resources '):
                    setting = query[15:].strip().lower()
                    if setting in ['on', 'true', 'yes']:
                        self.auto_include_resources = True
                        print("✓ Automatic resource inclusion enabled")
                    elif setting in ['off', 'false', 'no']:
                        self.auto_include_resources = False
                        print("✓ Automatic resource inclusion disabled")
                    else:
                        print("Usage: auto-resources on/off")
                    continue
                
                # Process regular query
                response = await self.process_query(query)
                print("\\n" + response)
                
            except Exception as e:
                print(f"\\nError: {str(e)}")
    
    async def _handle_list_resources(self):
        """Handle the 'resources' command"""
        resources = await self.resource_manager.list_resources()
        output = self.resource_manager.format_resources_list(resources)
        print("\\n" + output)
    
    async def _handle_read_resource(self, uri: str):
        """Handle the 'read <uri>' command"""
        if not uri:
            print("Please provide a resource URI. Usage: read <uri>")
            return
        
        contents = await self.resource_manager.read_resource(uri)
        output = self.resource_manager.format_resource_content(contents)
        print("\\n" + output)
    
    async def _handle_list_prompts(self):
        """Handle the 'prompts' command"""
        prompts = await self.prompt_manager.list_prompts()
        output = self.prompt_manager.format_prompts_list(prompts)
        print("\\n" + output)
    
    async def cleanup(self):
        """Clean up resources"""
        await self.session.cleanup()


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python refactored_client.py <path_to_server_script>")
        sys.exit(1)
    
    client = MCPClient()
    try:
        # Default to weather server if no argument provided
        server_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
            os.path.dirname(__file__), '..', 'servers', 'weather', 'weather.py'
        )
        
        await client.connect_to_server(server_path)
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
