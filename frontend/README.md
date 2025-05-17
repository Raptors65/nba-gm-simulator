# NBA GM Simulator Frontend

This is a Next.js application that allows users to chat with NBA team General Managers. The application provides a clean interface to select a team and start a conversation with its GM.

## Features

- Team selection interface with all 30 NBA teams
- Real-time chat interface with team GMs
- Responsive design that works on desktop and mobile
- Dark mode support
- Clean, basketball-themed UI

## Prerequisites

- Node.js 18.17.0 or later
- A running backend server (see backend setup below)

## Getting Started

1. Install dependencies:

```bash
npm install
```

2. Run the development server:

```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

## Backend Connection

The frontend is configured to communicate with a Flask backend server running at `http://127.0.0.1:5001`. The backend should implement the following API endpoint:

- `POST /api/chat/<team>` - Accepts messages and returns GM responses

Make sure the backend server is running before trying to chat with GMs.

## Backend Setup

1. Navigate to the backend directory:

```bash
cd ../mcp-client
```

2. Run the Flask server:

```bash
python flask_server.py <path_to_server_script>
```

## Technologies Used

- Next.js
- React
- TypeScript
- Tailwind CSS
- API integration with Flask backend

## Project Structure

- `app/page.tsx` - Main application component
- `app/components/TeamSelector.tsx` - Team selection interface
- `app/components/ChatInterface.tsx` - Chat interface with GMs
- `app/components/TeamLogo.tsx` - Team logo visualization
- `app/globals.css` - Global styles

## Notes

This application was created for the MCP Hackathon. It demonstrates integration between a Next.js frontend and a Python Flask backend using MCP (Multi-agent Communication Protocol).