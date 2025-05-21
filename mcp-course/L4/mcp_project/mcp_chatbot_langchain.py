from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_cohere import ChatCohere
from langchain_core.tools import Tool, tool
from langchain.agents import initialize_agent, AgentType
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, Any
import asyncio
import json
import os
import nest_asyncio
import traceback

nest_asyncio.apply()
load_dotenv()

class MCP_ChatBot:
    def __init__(self):
        # Initialize session and MCP client objects
        self.session: ClientSession = None
        self.mcp_tools: List[Dict[str, Any]] = []
        self.langchain_tools: List[Tool] = []
        self.chat_history = []
        
        # Check for API key
        if not os.getenv("COHERE_TRIAL_KEY"):
            raise ValueError("Please set COHERE_TRIAL_KEY environment variable")
        
        # Initialize Cohere model
        self.llm = ChatCohere(
            model="command-r-plus",  # or another Cohere model
            temperature=0
        )

    def setup_agent(self):
        """Set up the LangChain agent with the current tools"""
        # Create a CONVERSATIONAL_REACT_DESCRIPTION agent - simpler than structured tool chat
        self.agent = initialize_agent(
            self.langchain_tools,
            self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )

    async def process_query(self, query):
        """Process a user query through the LangChain agent"""
        try:
            # Add input to chat history
            self.chat_history.append(HumanMessage(content=query))
            
            # Invoke the agent
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.agent.invoke({
                    "input": query, 
                    "chat_history": [(m.content if isinstance(m, (HumanMessage, AIMessage)) else str(m)) 
                                    for m in self.chat_history[:-1]]  # Convert to simple format
                })
            )
            
            # Add response to chat history
            response = result["output"]
            self.chat_history.append(AIMessage(content=response))
            
            print(response)
            
        except Exception as e:
            print(f"Error during query processing: {str(e)}")
            print(traceback.format_exc())

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot with LangChain Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                await self.process_query(query)
                print("\n")

            except Exception as e:
                print(f"\nError: {str(e)}")

    def create_mcp_tool(self, mcp_tool):
        """Create a LangChain tool from an MCP tool definition"""
        tool_name = mcp_tool["name"]
        tool_desc = mcp_tool["description"]
        
        @tool(name=tool_name, description=tool_desc)
        def mcp_tool_function(*args, **kwargs):
            """Wrapper for MCP tool calls"""
            try:
                # Run the async call in the event loop
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    self.session.call_tool(tool_name, arguments=kwargs)
                )
                return result.content
            except Exception as e:
                return f"Error calling {tool_name}: {str(e)}"
        
        return mcp_tool_function

    async def connect_to_server_and_run(self):
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="uv",  # Executable
            args=["run", "research_server.py"],  # Command line arguments
            env=None,  # Environment variables
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection
                await session.initialize()

                # List available tools
                response = await session.list_tools()
                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])

                # Store MCP tools
                self.mcp_tools = [{
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                } for tool in response.tools]
                
                # Convert MCP tools to LangChain tools
                self.langchain_tools = []
                for mcp_tool in self.mcp_tools:
                    lc_tool = self.create_mcp_tool(mcp_tool)
                    self.langchain_tools.append(lc_tool)
                
                # Set up the agent with the tools
                self.setup_agent()
                
                # Start chat loop
                await self.chat_loop()

async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()

if __name__ == "__main__":
    asyncio.run(main())