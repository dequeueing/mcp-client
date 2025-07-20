"""LLM Client - handles communication with language models via OpenRouter"""

import os
import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """Manages communication with language models"""
    
    def __init__(self, model: str = "anthropic/claude-3-5-sonnet-20241022"):
        # Configure OpenAI client to use OpenRouter
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        
        # Conversation history with system prompt
        self.messages = [
            {
                "role": "system",
                "content": """You are an intelligent assistant with access to MCP (Model Context Protocol) tools, resources, and prompts. 

Guidelines:
- Use available tools to fetch real-time data when needed
- Leverage resources for reference information and context
- Be concise but thorough in your responses
- When using tools, explain what you're doing and why
- If multiple tools are needed, use them efficiently in sequence
- Always provide helpful, accurate information based on the data you receive"""
            }
        ]
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.messages.append({
            "role": role,
            "content": content
        })
    
    def add_messages(self, messages: List[Dict[str, str]]):
        """Add multiple messages to the conversation history"""
        self.messages.extend(messages)
    
    async def chat_completion(self, tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        """Get a chat completion from the LLM"""
        return await self.client.chat.completions.create(
            model=self.model,
            max_tokens=1000,
            messages=self.messages,
            tools=tools if tools else None
        )
    
    def clear_history(self):
        """Clear conversation history but keep system prompt"""
        system_prompt = self.messages[0] if self.messages and self.messages[0]["role"] == "system" else None
        self.messages = []
        if system_prompt:
            self.messages.append(system_prompt)
    
    def set_model(self, model: str):
        """Change the model being used"""
        self.model = model
    
    def get_conversation_length(self) -> int:
        """Get the number of messages in conversation"""
        return len(self.messages)
