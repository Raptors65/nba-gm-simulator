from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import sys
import os
import json
from asgiref.sync import async_to_sync
from datetime import datetime
from client import MCPClient
import atexit
import signal
import traceback

# Import GM Agent system
from gm_agent import GMAgentManager
from models import Trade, TradeProposal, TradeResponse

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
mcp_client = None
loop = None
gm_manager = GMAgentManager()

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

# New API endpoints for the trading system

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get list of all NBA teams"""
    teams = []
    for abbr, team in gm_manager.league_state.teams.items():
        teams.append({
            "id": team.id,
            "name": team.name,
            "abbreviation": team.abbreviation,
            "city": team.city,
            "conference": team.conference,
            "division": team.division
        })
    
    return jsonify({"teams": teams})

@app.route('/api/team/select', methods=['POST'])
def select_team():
    """Select a team for the user"""
    data = request.get_json()
    team_abbr = data.get('team')
    
    if not team_abbr or not gm_manager.select_user_team(team_abbr):
        return jsonify({"success": False, "message": "Invalid team selection"})
    
    return jsonify({"success": True, "message": f"Team {team_abbr} selected"})

@app.route('/api/team/roster/<team_abbr>', methods=['GET'])
def get_team_roster(team_abbr):
    """Get a team's roster"""
    roster = gm_manager.get_team_roster(team_abbr)
    return jsonify(roster)

@app.route('/api/league/activity', methods=['GET'])
def get_league_activity():
    """Get recent league activity"""
    limit = request.args.get('limit', default=10, type=int)
    # Ensure there's a user team selected (if not, pick one)
    if not gm_manager.user_team and len(gm_manager.agents) > 0:
        gm_manager.user_team = list(gm_manager.agents.keys())[0]
        print(f"Automatically selected {gm_manager.user_team} as user team for activity")
    
    activity = gm_manager.get_league_activity(limit)
    print(f"Returning {len(activity)} activity items")
    return jsonify({"activity": activity})

@app.route('/api/trade/propose', methods=['POST'])
async def propose_trade():
    """Propose a trade to another team"""
    try:
        data = request.get_json()
        
        # Validate data
        if not data.get('trade'):
            return jsonify({"success": False, "message": "Missing trade data"})
        
        # Create trade object
        trade_data = data['trade']
        
        # Get team abbreviations
        team1 = trade_data.get('team1', '')
        team2 = trade_data.get('team2', '')
        
        # Get players
        team1_players = trade_data.get('team1_players', [])
        team2_players = trade_data.get('team2_players', [])
        
        # Get picks
        team1_picks = trade_data.get('team1_picks', [])
        team2_picks = trade_data.get('team2_picks', [])
        
        # Create trade object
        trade = Trade(
            team1=team1,
            team2=team2,
            team1_players=team1_players,
            team2_players=team2_players,
            team1_picks=team1_picks,
            team2_picks=team2_picks,
            proposed_by="user"
        )
        
        # Create trade proposal
        message = data.get('message', 'Trade proposal from user')
        proposal = TradeProposal(trade=trade, message=message)
        
        # Process trade
        response = await gm_manager.process_user_trade_proposal(proposal)
        
        return jsonify({
            "success": True,
            "trade_id": response.trade_id,
            "status": response.status,
            "message": response.message,
            "counter_trade": response.counter_trade.model_dump() if response.counter_trade else None
        })
    
    except Exception as e:
        print(f"Error in propose_trade: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

@app.route('/api/trade/respond', methods=['POST'])
async def respond_to_trade():
    """Respond to a trade (accept/reject/counter)"""
    try:
        data = request.get_json()
        
        # Validate data
        if not data.get('trade_id') or not data.get('action'):
            return jsonify({"success": False, "message": "Missing trade_id or action"})
        
        trade_id = data['trade_id']
        action = data['action']
        
        # Find the trade
        trade = None
        for t in gm_manager.league_state.trades:
            if t.id == trade_id:
                trade = t
                break
        
        if not trade:
            return jsonify({"success": False, "message": "Trade not found"})
        
        # Process the response
        if action == 'accept':
            # Execute the trade
            success = gm_manager.league_state.execute_trade(trade)
            if success:
                gm_manager.league_state.save(gm_manager.league_state_path)
                return jsonify({"success": True, "message": "Trade accepted"})
            else:
                return jsonify({"success": False, "message": "Failed to execute trade"})
                
        elif action == 'reject':
            # Mark as rejected
            for i, t in enumerate(gm_manager.league_state.trades):
                if t.id == trade_id:
                    gm_manager.league_state.trades[i].status = 'rejected'
                    break
                    
            gm_manager.league_state.save(gm_manager.league_state_path)
            return jsonify({"success": True, "message": "Trade rejected"})
            
        elif action == 'counter':
            # Create counter proposal
            if not data.get('counter_trade'):
                return jsonify({"success": False, "message": "Missing counter trade data"})
                
            counter_data = data['counter_trade']
            
            # Create counter trade
            counter_trade = Trade(
                team1=counter_data.get('team1', ''),
                team2=counter_data.get('team2', ''),
                team1_players=counter_data.get('team1_players', []),
                team2_players=counter_data.get('team2_players', []),
                team1_picks=counter_data.get('team1_picks', []),
                team2_picks=counter_data.get('team2_picks', []),
                proposed_by="user",
                counter_trade_id=trade_id
            )
            
            # Add to league state
            gm_manager.league_state.trades.append(counter_trade)
            
            # Mark original trade as countered
            for i, t in enumerate(gm_manager.league_state.trades):
                if t.id == trade_id:
                    gm_manager.league_state.trades[i].status = 'countered'
                    break
                    
            gm_manager.league_state.save(gm_manager.league_state_path)
            
            # Process counter trade
            message = data.get('message', 'Counter proposal from user')
            proposal = TradeProposal(trade=counter_trade, message=message)
            
            target_team = counter_trade.team2 if counter_trade.team1 == gm_manager.user_team else counter_trade.team1
            
            # Let the target team's agent evaluate
            if target_team in gm_manager.agents:
                response = await gm_manager.agents[target_team].respond_to_trade(counter_trade)
                
                # If accepted, execute the trade
                if response.status == "accepted":
                    gm_manager.league_state.execute_trade(counter_trade)
                    gm_manager.league_state.save(gm_manager.league_state_path)
                
                return jsonify({
                    "success": True,
                    "trade_id": response.trade_id,
                    "status": response.status,
                    "message": response.message,
                    "counter_trade": response.counter_trade.model_dump() if response.counter_trade else None
                })
            else:
                return jsonify({"success": False, "message": "Invalid target team"})
        else:
            return jsonify({"success": False, "message": "Invalid action"})
        
    except Exception as e:
        print(f"Error in respond_to_trade: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

@app.route('/api/league/simulate', methods=['POST'])
async def simulate_league():
    """Simulate the league (agent-to-agent trades)"""
    try:
        all_results = []
        
        # Run multiple cycles of agent-to-agent trades to generate more activity
        # for _ in range(3):  # Run 3 cycles each time
        results = await gm_manager.run_agent_trade_cycle()
        all_results.extend(results)
        
        # Format results
        trades = []
        for result in all_results:
            proposal = result["proposal"]
            response = result["response"]
            
            # Get team names for better display
            team1 = gm_manager.league_state.get_team_by_abbreviation(proposal.trade.team1)
            team2 = gm_manager.league_state.get_team_by_abbreviation(proposal.trade.team2)
            team1_name = f"{team1.city} {team1.name}" if team1 else proposal.trade.team1
            team2_name = f"{team2.city} {team2.name}" if team2 else proposal.trade.team2
            
            trades.append({
                "proposal": {
                    "team": proposal.trade.team1,
                    "team_name": team1_name,
                    "target_team": proposal.trade.team2,
                    "target_team_name": team2_name,
                    "message": proposal.message,
                    "trade": proposal.trade.model_dump()
                },
                "response": {
                    "status": response.status,
                    "message": response.message,
                    "trade_id": response.trade_id,
                    "counter_trade": response.counter_trade.model_dump() if response.counter_trade else None
                }
            })
        
        # Get more recent activity to show 
        return jsonify({
            "success": True,
            "trades": trades,
            "activity": gm_manager.get_league_activity(15)  # Show more activity
        })
        
    except Exception as e:
        print(f"Error in simulate_league: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python flask_server.py <path_to_server_script>")
        sys.exit(1)
    
    # Initialize the league state before starting the server
    from models import initialize_league
    initialize_league()
    
    # Run the Flask server
    app.run(debug=True, port=5001)