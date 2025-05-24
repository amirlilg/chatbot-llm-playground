
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

async def test_mcp_server():
    """Test the MCP filesystem server"""
    print("🧪 Testing MCP Filesystem Server...")
    
    async with AsyncExitStack() as stack:
        # Load server configuration
        with open("server_config.json", "r") as f:
            config = json.load(f)
        
        server_config = config["mcpServers"]["filesystem"]
        server_params = StdioServerParameters(**server_config)
        
        # Connect to the server
        stdio_transport = await stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = stdio_transport
        
        session = await stack.enter_async_context(
            ClientSession(read, write)
        )
        
        # Initialize the session
        await session.initialize()
        print("✅ Connected to filesystem server")
        
        # List available tools
        tools_response = await session.list_tools()
        print(f"\n📋 Available tools:")
        for tool in tools_response.tools:
            print(f"  • {tool.name}: {tool.description}")
        
        # Test some basic functionality
        print(f"\n🔧 Testing tools:")
        
        # Test list_directory
        try:
            result = await session.call_tool("list_directory", {"path": "."})
            print(f"✅ list_directory: Found {len(result.content)} items")
        except Exception as e:
            print(f"❌ list_directory failed: {e}")
        
        # Test write_file
        try:
            result = await session.call_tool("write_file", {
                "file_path": "test_file.txt",
                "content": "Hello from MCP test!"
            })
            print(f"✅ write_file: {result.content}")
        except Exception as e:
            print(f"❌ write_file failed: {e}")
        
        # Test read_file
        try:
            result = await session.call_tool("read_file", {"file_path": "test_file.txt"})
            print(f"✅ read_file: File content retrieved")
        except Exception as e:
            print(f"❌ read_file failed: {e}")
        
        # Test get_file_info
        try:
            result = await session.call_tool("get_file_info", {"file_path": "test_file.txt"})
            print(f"✅ get_file_info: File info retrieved")
        except Exception as e:
            print(f"❌ get_file_info failed: {e}")
        
        # Clean up test file
        try:
            result = await session.call_tool("delete_file", {"file_path": "test_file.txt"})
            print(f"✅ delete_file: {result.content}")
        except Exception as e:
            print(f"❌ delete_file failed: {e}")
        
        print(f"\n🎉 MCP server test completed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())