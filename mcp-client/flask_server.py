from flask import Flask, request, jsonify
import asyncio
from asgiref.sync import async_to_sync
from client import MCPClient
import atexit
import signal

app = Flask(__name__)
mcp_client = None
loop = None

def cleanup_client():
    if mcp_client and loop:
        loop.run_until_complete(mcp_client.cleanup())

def signal_handler(signum, frame):
    cleanup_client()
    exit(0)

@app.route('/api/chat/<team>', methods=['POST'])
async def chat(team):
    data = request.get_json()
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        result = await client.process_query(data["messages"], team)
    finally:
        await client.cleanup()
    
    return jsonify({"response": result})

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python flask_server.py <path_to_server_script>")
        sys.exit(1)
    
    # Run the Flask server
    app.run(debug=True)
