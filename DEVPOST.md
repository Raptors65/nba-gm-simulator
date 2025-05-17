# NBA GM Simulator with Claude AI

## Elevator Pitch
An NBA General Manager simulation that uses Claude AI and MCP to provide realistic trade evaluations based on actual NBA statistics and data.

## About the Project

### Inspiration
We wanted to build a fun, interactive application that demonstrates the power of AI assistants with external tools. The NBA trade deadline is always exciting, and we wanted to recreate that experience in a simulator that uses real NBA data and Claude's reasoning capabilities to evaluate trades realistically.

### What it does
NBA GM Simulator lets users:
- Take on the role of an NBA General Manager
- Browse current team rosters with up-to-date statistics and salary information
- Propose trades with other teams in the league
- Receive AI-powered evaluations of trade proposals that consider multiple factors including player stats, team needs, salary cap implications, and strategic fit
- Negotiate with AI-controlled GMs who can accept, reject, or counter offers
- Simulate league-wide trade activity to see what other teams are doing

### How we built it
The application consists of three main components:

1. **Frontend**: A React/Next.js application with Tailwind CSS that provides a modern, responsive interface for users to interact with their team and propose trades.

2. **Backend Server**: A Flask server that manages the simulation state, handles trade proposals, and communicates with the AI agent for trade evaluations.

3. **AI Integration**:
   - Created a Model Context Protocol (MCP) server that gives Claude access to NBA player and team data
   - Implemented custom tools for player analysis, team evaluation, and trade assessment
   - Developed context-aware prompting that helps Claude understand the nuances of NBA trades

### Challenges we ran into
- **Realistic Trade Logic**: Creating a system that evaluates trades similar to how real NBA GMs would think required careful consideration of many factors.
- **MCP Integration**: Initially, we struggled with the correct approach to integrate MCP with Claude. We had to revise our implementation to allow Claude to determine when to use the NBA data tools.
- **UI/UX Design**: Presenting complex NBA data and trade mechanics in an intuitive interface required several iterations.
- **Contrast Issues**: We had to carefully adjust text contrast throughout the application to ensure readability and accessibility.

### Accomplishments we're proud of
- Successfully implementing a complete trade proposal and evaluation system that considers multiple factors
- Creating a responsive, intuitive UI that showcases player stats and team information clearly
- Integrating Claude with MCP to leverage both AI reasoning and real NBA data
- Building an engaging simulation that feels authentic to NBA basketball

### What we learned
- How to effectively use Model Context Protocol to extend Claude's capabilities with external tools
- Techniques for designing effective AI prompts that produce consistent, high-quality responses
- Approaches for balancing AI agency with user control in interactive applications
- Best practices for building accessible UIs with proper text contrast

### What's next
- Add draft pick trading capabilities
- Implement multi-season simulation with player development
- Create a "franchise mode" where users can build a team over multiple seasons
- Add more advanced statistics and player evaluation metrics
- Implement mobile-responsive design for on-the-go trade proposals

## Built with
Python, Flask, React, Next.js, TypeScript, TailwindCSS, Anthropic Claude API, Model Context Protocol (MCP), NBA API