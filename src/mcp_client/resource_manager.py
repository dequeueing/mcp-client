"""MCP Resources Management - handles resource-related operations"""

from typing import List, Optional
from .mcp_session import MCPSession


class ResourceManager:
    """Manages MCP resource operations"""
    
    def __init__(self, session: MCPSession):
        self.session = session
    
    async def list_resources(self):
        """List all available resources"""
        try:
            response = await self.session.session.list_resources()
            return response.resources
        except Exception as e:
            print(f"Error listing resources: {e}")
            return []
    
    async def read_resource(self, uri: str):
        """Read a specific resource by URI"""
        try:
            response = await self.session.session.read_resource(uri)
            return response.contents
        except Exception as e:
            print(f"Error reading resource {uri}: {e}")
            return None
    
    async def get_relevant_resources(self, query: str, max_resources: int = 3):
        """Get resources that might be relevant to the query"""
        resources = await self.list_resources()
        if not resources:
            return []
        
        # Simple relevance matching
        relevant = []
        query_lower = query.lower()
        
        for resource in resources:
            # Check if query keywords match resource name or description
            name_match = any(word in resource.name.lower() for word in query_lower.split())
            desc_match = resource.description and any(word in resource.description.lower() for word in query_lower.split())
            
            if name_match or desc_match:
                relevant.append(resource)
        
        return relevant[:max_resources]
    
    async def add_resource_context(self, query: str) -> str:
        """Add relevant resource content as context to the query"""
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
    
    def format_resources_list(self, resources) -> str:
        """Format resources for display"""
        if not resources:
            return "No resources available."
        
        output = [f"Available Resources ({len(resources)}):"]
        for i, resource in enumerate(resources, 1):
            output.append(f"{i}. {resource.name}")
            output.append(f"   URI: {resource.uri}")
            if resource.description:
                output.append(f"   Description: {resource.description}")
            if resource.mimeType:
                output.append(f"   MIME Type: {resource.mimeType}")
            if resource.size:
                output.append(f"   Size: {resource.size} bytes")
            output.append("")
        
        return "\n".join(output)
    
    def format_resource_content(self, contents) -> str:
        """Format resource content for display"""
        if not contents:
            return "No content available."
        
        output = []
        for content in contents:
            output.append(f"Resource: {content.uri}")
            if content.mimeType:
                output.append(f"MIME Type: {content.mimeType}")
            
            if hasattr(content, 'text') and content.text:
                output.append("Content (text):")
                output.append("-" * 50)
                # Truncate very long content
                text = content.text
                if len(text) > 2000:
                    text = text[:2000] + "\n... (truncated)"
                output.append(text)
                output.append("-" * 50)
            elif hasattr(content, 'blob') and content.blob:
                output.append("Content (binary - base64 encoded):")
                output.append(f"Length: {len(content.blob)} characters")
                output.append("Use appropriate tools to decode this binary data.")
            else:
                output.append("No content available.")
        
        return "\n".join(output)
