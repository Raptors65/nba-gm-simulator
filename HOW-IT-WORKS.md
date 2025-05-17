# NBA GM Simulator: Architecture and Implementation Guide

This document provides a comprehensive overview of the NBA GM Simulator, a platform that simulates NBA team management with intelligent trade evaluation powered by AI. The system uses Anthropic's Claude AI model with MCP (Model Context Protocol) integration to enable NBA API access for more informed trade evaluations.

## System Overview

The NBA GM Simulator allows users to:
- Select and manage an NBA team
- Review team rosters and player statistics
- Propose and evaluate trades with AI-powered GMs representing other NBA teams
- Access real NBA data through Claude AI using MCP

The system consists of several interconnected components:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Frontend UI    │◄────┤  Flask Server   │◄────┤  GM Agents      │
│  (React/Next.js)│     │                 │     │                 │
│                 │     │                 │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         └─────────────►│                 │◄─────────────┘
                        │  League State   │
                        │                 │
                        └────────┬────────┘
                                 │
                                 │
                                 ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Claude AI      │◄────┤  NBA MCP Server │
                        │  (Trade Eval)   │     │  (NBA API)      │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
```

## Core Components

### 1. League State (`league_state.json`, `models.py`)
- Centralized data store maintaining the entire NBA simulation state
- Contains teams, players, draft picks, and trade history
- Implements data models and business logic for the simulation

### 2. GM Agents (`gm_agent.py`)
- Autonomous agents representing NBA team general managers
- Evaluate trades based on player value, team needs, and salary constraints
- Use Claude AI enhanced with NBA API access through MCP for trade decisions
- Generate and respond to trade proposals with realistic rationales

### 3. NBA MCP Server (`trade_mcp_server.py`, `nba_server.py`)
- Implements the Model Context Protocol (MCP) to provide NBA data tools to Claude
- Provides access to NBA API endpoints for players, teams, and stats
- Enables Claude to analyze trades with real NBA data context

### 4. MCP Client (`client.py`)
- Manages communication between Claude and the MCP server
- Handles tool invocation and response processing
- Formats messages and ensures proper conversation flow

### 5. Flask Server (`flask_server.py`) 
- HTTP API server connecting frontend with backend systems
- Handles authentication, request routing, and response formatting
- Manages user sessions and team interactions

### 6. Frontend (in separate `/frontend` directory)
- React/Next.js application providing user interface
- Visualizes team info, player stats, and trade proposals
- Provides interactive controls for team management

## Data Flow

### Trade Evaluation Process

1. **Trade Proposal Initiation**
   - User proposes a trade through the frontend, or
   - AI GM initiates a trade proposal based on team needs analysis

2. **Trade Evaluation**
   - The receiving GM agent analyzes the trade using:
     - Internal player valuation algorithms
     - Team needs assessment
     - Salary cap implications
     - Claude AI with NBA API access through MCP

3. **MCP-Enhanced Analysis**
   - Claude uses NBA MCP tools to gather relevant NBA data
   - It can call tools like `nba_analyze_trade`, `nba_get_player_info`
   - The data enriches trade evaluation with real NBA context

4. **Decision and Response**
   - The GM agent decides to accept, reject, or counter the trade
   - Claude provides the rationale in a human-like format
   - The response is returned to the user or other GM agent

5. **Trade Execution**
   - If accepted, the league state is updated to reflect the trade
   - Player rosters, team salary caps, and draft picks are adjusted

## Key Files Explained

### `models.py`
Defines the core data models and classes for the simulation using Pydantic:
- `Player`: Player attributes, contracts, and statistics
- `Team`: Team information, roster, and salary cap management
- `Trade`: Trade proposal structure with involved teams and assets
- `LeagueState`: Overall league state including all teams and trade history

### `gm_agent.py`
Contains the GM agent logic and trade evaluation system:
- `GMAgent`: Core agent class with player valuation and trade analysis
- `evaluate_trade_with_claude`: Uses Claude with MCP to evaluate trades
- `GMAgentManager`: Coordinates multiple GM agents in the simulation
- MCP integration for enhancing Claude with NBA API access

### `trade_mcp_server.py`
MCP server providing NBA API tools:
- `nba_get_player_info`: Get details about specific NBA players
- `nba_get_player_stats`: Retrieve player statistical data
- `nba_analyze_trade`: Basic trade analysis with player comparisons
- Additional tools for team information and league data

### `client.py`
Implements the MCP client to connect Claude with the MCP server:
- `MCPClient`: Manages MCP server connections and tool processing
- `process_query`: Handles Claude conversations with tool invocations
- Message formatting and conversation state tracking

### `flask_server.py`
Implements the HTTP API serving the frontend:
- API endpoints for team management, trade proposals, and league data
- Session management and authentication
- Request validation and response formatting

## Claude Integration with MCP

The system uses Anthropic's Claude AI model with MCP integration to provide intelligent and data-informed trade evaluations:

1. **Connection Setup**
   ```python
   # From gm_agent.py
   async def connect_to_mcp_server(self, server_script_path: str = "trade_mcp_server.py"):
       server_params = StdioServerParameters(
           command="python",
           args=[server_script_path],
           env=None
       )
       
       stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
       stdio, write = stdio_transport
       self.mcp_session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
       
       await self.mcp_session.initialize()
   ```

2. **Tool Registration with Claude**
   ```python
   # Get available tools from MCP server
   response = await self.mcp_session.list_tools()
   available_tools = [{ 
       "name": tool.name,
       "description": tool.description,
       "input_schema": tool.inputSchema
   } for tool in response.tools]
   
   # Add available tools to Claude API call
   claude_params = {
       "model": "claude-3-5-sonnet-20241022",
       "max_tokens": 1000,
       "temperature": 0.7,
       "system": "You are an experienced NBA General Manager making trade decisions...",
       "messages": messages,
       "tools": available_tools
   }
   ```

3. **Tool Execution and Response Processing**
   ```python
   # Process Claude's response and handle tool calls
   for content in response.content:
       if content.type == 'text':
           final_text.append(content.text)
       elif content.type == 'tool_use' and self.mcp_session:
           tool_name = content.name
           tool_args = content.input
           
           # Execute tool call through MCP
           result = await self.mcp_session.call_tool(tool_name, tool_args)
           
           # Continue conversation with tool results
           messages.append({"role": "user", "content": result.content})
           
           # Get next response from Claude
           follow_up = anthropic.messages.create(...)
   ```

## NBA Data Access through MCP

The `trade_mcp_server.py` provides NBA API tools that Claude can use to access real NBA data:

### Player Information
```python
@mcp.tool()
def nba_get_player_info(player_name: str) -> Dict[str, Any]:
    """Get basic information about an NBA player by name."""
    try:
        player_results = players.find_players_by_full_name(player_name)
        # ... process and return player data
    except Exception as e:
        return {"error": f"Error fetching player info: {str(e)}"}
```

### Player Statistics
```python
@mcp.tool()
def nba_get_player_stats(player_id: str, per_mode: str = "PerGame") -> Dict[str, Any]:
    """Get career statistics for an NBA player by ID."""
    try:
        career_stats = playercareerstats.PlayerCareerStats(
            player_id=player_id,
            per_mode36=per_mode
        )
        return career_stats.get_normalized_dict()
    except Exception as e:
        return {"error": f"Error fetching player stats: {str(e)}"}
```

### Trade Analysis
```python
@mcp.tool()
def nba_analyze_trade(team1: TradeParticipant, team2: TradeParticipant) -> Dict[str, Any]:
    """Analyze a potential NBA trade between two teams."""
    try:
        # Calculate trade metrics and return detailed analysis
        # ... calculate values, salary implications, positional fit, etc.
    except Exception as e:
        return {"error": f"Error analyzing trade: {str(e)}"}
```

## Trade Evaluation Process in Detail

When evaluating a trade, Claude considers multiple factors:

1. **Player Value**
   - Stats-based assessment (points, rebounds, assists)
   - Age and developmental trajectory
   - Contract value and length
   - Position scarcity

2. **Team Needs**
   - Current roster composition
   - Positional strengths and weaknesses
   - Immediate vs. future focus

3. **Salary and Cap Implications**
   - Impact on team salary cap
   - Luxury tax considerations
   - Future flexibility

4. **NBA Context**
   - Real player performance data
   - League trends and player comparisons
   - Historical trade precedents

## Running the Simulation

To run the full NBA GM Simulator:

1. **Start the NBA MCP Server**
   ```bash
   cd mcp-client
   python trade_mcp_server.py
   ```

2. **Run the Flask Server**
   ```bash
   cd mcp-client
   python flask_server.py
   ```

3. **Launch the Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

4. **Access the Simulation**
   - Open your browser to http://localhost:3000
   - Select a team to manage
   - Begin exploring rosters and proposing trades

## Future Enhancements

Potential areas for expansion:

1. **Draft Simulation**
   - Prospect generation with realistic attributes
   - Mock drafts and team draft strategies
   - Draft pick trading and valuation

2. **Season Simulation**
   - Game results and season standings
   - Player development and progression
   - Free agency and contract negotiations

3. **Enhanced AI-Powered GMs**
   - More sophisticated decision-making factors
   - Team-specific strategies and biases
   - Memory of past trade interactions

4. **Expanded NBA Data Integration**
   - More detailed player metrics and advanced stats
   - Real-time NBA integration during the season
   - Historical data-based player comparisons

## Conclusion

The NBA GM Simulator provides a sophisticated platform for simulating NBA team management with intelligent AI-powered trade evaluations. The integration of Claude with MCP enables AI agents to utilize real NBA data in their decision-making, creating a more realistic and engaging experience.

The modular architecture allows for easy extension and enhancement, making it a solid foundation for further development of sports management simulation features.