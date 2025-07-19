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
        
        
    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        # Add user message to persistent conversation history
        self.messages.append({
            "role": "user",
            "content": query
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

    def clear_chat_history(self):
        """Clear the conversation history"""
        self.messages = []
        print("Chat history cleared!")


    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries, 'clear' to reset chat history, or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break
                elif query.lower() == 'clear':
                    self.clear_chat_history()
                    continue

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

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