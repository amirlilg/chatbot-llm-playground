import ollama
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
    def __init__(self, desired_model = "llama3.2:3b"):
        # Choose a model that supports function calling
        # Options: llama3.2:3b, llama3.1:8b, mistral:7b, qwen2.5:3b
        self.desired_model = desired_model
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        
    def setup_ollama(self):
        """Setup and verify Ollama installation"""
        print("Setting up Ollama...")
        
        # Check if model is available
        # try:
        #     models = ollama.list()
        #     model_names = [model['name'] for model in models['models']]
            
        #     if self.desired_model not in model_names:
        #         print(f"Pulling {self.desired_model} model...")
        #         ollama.pull(self.desired_model)
        #         print("✅ Llama3.2 model downloaded successfully!")
        #     else:
        #         print("✅ Llama3.2 model is already available!")
                
        # except Exception as e:
        #     print(f"❌ Error setting up Ollama: {e}")
        #     return False
        
        return True

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
            with open("server_config_1.json", "r") as file:
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
            response = ollama.chat(
                model=self.desired_model,
                messages=messages,
                tools=tools if tools else None
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
                final_response = ollama.chat(
                    model=self.desired_model,
                    messages=messages
                )
                
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
        print("\n🤖 MCP Chatbot Started!")
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
    # chatbot = LocalMCPChatbot(desired_model="qwen3:0.6b")
    chatbot = LocalMCPChatbot()
    try:
        # Setup Ollama
        # if not chatbot.setup_ollama():
        #     print("Failed to setup Ollama. Exiting.")
        #     return
        
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