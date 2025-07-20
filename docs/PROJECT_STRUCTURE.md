# MCP Client Project Structure

This document describes the organized structure of the MCP (Model Context Protocol) client project.

## 📁 Project Structure

```
mcp-client/
├── 📄 README.md                   # Main project documentation
├── 📄 pyproject.toml              # Python project configuration
├── 📄 uv.lock                     # Dependency lock file
├── 📄 .env                        # Environment variables
├── 📄 .gitignore                  # Git ignore rules
├── 📄 __init__.py                 # Root package marker
│
├── 📁 src/                        # Source code
│   └── 📁 mcp_client/            # Main client package
│       ├── 📄 __init__.py         # Package initialization
│       ├── 📄 mcp_session.py      # MCP server connection management
│       ├── 📄 tool_manager.py     # Tool operations and formatting
│       ├── 📄 resource_manager.py # Resource operations and context
│       ├── 📄 prompt_manager.py   # Prompt operations and arguments
│       ├── 📄 llm_client.py       # LLM communication via OpenRouter
│       └── 📄 chat_processor.py   # Chat logic and tool execution
│
├── 📁 servers/                    # MCP server implementations
│   └── 📁 weather/               # Weather server example
│       ├── 📄 __init__.py        # Server package marker
│       ├── 📄 weather.py         # Weather MCP server
│       └── 📄 pyproject.toml     # Server dependencies
│
├── 📁 examples/                   # Usage examples
│   └── 📄 basic_client.py        # Basic client implementation example
│
├── 📁 tests/                     # Test suite
│   ├── 📄 __init__.py            # Test package marker
│   └── 📄 test_client.py         # Client functionality tests
│
└── 📁 docs/                      # Documentation
    ├── 📄 README_refactored.md   # Refactoring documentation
    └── 📄 REFACTORING_SUMMARY.md # Refactoring summary
```

## 🏗️ Architecture Overview

### Core Package (`src/mcp_client/`)

The main client functionality is organized into focused modules:

1. **`mcp_session.py`** - Connection Management
   - Handles MCP server connections
   - Manages protocol initialization
   - Provides session lifecycle

2. **`tool_manager.py`** - Tool Operations
   - Lists and formats tools for LLM APIs
   - Executes tool calls
   - Formats tool results

3. **`resource_manager.py`** - Resource Management
   - Lists and reads resources
   - Provides relevance matching
   - Handles auto-inclusion of context

4. **`prompt_manager.py`** - Prompt Handling
   - Manages prompt operations
   - Collects arguments interactively
   - Converts to LLM-compatible format

5. **`llm_client.py`** - Language Model Communication
   - OpenRouter/OpenAI integration
   - Conversation history management
   - System prompt handling

6. **`chat_processor.py`** - Chat Orchestration
   - Main chat logic coordination
   - Tool execution loops
   - Multi-turn conversation handling

### Servers (`servers/`)

MCP server implementations organized by functionality:

- **`weather/`** - Comprehensive weather server
  - Implements all three MCP primitives
  - Uses National Weather Service API
  - Demonstrates best practices

### Examples (`examples/`)

Ready-to-run examples showing how to use the client:

- **`basic_client.py`** - Complete client implementation
  - Interactive chat interface
  - All MCP primitives supported
  - Configurable settings

### Tests (`tests/`)

Test suite for validating functionality:

- **`test_client.py`** - Integration tests
  - Server connection testing
  - Tool/resource/prompt functionality
  - End-to-end validation

### Documentation (`docs/`)

Comprehensive project documentation:

- Refactoring guides
- Architecture explanations
- Usage examples

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd mcp-client
uv install
```

### 2. Run Example Client
```bash
cd examples
python basic_client.py
```

### 3. Run Tests
```bash
cd tests
python test_client.py
```

## 🎯 Benefits of This Structure

### ✅ **Clear Separation of Concerns**
- Each module has a single responsibility
- Easy to understand and maintain
- Minimal coupling between components

### ✅ **Scalability**
- New servers can be added to `servers/`
- New examples can be added to `examples/`
- Package structure supports growth

### ✅ **Testability**
- Components can be tested independently
- Clear test organization
- Easy to add new test categories

### ✅ **Reusability**
- Core client package is reusable
- Server implementations can be shared
- Examples serve as templates

### ✅ **Professional Standards**
- Follows Python packaging best practices
- Clear documentation structure
- Proper dependency management

## 🔧 Development Workflow

### Adding New Servers
1. Create new directory in `servers/`
2. Implement MCP server
3. Add dependencies to local `pyproject.toml`
4. Update documentation

### Adding New Features
1. Identify appropriate module in `src/mcp_client/`
2. Implement feature with tests
3. Update examples if needed
4. Document changes

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_client.py
```

This structure provides a solid foundation for MCP client development while maintaining clean separation of concerns and professional standards.
