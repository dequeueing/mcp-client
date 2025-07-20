"""MCP Prompts Management - handles prompt-related operations"""

from typing import List, Dict, Any, Optional
from .mcp_session import MCPSession


class PromptManager:
    """Manages MCP prompt operations"""
    
    def __init__(self, session: MCPSession):
        self.session = session
    
    async def list_prompts(self):
        """List all available prompts"""
        try:
            response = await self.session.session.list_prompts()
            return response.prompts
        except Exception as e:
            print(f"Error listing prompts: {e}")
            return []
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None):
        """Get a specific prompt with arguments"""
        try:
            response = await self.session.session.get_prompt(name, arguments or {})
            return response
        except Exception as e:
            print(f"Error getting prompt {name}: {e}")
            return None
    
    def format_prompts_list(self, prompts) -> str:
        """Format prompts for display"""
        if not prompts:
            return "No prompts available."
        
        output = [f"Available Prompts ({len(prompts)}):"]
        for i, prompt in enumerate(prompts, 1):
            output.append(f"{i}. {prompt.name}")
            if prompt.description:
                output.append(f"   Description: {prompt.description}")
            if prompt.arguments:
                output.append("   Arguments:")
                for arg in prompt.arguments:
                    required = " (required)" if arg.required else " (optional)"
                    output.append(f"     - {arg.name}{required}: {arg.description or 'No description'}")
            output.append("")
        
        return "\n".join(output)
    
    def collect_prompt_arguments(self, prompt_def) -> Dict[str, Any]:
        """Interactively collect arguments for a prompt"""
        arguments = {}
        if not prompt_def.arguments:
            return arguments
        
        print(f"\nPrompt '{prompt_def.name}' requires arguments:")
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
        
        return arguments
    
    def format_prompt_messages(self, prompt_result) -> List[Dict[str, str]]:
        """Convert prompt messages to OpenAI format"""
        messages = []
        for message in prompt_result.messages:
            # Convert prompt message to OpenAI format
            if hasattr(message.content, 'text'):
                content = message.content.text
            else:
                content = str(message.content)
            
            messages.append({
                "role": message.role,
                "content": content
            })
        
        return messages
