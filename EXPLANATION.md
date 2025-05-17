# NBA GM Simulator: Codebase Architecture & System Overview

---

## 1. Overview

This project is a full-stack NBA General Manager (GM) simulator. It allows users to chat with AI-powered GMs, propose and simulate trades, and manage NBA teams. The system consists of:

- A modern React/Next.js frontend
- A Python Flask backend API
- A set of agent and server modules for trade logic and NBA data
- Integration with the MCP (Multi-Component Protocol) for tool-based AI reasoning
- Data models and league state management

---

## 2. Frontend (`frontend/`)

**Framework:** Next.js (React, TypeScript)

**Key Components:**
- `page.tsx`: Main entry point. Lets users select between "Chat" and "GM" modes, pick a team, and interact with the system.
- `TeamDashboard.tsx`: The core GM interface. Shows roster, salary info, and allows proposing trades or simulating league activity.
- `TradeModal.tsx`: Modal for constructing and submitting trade proposals, including player selection and trade validation.
- `LeagueActivity.tsx`: Displays recent league trade activity.
- `ChatInterface.tsx`: Chat UI for conversing with an AI GM for a selected team.
- `TeamSelector.tsx`, `PlayerCard.tsx`, `TeamLogo.tsx`: UI helpers for team/player selection and display.

**How it works:**
- The frontend communicates with the backend Flask API for all data (rosters, trades, chat, etc.).
- State is managed with React hooks.
- All team/player data, trade proposals, and chat messages are fetched or posted to the backend.
- The UI is styled with Tailwind CSS and is responsive and modern.

---

## 3. Backend API (`mcp-client/flask_server.py`)

**Framework:** Flask (with async support), CORS enabled

**Key Endpoints:**
- `/api/chat/<team>`: Handles chat with the AI GM for a team, using the MCPClient and Anthropic Claude.
- `/api/teams`: Returns all NBA teams.
- `/api/team/select`: Sets the user's managed team.
- `/api/team/roster/<team_abbr>`: Returns a team's roster and salary info.
- `/api/league/activity`: Returns recent trade activity.
- `/api/trade/propose`: Accepts trade proposals and processes them via the GM agent system.
- `/api/trade/respond`: Handles responses to trades (accept, reject, counter).
- `/api/league/simulate`: Simulates league activity (trades, etc.).

**How it works:**
- The Flask server acts as the main API for the frontend.
- It manages league state, trade logic, and delegates chat/trade reasoning to the agent system and MCP tools.
- Uses `GMAgentManager` to coordinate team agents and league state.

---

## 4. GM Agent System (`mcp-client/gm_agent.py`)

**Key Classes:**
- `GMAgent`: Represents an AI GM for a team. Handles trade evaluation, player valuation, and trade proposal logic.
- `GMAgentManager`: Manages all team agents, user team selection, and trade processing.

**How it works:**
- Each team has an agent that can evaluate trades, propose counters, and simulate trading behavior.
- Player and trade evaluation considers stats, salary, contract, team needs, and cap implications.
- Agents can interact with the MCP server for advanced reasoning and data.

---

## 5. Data Models & League State (`mcp-client/models.py`)

**Key Models:**
- `Player`, `Team`, `DraftPick`: Represent NBA entities.
- `Trade`, `TradeProposal`, `TradeResponse`: Represent trade logic and proposals.
- `LeagueState`: Holds all teams, trades, and provides methods for saving/loading state, executing trades, etc.

**How it works:**
- The league state is stored in a JSON file (`league_state.json`).
- Helper functions generate sample data for all 30 NBA teams.
- All trade and roster logic is built on these models.

---

## 6. MCP Servers

### a. Trade MCP Server (`mcp-client/trade_mcp_server.py`)
- Provides MCP tools for player info, stats, team info, and trade analysis.
- Wraps NBA API endpoints and exposes them as callable tools for agents.

### b. NBA MCP Server (`nba-mcp-server/nba_server.py`)
- More comprehensive server with tools for live data (scoreboard, boxscore, play-by-play), player/team stats, standings, etc.
- Used for advanced data retrieval and reasoning.

---

## 7. MCP Client (`mcp-client/client.py`)

- Handles communication with MCP servers.
- Manages tool calls, system prompts, and conversation flow for AI GMs.
- Integrates with Anthropic Claude for natural language reasoning and tool use.

---

## 8. Testing (`mcp-client/test_trades.py`)

- Contains async tests for league initialization, trade acceptance/rejection, counter-offers, and agent-to-agent trading.
- Demonstrates and validates the core trade logic and agent behavior.

---

## 9. League State & Data

- The league state is initialized with all 30 NBA teams, each with a roster of sample players and draft picks.
- All player/team data is stored in `league_state.json` and manipulated via the backend and agent system.

---

## 10. Summary of Flow

1. **User interacts with the frontend** (selects team, chats, proposes trades).
2. **Frontend calls Flask API** for all actions.
3. **Flask API manages league state** and delegates logic to the GM agent system.
4. **GM agents use MCP tools and AI** to evaluate trades, chat, and simulate league activity.
5. **All data is persisted** in the league state JSON file.

--- 