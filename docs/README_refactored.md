# Refactored MCP Client

This is a refactored version of the MCP client that separates concerns into modular components.

## File Structure

```
mcp-client/
├── __init__.py              # Package initialization
├── mcp_session.py           # MCP server connection management
├── tool_manager.py          # Tool operations and formatting
├── resource_manager.py      # Resource operations and context handling
├── prompt_manager.py        # Prompt operations and argument collection
├── llm_client.py           # Language model communication
├── chat_processor.py       # Main chat logic with tool execution
├── refactored_client.py    # Main client using modular components
├── test_refactored.py      # Test script for the refactored client
├── client.py              # Original monolithic client (for comparison)
└── README_refactored.md   # This file
```

## Architecture

### Core Components

1. **MCPSession** (`mcp_session.py`)
   - Manages connection to MCP servers
   - Handles basic MCP protocol operations
   - Provides session lifecycle management

2. **ToolManager** (`tool_manager.py`)
   - Lists and formats tools for OpenAI API
   - Executes tool calls
   - Formats tool results for display

3. **ResourceManager** (`resource_manager.py`)
   - Manages resource operations (list, read)
   - Provides relevance matching for auto-inclusion
   - Formats resources for display

4. **PromptManager** (`prompt_manager.py`)
   - Handles prompt operations
   - Collects prompt arguments interactively
   - Converts prompt messages to OpenAI format

5. **LLMClient** (`llm_client.py`)
   - Manages OpenRouter/OpenAI communication
   - Maintains conversation history with system prompt
   - Provides clean chat completion interface

6. **ChatProcessor** (`chat_processor.py`)
   - Orchestrates the main chat logic
   - Handles tool execution loops
   - Processes queries with multiple tool calls

### Benefits of Refactoring

1. **Separation of Concerns**: Each component has a single responsibility
2. **Testability**: Individual components can be unit tested
3. **Maintainability**: Changes to one aspect don't affect others
4. **Reusability**: Components can be reused in other projects
5. **Readability**: Smaller, focused files are easier to understand
6. **Extensibility**: New features can be added without modifying existing code

## Usage

### Basic Usage
```python
from refactored_client import MCPClient

client = MCPClient()
await client.connect_to_server("/path/to/server.py")
response = await client.process_query("Your query here")
```

### Advanced Usage
```python
# Change model
client.set_model("moonshotai/kimi-k2")

# Enable auto-resource inclusion
client.auto_include_resources = True

# Use a prompt
response = await client.use_prompt("weather_report")

# Clear conversation history
client.clear_chat_history()
```

## Testing

Run the test script to verify the refactored client works:

```bash
python test_refactored.py
```

Or run the interactive client:

```bash
python refactored_client.py /home/exouser/temp/langchain-agent/weather/weather.py
```

## Comparison with Original

| Aspect | Original | Refactored |
|--------|----------|------------|
| File size | 552 lines | Multiple smaller files |
| Testability | Difficult | Easy (isolated components) |
| Readability | Mixed concerns | Clear separation |
| Extensibility | Requires large edits | Add new components |
| Debugging | Hard to isolate issues | Component-level debugging |

## Future Enhancements

The modular structure makes it easy to add:

1. **Configuration Management**: Separate config component
2. **Logging**: Dedicated logging component
3. **Error Handling**: Centralized error management
4. **Caching**: Resource and tool result caching
5. **Authentication**: Separate auth component
6. **Metrics**: Usage tracking and analytics
