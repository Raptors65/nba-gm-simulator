# NBA GM Simulator with Claude AI

## Elevator Pitch
An NBA General Manager simulation that uses Claude AI and MCP to provide realistic trade evaluations based on actual NBA statistics and data.

## About the Project

### Inspiration
After the Luka Dončić trade happened, I thought to myself that even an AI agent could do a better job of being the general manager of an NBA team than Nico Harrison. So why not put that to the test?

I also wanted to build a fun, interactive application that demonstrates the power of AI assistants with external tools. The NBA trade deadline is always exciting, and I wanted to recreate that experience in a simulator that uses real NBA data and Claude's reasoning capabilities to evaluate trades realistically.

### What it does
NBA GM Simulator allows the user to take on the role of general manager of 1 of the 30 NBA teams and negotiate trades with 29 AI agents, each of which manages another NBA team. Simultaneously, these 29 agents are negotiating trades with each other. Each of these agents uses MCP to view their current players and their NBA stats through the NBA API, allowing them to make more informed decisions.

Basically, you can:
- Browse current team rosters with up-to-date statistics and salary information
- Propose trades with other teams in the league
- Chat and negotiate with AI-controlled GMs who can accept, reject, or counter offers
- Simulate league-wide trade activity to see what other teams are doing

### How I built it
The application consists of three main components:

1. **Frontend**: A React/Next.js application with Tailwind CSS that provides a modern, responsive interface for users to interact with their team and propose trades.
2. **Backend Server**: A Flask server that manages the simulation state, handles trade proposals, and communicates with the AI agents for trade evaluations.
3. **AI Integration**:
   - Created a Model Context Protocol (MCP) server that gives Claude access to NBA player and team data
   - Implemented custom tools for player analysis, team evaluation, and trade assessment, taking additional factors like salary cap into account

### Challenges I ran into

- **MCP Integration**: This was my first time using MCP—I learned it on my flight here (literally learning on the fly). Initially I struggled with the correct approach to integrate MCP with Claude.
- **UI/UX Design**: Presenting complex NBA data and trade mechanics in an intuitive interface
- **Realistic Trade Logic**: Creating a system that proposes and evaluates trades similar to how real NBA GMs would think

### Accomplishments I'm proud of
- Successfully implementing a complete trade proposal and evaluation system that considers multiple factors
- Creating an intuitive UI that showcases player stats and team information clearly
- Integrating Claude with MCP to leverage both AI reasoning and real NBA data
- Building an engaging simulation that feels reasonably authentic to NBA basketball within a very short timeframe

### What I learned
- How to effectively use Model Context Protocol to extend Claude's capabilities with external tools
- How to have many AI agents communicate among themselves and with the user

### What's next
- Add draft pick trading capabilities
- Implement a multi-season simulation with player development, injuries, etc.
- Create a "franchise mode" where users can build a team over multiple seasons
- Add more advanced statistics and player evaluation metrics

## Built with
Python, Flask, React, Next.js, TypeScript, TailwindCSS, Anthropic Claude API, Model Context Protocol (MCP), NBA API