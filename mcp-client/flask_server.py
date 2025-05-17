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
def chat(team):
    if not mcp_client:
        return jsonify({"error": "MCP client not initialized"}), 500
    
    data = request.get_json()
    if not data or 'messages' not in data:
        return jsonify({"error": "No messages provided"}), 400
    
    try:
        response = async_to_sync(mcp_client.process_query)(data['messages'], team)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def initialize_client(server_script_path):
    global mcp_client, loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    mcp_client = MCPClient()
    loop.run_until_complete(mcp_client.connect_to_server(server_script_path))
    
    # Register cleanup handlers
    atexit.register(cleanup_client)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python flask_server.py <path_to_server_script>")
        sys.exit(1)
    
    # Initialize the MCP client before starting the Flask server
    initialize_client(sys.argv[1])
    
    # Run the Flask server
    app.run(debug=True)
