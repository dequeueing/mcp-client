"""Chat Processor - handles the main chat logic and tool execution"""

import json
from typing import List, Dict, Any
from .llm_client import LLMClient
from .tool_manager import ToolManager


class ChatProcessor:
    """Processes chat queries with tool execution support"""
    
    def __init__(self, llm_client: LLMClient, tool_manager: ToolManager):
        self.llm_client = llm_client
        self.tool_manager = tool_manager
    
    async def process_query(self, query: str) -> str:
        """Process a user query with potential tool calls"""
        # Add user message to conversation
        self.llm_client.add_message("user", query)
        
        # Get available tools
        available_tools = await self.tool_manager.get_tools_for_openai()
        
        # Process with tool execution loop
        return await self._execute_with_tools(available_tools)
    
    async def process_from_existing_messages(self) -> str:
        """Process using existing messages in conversation history"""
        available_tools = await self.tool_manager.get_tools_for_openai()
        return await self._execute_with_tools(available_tools)
    
    async def _execute_with_tools(self, available_tools: List[Dict[str, Any]]) -> str:
        """Execute the main tool calling loop"""
        final_text = []
        max_iterations = 10  # Prevent infinite loops
        
        for iteration in range(max_iterations):
            # Get response from LLM
            response = await self.llm_client.chat_completion(available_tools)
            assistant_message = response.choices[0].message
            
            # Add any text content to final output
            if assistant_message.content:
                final_text.append(assistant_message.content)
            
            # Check if there are tool calls to process
            if not assistant_message.tool_calls:
                # No more tool calls, add final assistant message and break
                self.llm_client.messages.append(assistant_message.model_dump())
                break
            
            # Add assistant message with tool calls to conversation
            self.llm_client.messages.append(assistant_message.model_dump())
            
            # Process all tool calls in this response
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
                
                # Parse arguments if they're a string
                if isinstance(tool_args, str):
                    tool_args = json.loads(tool_args)
                
                # Execute tool call
                result = await self.tool_manager.call_tool(tool_name, tool_args)
                
                # Add tool execution info to output
                tool_info = self.tool_manager.format_tool_result(tool_name, tool_args, result)
                final_text.append(tool_info)
                
                # Add tool result to conversation history
                self.llm_client.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result.content)
                })
        
        return "\n".join(final_text)
