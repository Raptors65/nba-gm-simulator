# NBA GM Simulator with Multi-Agent Trading

A Next.js and Flask application that allows users to chat with NBA team GMs and simulate a multi-agent trading system where AI-powered GMs autonomously negotiate with each other.

## Project Overview

This project combines:

1. **Chat Interface**: Talk to AI-powered NBA team GMs for insights and strategy
2. **Trading System**: Simulate being a GM and make trades with AI-powered team GMs
3. **Agent-to-Agent Communication**: AI GMs negotiate trades with each other based on team needs and player valuations

## Project Structure

- `/frontend`: Next.js application with UI components
- `/mcp-client`: Python client for MCP and trading system backend
- `/mcp-server`: MCP server for NBA data
- `/nba-mcp-server`: MCP server with NBA API integration

## Features

### Chat Mode

- Select any NBA team and chat with their GM
- Ask about team strategy, players, and insights
- Leverages Claude to generate realistic GM responses

### GM Mode

- Take control of any NBA team as the GM
- View team roster, salary information, and league activity
- Propose trades to other teams
- Receive counter-offers
- Watch AI GMs make trades with each other
- League simulation that progresses the state of teams

## Trading System Architecture

The trading system is built on a multi-agent architecture where each team has an AI agent that:

1. **Evaluates Players**: Considers stats, contract, age, and position
2. **Analyzes Team Needs**: Identifies positional needs and roster holes
3. **Makes Strategic Decisions**: Decides whether to accept, reject, or counter trade offers
4. **Proposes Trades**: Initiates trades with other teams based on needs
5. **Validates Trades**: Ensures trades comply with simplified NBA rules

## Getting Started

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Backend Setup

1. Install dependencies:
```bash
cd mcp-client
pip install -r requirements.txt
```

2. Run the Flask server:
```bash
python flask_server.py ../nba-mcp-server/nba_server.py
```

## How It Works

### Backend Components

- **GMAgent**: AI agent that represents each team's GM
- **LeagueState**: Central data model tracking teams, players and trades
- **Flask Server**: API endpoints for chat and trade functionality

### Frontend Components

- **TeamDashboard**: UI for viewing team roster and league activity
- **TradeModal**: Interface for proposing and responding to trades
- **LeagueActivity**: Feed showing recent trades and negotiations

## Testing

To test the trading system functionality:

```bash
cd mcp-client
python test_trades.py
```

This will run through test scenarios for:
- Trade proposal acceptance
- Trade proposal rejection
- Counter offers
- Agent-to-agent trading

## Future Enhancements

- More sophisticated player valuation algorithms
- Draft pick trading
- Salary cap exceptions
- Three-team trades
- Season simulation
- Win-loss record tracking

## Technologies Used

- **Next.js & React**: Frontend UI
- **TailwindCSS**: Styling
- **Flask**: Backend API
- **Claude AI**: GM conversations and trade evaluations
- **MCP Protocol**: Multi-agent communication
- **NBA API**: Team and player data

## Credits

- NBA data provided by NBA API
- Original MCP server code by obinopaul on GitHub
- Created for the MCP Hackathon