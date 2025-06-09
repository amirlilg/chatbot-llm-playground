import requests
import json
import asyncio
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from typing import List, Dict, TypedDict

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class LocalMCPChatbot:
    def __init__(self, desired_model="qwen3:8b", ollama_host="192.168.176.1", ollama_port=11434, timeout=120):
        # Choose a model that supports function calling
        # Options: llama3.2:3b, llama3.1:8b, mistral:7b, qwen2.5:3b, qwen3:8b
        self.desired_model = desired_model
        self.ollama_base_url = f"http://{ollama_host}:{ollama_port}"
        self.timeout = timeout  # Timeout in seconds
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        
    def test_ollama_connection(self):
        """Test connection to Ollama API"""
        print("Testing Ollama connection...")
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                model_names = [model['name'] for model in models['models']]
                print(f"✅ Connected to Ollama. Available models: {model_names}")
                
                if self.desired_model not in model_names:
                    print(f"⚠️  Warning: Model '{self.desired_model}' not found in available models")
                    print(f"Available models: {model_names}")
                    return False
                else:
                    print(f"✅ Model '{self.desired_model}' is available!")
                return True
            else:
                print(f"❌ Failed to connect to Ollama: HTTP {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to Ollama at {self.ollama_base_url}")
            print("Make sure Ollama is running on Windows and accessible from WSL")
            return False
        except Exception as e:
            print(f"❌ Error testing Ollama connection: {e}")
            return False

    def ollama_chat(self, messages, tools=None, stream=False):
        """Make a chat request to Ollama API"""
        url = f"{self.ollama_base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        
        data = {
            "model": self.desired_model,
            "messages": messages,
            "stream": stream
        }
        
        # Add tools if provided
        if tools:
            data["tools"] = tools
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                result_content = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        json_data = json.loads(line.decode("utf-8"))
                        if "message" in json_data:
                            content = json_data["message"].get("content", "")
                            result_content += content
                            if json_data.get("done", False):
                                break
                    except json.JSONDecodeError:
                        continue
                
                return {
                    "message": {
                        "role": "assistant",
                        "content": result_content
                    }
                }
            else:
                # Handle non-streaming response
                return response.json()
                
        except requests.exceptions.RequestException as e:
            print(f"Error making request to Ollama: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error in ollama_chat: {e}")
            raise

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            
            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise

    def format_tools_for_ollama(self) -> List[Dict]:
        """Format MCP tools for Ollama's function calling format"""
        ollama_tools = []
        
        for tool in self.available_tools:
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            }
            ollama_tools.append(ollama_tool)
        
        return ollama_tools

    async def call_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool and return the result"""
        try:
            session = self.tool_to_session[tool_name]
            result = await session.call_tool(tool_name, arguments=arguments)
            
            # Extract content from MCP result
            if hasattr(result, 'content'):
                if isinstance(result.content, list):
                    return '\n'.join([str(item) for item in result.content])
                else:
                    return str(result.content)
            else:
                return str(result)
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"

    async def process_query(self, query: str, messages: List[Dict]) -> List[Dict]:
        """Process a query with potential tool calls"""
        
        # Add user query to messages
        messages.append({"role": "user", "content": query})
        
        # Format tools for Ollama
        tools = self.format_tools_for_ollama() if self.available_tools else None
        
        try:
            # Make request to Ollama with tools
            response = self.ollama_chat(
                messages=messages,
                tools=tools
            )
            
            assistant_message = response['message']
            messages.append(assistant_message)
            
            # Check if the model wants to call tools
            if 'tool_calls' in assistant_message and assistant_message['tool_calls']:
                print(f"\n🔧 LLM Model is calling tools...")
                
                # Process each tool call
                for tool_call in assistant_message['tool_calls']:
                    function_name = tool_call['function']['name']
                    function_args = tool_call['function']['arguments']
                    
                    print(f"   Calling {function_name} with args: {function_args}")
                    
                    # Call the MCP tool
                    tool_result = await self.call_mcp_tool(function_name, function_args)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call.get('id', 'unknown')
                    })
                
                # Get final response after tool calls
                final_response = self.ollama_chat(messages=messages)
                
                final_message = final_response['message']
                messages.append(final_message)
                print(f"\n{self.desired_model}: {final_message['content']}")
                
            else:
                # No tool calls, just display the response
                print(f"\n{self.desired_model}: {assistant_message['content']}")
            
        except Exception as e:
            print(f"Error processing query: {e}")
        
        return messages

    async def chat_loop(self):
        """Run an interactive chat loop with tool support"""
        print(f"\n🤖 MCP Chatbot Started with {self.desired_model}!")
        print("Available filesystem tools:")
        for tool in self.available_tools:
            print(f"  • {tool['name']}: {tool['description']}")
        print("\nType your queries or 'exit' to end the conversation.")
        
        messages = []
        
        # Optional: Set a system prompt
        system_prompt = input("\nEnter a system prompt (or press Enter to use default): ").strip()
        if not system_prompt:
            system_prompt = ("You are a helpful AI assistant with access to filesystem tools. "
                           "You can read, write, list, and manage files and directories. "
                           "Use the available tools when users ask about file operations.")
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Ending conversation. Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                messages = await self.process_query(user_input, messages)
                
            except KeyboardInterrupt:
                print("\n\n👋 Conversation interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

    async def cleanup(self):
        """Cleanly close all resources"""
        await self.exit_stack.aclose()

async def main():
    desired_model = "qwen3:8b"
    ollama_host = "192.168.176.1"
    ollama_port = 11434
    # You can specify different models and connection details here
    chatbot = LocalMCPChatbot(
        desired_model=desired_model,  # Change this to your preferred model
        ollama_host=ollama_host,   # Usually localhost if running on same machine
        ollama_port=ollama_port,        # Default Ollama port
        timeout=180              # Timeout in seconds (3 minutes)
    )
    
    try:
        # Test Ollama connection
        if not chatbot.test_ollama_connection():
            print("Failed to connect to Ollama. Exiting.")
            print("\nTroubleshooting tips:")
            print("1. Make sure Ollama is running on Windows")
            print("2. Check if Windows Firewall is blocking the connection")
            print(f"3. Try accessing http://{ollama_host}:{ollama_port} in your browser")
            return
        
        # Connect to MCP servers
        print("\nConnecting to MCP servers...")
        await chatbot.connect_to_servers()
        
        # Start chat loop
        await chatbot.chat_loop()
        
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())