# MCP Client

A comprehensive, modular implementation of an MCP (Model Context Protocol) client with full support for tools, resources, and prompts.

## 🚀 Quick Start

```bash
# Install dependencies
uv install

# Run the example client
cd examples
python basic_client.py

# Or run with a specific server
python basic_client.py ../servers/weather/weather.py
```

## 📁 Project Structure

```
mcp-client/
├── src/mcp_client/          # Core client package
├── servers/                 # MCP server implementations
├── examples/                # Usage examples  
├── tests/                   # Test suite
└── docs/                    # Documentation
```

See [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed information.

## ✨ Features

- **Tools**: Execute server-provided functions
- **Resources**: Access server-provided data and context
- **Prompts**: Use server-provided prompt templates
- **LLM Integration**: Communicate with models via OpenRouter
- **Modular Design**: Clean, testable, extensible architecture

## 🏗️ Architecture

The client is built with a modular architecture:

- **MCPSession**: Connection management
- **ToolManager**: Tool operations
- **ResourceManager**: Resource handling
- **PromptManager**: Prompt operations
- **LLMClient**: Language model communication
- **ChatProcessor**: Chat orchestration

## 📚 Documentation

- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Refactoring Guide](docs/README_refactored.md)
- [Refactoring Summary](docs/REFACTORING_SUMMARY.md)

## 🧪 Testing

```bash
cd tests
python test_client.py
```

## 🛠️ Development

This project follows Python best practices with clear separation of concerns, comprehensive testing, and professional documentation standards.