import asyncio
import os
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Configure OpenAI client to use OpenRouter
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),  # Use OpenRouter API key
            base_url="https://openrouter.ai/api/v1"   # OpenRouter base URL
        )
        
        # Maintain conversation history across queries
        self.messages = []
        
        # Resource settings
        self.auto_include_resources = False
    # methods will go here00
    
    async def connect_to_server(self, server_script_path: str):
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

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        
        # print detailed tool information
        for tool in tools:
            print(f"Tool: {tool.name}, Description: {tool.description}, Input Schema: {tool.inputSchema}")
        
        # Also list available resources
        try:
            resources_response = await self.session.list_resources()
            resources = resources_response.resources
            if resources:
                print(f"\nConnected to server with {len(resources)} resources:")
                for resource in resources:
                    print(f"Resource: {resource.name} ({resource.uri})")
                    if resource.description:
                        print(f"  Description: {resource.description}")
                    if resource.mimeType:
                        print(f"  MIME Type: {resource.mimeType}")
            else:
                print("\nNo resources available on this server.")
        except Exception as e:
            print(f"\nServer does not support resources or error listing them: {e}")
        
        # Also list available prompts
        try:
            prompts_response = await self.session.list_prompts()
            prompts = prompts_response.prompts
            if prompts:
                print(f"\nConnected to server with {len(prompts)} prompts:")
                for prompt in prompts:
                    print(f"Prompt: {prompt.name}")
                    if prompt.description:
                        print(f"  Description: {prompt.description}")
            else:
                print("\nNo prompts available on this server.")
        except Exception as e:
            print(f"\nServer does not support prompts or error listing them: {e}")
        
        
    async def list_prompts(self):
        """List all available prompts from the server"""
        try:
            response = await self.session.list_prompts()
            return response.prompts
        except Exception as e:
            print(f"Error listing prompts: {e}")
            return []
    
    async def get_prompt(self, name: str, arguments: dict = None):
        """Get a specific prompt with arguments"""
        try:
            response = await self.session.get_prompt(name, arguments or {})
            return response
        except Exception as e:
            print(f"Error getting prompt {name}: {e}")
            return None
        
        
    async def list_resources(self):
        """List all available resources from the server"""
        try:
            response = await self.session.list_resources()
            return response.resources
        except Exception as e:
            print(f"Error listing resources: {e}")
            return []
    
    async def read_resource(self, uri: str):
        """Read a specific resource by URI"""
        try:
            response = await self.session.read_resource(uri)
            return response.contents
        except Exception as e:
            print(f"Error reading resource {uri}: {e}")
            return None
        
        
    async def process_query(self, query: str, include_resources: bool = False) -> str:
        """Process a query using Claude and available tools"""
        
        # Optionally enhance query with relevant resource context
        if include_resources:
            enhanced_query = await self.add_resource_context(query)
        else:
            enhanced_query = query
            
        # Add user message to persistent conversation history
        self.messages.append({
            "role": "user",
            "content": enhanced_query
        })

        # Get tools from the already established session (avoid redundant call)
        response = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]

        # Initial API call using OpenAI format with full conversation history
        response = await self.client.chat.completions.create(
            model="anthropic/claude-3-5-sonnet-20241022",  # OpenRouter model format
            max_tokens=1000,
            messages=self.messages,  # Use persistent conversation history
            tools=available_tools if available_tools else None
        )

        # Process response and handle multiple rounds of tool calls
        final_text = []
        max_iterations = 10  # Prevent infinite loops
        
        for iteration in range(max_iterations):
            assistant_message = response.choices[0].message
            
            # Add any text content to final output
            if assistant_message.content:
                final_text.append(assistant_message.content)

            # Check if there are tool calls to process
            if not assistant_message.tool_calls:
                # No more tool calls, add final assistant message to history and break
                self.messages.append(assistant_message.model_dump())
                break

            # Add assistant message with tool calls to conversation history
            self.messages.append(assistant_message.model_dump())
            
            # Process all tool calls in this response (parallel execution)
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
                
                # Parse arguments if they're a string
                if isinstance(tool_args, str):
                    import json
                    tool_args = json.loads(tool_args)

                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Add tool result to conversation history
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result.content)
                })

            # Get next response from Claude (might contain more tool calls)
            response = await self.client.chat.completions.create(
                model="anthropic/claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=self.messages,  # Use updated conversation history
                tools=available_tools if available_tools else None
            )

        return "\n".join(final_text)

    async def get_relevant_resources(self, query: str, max_resources: int = 3):
        """Get resources that might be relevant to the query"""
        resources = await self.list_resources()
        if not resources:
            return []
        
        # Simple relevance matching - you could make this more sophisticated
        relevant = []
        query_lower = query.lower()
        
        for resource in resources:
            # Check if query keywords match resource name or description
            name_match = any(word in resource.name.lower() for word in query_lower.split())
            desc_match = resource.description and any(word in resource.description.lower() for word in query_lower.split())
            
            if name_match or desc_match:
                relevant.append(resource)
        
        return relevant[:max_resources]

    async def add_resource_context(self, query: str):
        """Add relevant resource content as context to the conversation"""
        relevant_resources = await self.get_relevant_resources(query)
        
        context_parts = []
        for resource in relevant_resources:
            contents = await self.read_resource(resource.uri)
            if contents:
                for content in contents:
                    if hasattr(content, 'text') and content.text:
                        # Truncate long resources
                        text = content.text
                        if len(text) > 1000:
                            text = text[:1000] + "... (truncated)"
                        
                        context_parts.append(f"Resource '{resource.name}' ({resource.uri}):\n{text}")
        
        if context_parts:
            context = "\n\n".join(context_parts)
            return f"Here are some relevant resources for context:\n\n{context}\n\nUser query: {query}"
        
        return query

    def clear_chat_history(self):
        """Clear the conversation history"""
        self.messages = []
        print("Chat history cleared!")


    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Commands:")
        print("  - Type your queries for AI interaction")
        print("  - 'clear' to reset chat history")
        print("  - 'resources' to list available resources")
        print("  - 'read <uri>' to read a specific resource")
        print("  - 'prompts' to list available prompts")
        print("  - 'prompt <name>' to use a prompt")
        print("  - 'auto-resources on/off' to toggle automatic resource inclusion")
        print("  - 'quit' to exit")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break
                elif query.lower() == 'clear':
                    self.clear_chat_history()
                    continue
                elif query.lower() == 'resources':
                    await self.handle_list_resources()
                    continue
                elif query.lower().startswith('read '):
                    uri = query[5:].strip()  # Remove 'read ' prefix
                    await self.handle_read_resource(uri)
                    continue
                elif query.lower() == 'prompts':
                    await self.handle_list_prompts()
                    continue
                elif query.lower().startswith('prompt '):
                    prompt_name = query[7:].strip()  # Remove 'prompt ' prefix
                    await self.handle_use_prompt(prompt_name)
                    continue
                elif query.lower().startswith('auto-resources '):
                    setting = query[15:].strip().lower()  # Remove 'auto-resources ' prefix
                    if setting in ['on', 'true', 'yes']:
                        self.auto_include_resources = True
                        print("✓ Automatic resource inclusion enabled")
                    elif setting in ['off', 'false', 'no']:
                        self.auto_include_resources = False
                        print("✓ Automatic resource inclusion disabled")
                    else:
                        print("Usage: auto-resources on/off")
                    continue

                response = await self.process_query(query, include_resources=self.auto_include_resources)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def handle_list_resources(self):
        """Handle the 'resources' command"""
        resources = await self.list_resources()
        if resources:
            print(f"\nAvailable Resources ({len(resources)}):")
            for i, resource in enumerate(resources, 1):
                print(f"{i}. {resource.name}")
                print(f"   URI: {resource.uri}")
                if resource.description:
                    print(f"   Description: {resource.description}")
                if resource.mimeType:
                    print(f"   MIME Type: {resource.mimeType}")
                if resource.size:
                    print(f"   Size: {resource.size} bytes")
                print()
        else:
            print("\nNo resources available.")

    async def handle_read_resource(self, uri: str):
        """Handle the 'read <uri>' command"""
        if not uri:
            print("Please provide a resource URI. Usage: read <uri>")
            return
            
        contents = await self.read_resource(uri)
        if contents:
            for content in contents:
                print(f"\nResource: {content.uri}")
                if content.mimeType:
                    print(f"MIME Type: {content.mimeType}")
                
                if hasattr(content, 'text') and content.text:
                    print("Content (text):")
                    print("-" * 50)
                    # Truncate very long content
                    text = content.text
                    if len(text) > 2000:
                        text = text[:2000] + "\n... (truncated)"
                    print(text)
                    print("-" * 50)
                elif hasattr(content, 'blob') and content.blob:
                    print("Content (binary - base64 encoded):")
                    print(f"Length: {len(content.blob)} characters")
                    print("Use appropriate tools to decode this binary data.")
                else:
                    print("No content available.")
        else:
            print(f"Could not read resource: {uri}")

    async def handle_list_prompts(self):
        """Handle the 'prompts' command"""
        prompts = await self.list_prompts()
        if prompts:
            print(f"\nAvailable Prompts ({len(prompts)}):")
            for i, prompt in enumerate(prompts, 1):
                print(f"{i}. {prompt.name}")
                if prompt.description:
                    print(f"   Description: {prompt.description}")
                if prompt.arguments:
                    print(f"   Arguments:")
                    for arg in prompt.arguments:
                        required = " (required)" if arg.required else " (optional)"
                        print(f"     - {arg.name}{required}: {arg.description or 'No description'}")
                print()
        else:
            print("\nNo prompts available.")

    async def handle_use_prompt(self, prompt_name: str):
        """Handle using a specific prompt"""
        if not prompt_name:
            print("Please provide a prompt name. Usage: prompt <name>")
            return
        
        # Get prompt definition first
        prompts = await self.list_prompts()
        prompt_def = None
        for p in prompts:
            if p.name == prompt_name:
                prompt_def = p
                break
        
        if not prompt_def:
            print(f"Prompt '{prompt_name}' not found. Use 'prompts' to see available prompts.")
            return
        
        # Collect arguments if needed
        arguments = {}
        if prompt_def.arguments:
            print(f"\nPrompt '{prompt_name}' requires arguments:")
            for arg in prompt_def.arguments:
                while True:
                    required_str = " (required)" if arg.required else " (optional)"
                    prompt_text = f"{arg.name}{required_str}"
                    if arg.description:
                        prompt_text += f" - {arg.description}"
                    
                    value = input(f"{prompt_text}: ").strip()
                    
                    if arg.required and not value:
                        print("This argument is required. Please provide a value.")
                        continue
                    
                    if value:  # Only add non-empty values
                        arguments[arg.name] = value
                    break
        
        # Get the prompt with arguments
        prompt_result = await self.get_prompt(prompt_name, arguments)
        if not prompt_result:
            return
        
        # Add prompt messages to conversation history and process
        print(f"\n🎯 Using prompt: {prompt_name}")
        
        # Log the message from prompt result
        print(f"\n🥵 Prompt messages:")
        for message in prompt_result.messages:
            # Convert prompt message to OpenAI format
            if hasattr(message.content, 'text'):
                content = message.content.text
            else:
                content = str(message.content)
            
            print(f"\n{message.role}: {content}")
        
        
        # Add each message from the prompt to conversation history
        for message in prompt_result.messages:
            # Convert prompt message to OpenAI format
            if hasattr(message.content, 'text'):
                content = message.content.text
            else:
                content = str(message.content)
            
            self.messages.append({
                "role": message.role,
                "content": content
            })
        
        # Process the prompt as if it was a regular query
        response = await self.process_query_from_messages()
        print("\n" + response)

    async def process_query_from_messages(self) -> str:
        """Process query using existing messages in conversation history"""
        # Get tools from the already established session
        response = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]

        # Process with existing conversation history (no new user message to add)
        response = await self.client.chat.completions.create(
            # model="anthropic/claude-3-5-sonnet-20241022",
            model="moonshotai/kimi-k2",
            max_tokens=1000,
            messages=self.messages,
            tools=available_tools if available_tools else None
        )

        # Handle tool calls the same way as process_query
        final_text = []
        max_iterations = 10
        
        for iteration in range(max_iterations):
            assistant_message = response.choices[0].message
            
            if assistant_message.content:
                final_text.append(assistant_message.content)

            if not assistant_message.tool_calls:
                self.messages.append(assistant_message.model_dump())
                break

            self.messages.append(assistant_message.model_dump())
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
                
                if isinstance(tool_args, str):
                    import json
                    tool_args = json.loads(tool_args)

                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result.content)
                })

            response = await self.client.chat.completions.create(
                model="anthropic/claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=self.messages,
                tools=available_tools if available_tools else None
            )

        return "\n".join(final_text)

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
    
async def main():
    # if len(sys.argv) < 2:
    #     print("Usage: python client.py <path_to_server_script>")
    #     sys.exit(1)

    client = MCPClient()
    try:
        # await client.connect_to_server(sys.argv[1])
        server_path = '/home/exouser/temp/langchain-agent/weather/weather.py'
        await client.connect_to_server(server_path)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())