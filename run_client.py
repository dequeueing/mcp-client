#!/usr/bin/env python3
"""
MCP Client Launcher

Easy way to run the MCP client with the weather server or any custom server.

Usage:
    python run_client.py                    # Use default weather server
    python run_client.py path/to/server.py  # Use custom server
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from examples.basic_client import MCPClient


async def main():
    """Main entry point for the MCP client"""
    # Default to weather server if no argument provided
    if len(sys.argv) > 1:
        server_path = sys.argv[1]
    else:
        server_path = os.path.join(
            os.path.dirname(__file__), 'servers', 'weather', 'weather.py'
        )
    
    print(f"🌤️  Starting MCP Client with server: {server_path}")
    
    client = MCPClient()
    try:
        await client.connect_to_server(server_path)
        await client.chat_loop()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
