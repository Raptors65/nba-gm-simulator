import asyncio
import sys
from typing import Optional, List, Dict
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.stdio = None
        self.write = None
        
        # Initialize messages with system prompt
        self.messages = []
        self.base_system_prompt = """You are an experienced NBA General Manager engaging in trade discussions with another NBA GM. 
                You have deep knowledge of basketball analytics, player values, team needs, and salary cap implications.
                You should:
                - Discuss potential trades in a professional but conversational manner
                - Consider salary cap implications and team needs
                - Reference player statistics and team dynamics when relevant
                - Be strategic but realistic in your trade proposals
                - Maintain a professional tone while being engaging
                - Consider both short-term and long-term implications of trades
                - Be knowledgeable about current NBA trends and player values"""

    def get_team_specific_prompt(self, team: str) -> str:
        """Get a team-specific system prompt"""
        return f"{self.base_system_prompt}\nYou are the GM of the {team}. Consider your team's specific needs, roster, and situation when discussing trades."

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        try:
            is_python = server_script_path.endswith('.py')
            is_js = server_script_path.endswith('.js')
            if not (is_python or is_js):
                raise ValueError("Server script must be a .py or .js file")
                
            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command,
                args=[server_script_path],
                env=None
            )
            
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            
            await self.session.initialize()
            
            # List available tools
            response = await self.session.list_tools()
            tools = response.tools
            print("\nConnected to server with tools:", [tool.name for tool in tools])
        except Exception as e:
            await self.cleanup()
            raise e

    async def process_query(self, messages: List[Dict[str, str]], team: str) -> str:
        """Process a query using Claude and available tools
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            team: The NBA team to generate a response for
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
            
        # Set messages and system prompt
        self.messages = messages
        system_prompt = self.get_team_specific_prompt(team)

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Initial Claude API call
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=self.messages,
            system=system_prompt,
            tools=available_tools
        )

        # Process response and handle tool calls
        tool_results = []
        final_text = []

        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input
                
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                tool_results.append({"call": tool_name, "result": result})
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Continue conversation with tool results
                if hasattr(content, 'text') and content.text:
                    self.messages.append({
                      "role": "assistant",
                      "content": content.text
                    })
                self.messages.append({
                    "role": "user", 
                    "content": result.content
                })

                # Get next response from Claude
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=self.messages,
                )

                final_text.append(response.content[0].text)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query([{"role": "user", "content": query}], "Dallas Mavericks")
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.exit_stack = AsyncExitStack()
            self.session = None
            self.stdio = None
            self.write = None

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())