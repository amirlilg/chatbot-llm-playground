from dotenv import load_dotenv
import cohere
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List
import asyncio
import nest_asyncio
import os
import json

nest_asyncio.apply()

load_dotenv()

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.session: ClientSession = None
        self.cohere_client = cohere.Client(os.getenv('COHERE_TRIAL_KEY'))
        self.available_tools: List[dict] = []
        self.conversation_history = []

    async def process_query(self, query):
        # Add the user query to conversation history
        self.conversation_history.append({"role": "User", "message": query})
        
        # Prepare tools in the format expected by Cohere
        cohere_tools = []
        for tool in self.available_tools:
            cohere_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "parameter_definitions": tool["input_schema"]
            })
        
        # Initial call to Cohere
        response = self.cohere_client.chat(
            model="command-light",  # or another appropriate Cohere model
            message=query,
            temperature=0.3,
            chat_history=self.conversation_history,
            tools=cohere_tools if cohere_tools else None,
            prompt_truncation='AUTO'
        )
        
        process_query = True
        while process_query:
            # Check if the response has tool calls
            if response.tool_calls and len(response.tool_calls) > 0:
                # Process each tool call
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["parameters"]
                    
                    print(f"Calling tool {tool_name} with args {tool_args}")
                    
                    # Call the tool via MCP session
                    result = await self.session.call_tool(tool_name, arguments=tool_args)
                    
                    # Add the tool result to a new message
                    tool_result_message = f"Tool {tool_name} result: {result.content}"
                    self.conversation_history.append({"role": "System", "message": tool_result_message})
                    
                    # Call Cohere again with the tool result
                    response = self.cohere_client.chat(
                        model="command-light",
                        message=f"Here's the result from the {tool_name} tool: {result.content}. Please continue with your response.",
                        temperature=0.3,
                        chat_history=self.conversation_history,
                        tools=cohere_tools if cohere_tools else None,
                        prompt_truncation='AUTO'
                    )
            else:
                # No more tool calls, print the response and exit the loop
                print(response.text)
                self.conversation_history.append({"role": "Chatbot", "message": response.text})
                process_query = False
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot with Cohere Started!")
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
    
    async def connect_to_server_and_run(self):
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="uv",  # Executable
            args=["run", "research_server.py"],  # Optional command line arguments
            env=None,  # Optional environment variables
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
                
                self.available_tools = [{
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]
    
                await self.chat_loop()


async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()
  

if __name__ == "__main__":
    asyncio.run(main())