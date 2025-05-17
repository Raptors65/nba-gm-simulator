"""
NBA Trade MCP Server

This server provides access to NBA data via MCP tools to help with trade evaluations.
It acts as a simple wrapper around the NBA API for use with the GM agent.
"""

from mcp.server.fastmcp import FastMCP
import time
import signal
import sys
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats

# Handle SIGINT (Ctrl+C) gracefully
def signal_handler(sig, frame):
    print("Shutting down NBA trade MCP server gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Create an MCP server with increased timeout
mcp = FastMCP(
    name="nba_trade_mcp_server",
    timeout=30  # Increase timeout to 30 seconds
)

# -------------------------------------------------------------
# Player Info Tool
# -------------------------------------------------------------

class PlayerInfoInput(BaseModel):
    player_name: str = Field(..., description="Name of the NBA player to search for")

@mcp.tool()
def nba_get_player_info(player_name: str) -> Dict[str, Any]:
    """Get basic information about an NBA player by name.
    
    This tool searches for an NBA player by name and returns basic information
    about the player if found.
    
    Args:
        player_name: Name of the NBA player to search for
    
    Returns:
        A dictionary containing information about the player, including their ID,
        name, team, and active status. If no player is found or multiple players
        match the name, appropriate error information is returned.
    """
    try:
        # Search for players matching the name
        player_results = players.find_players_by_full_name(player_name)
        
        if not player_results:
            return {"error": f"No NBA player found with name '{player_name}'"}
        
        if len(player_results) > 1:
            return {
                "warning": "Multiple players found",
                "players": player_results
            }
        
        player_info = player_results[0]
        player_id = player_info['id']
        
        # Fetch detailed player info if active
        if player_info['is_active']:
            detailed_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            player_data = detailed_info.get_normalized_dict()
            return {
                "id": player_id,
                "name": player_info['full_name'],
                "team": player_data.get('CommonPlayerInfo', [{}])[0].get('TEAM_NAME', 'Unknown'),
                "active": True,
                "details": player_data
            }
        else:
            return {
                "id": player_id,
                "name": player_info['full_name'], 
                "active": False,
                "message": "Player is not active"
            }
    except Exception as e:
        return {"error": f"Error fetching player info: {str(e)}"}

# -------------------------------------------------------------
# Player Stats Tool
# -------------------------------------------------------------

class PlayerStatsInput(BaseModel):
    player_id: str = Field(..., description="The NBA player ID")
    per_mode: str = Field(default="PerGame", description="Per game or total stats (e.g., 'PerGame', 'Totals')")

@mcp.tool()
def nba_get_player_stats(player_id: str, per_mode: str = "PerGame") -> Dict[str, Any]:
    """Get career statistics for an NBA player by ID.
    
    This tool retrieves comprehensive career statistics for an NBA player
    based on their ID.
    
    Args:
        player_id: The NBA player ID
        per_mode: Stats calculation mode (PerGame, Totals, etc.)
    
    Returns:
        A dictionary containing the player's career statistics, including
        regular season and playoff stats.
    """
    try:
        career_stats = playercareerstats.PlayerCareerStats(
            player_id=player_id,
            per_mode36=per_mode
        )
        
        return career_stats.get_normalized_dict()
    except Exception as e:
        return {"error": f"Error fetching player stats: {str(e)}"}

# -------------------------------------------------------------
# Team Info Tool
# -------------------------------------------------------------

class TeamInfoInput(BaseModel):
    team_name: str = Field(..., description="Name of the NBA team to search for")

@mcp.tool()
def nba_get_team_info(team_name: str) -> Dict[str, Any]:
    """Get information about an NBA team by name.
    
    This tool searches for an NBA team by name and returns information about
    the team if found.
    
    Args:
        team_name: Name of the NBA team to search for
    
    Returns:
        A dictionary containing information about the team, including their ID,
        name, city, and abbreviation. If no team is found or multiple teams
        match the name, appropriate error information is returned.
    """
    try:
        # Search for teams matching the name
        team_results = teams.find_teams_by_full_name(team_name)
        
        if not team_results:
            return {"error": f"No NBA team found with name '{team_name}'"}
        
        if len(team_results) > 1:
            return {
                "warning": "Multiple teams found",
                "teams": team_results
            }
        
        return team_results[0]
    except Exception as e:
        return {"error": f"Error fetching team info: {str(e)}"}

# -------------------------------------------------------------
# Trade Analysis Tool
# -------------------------------------------------------------

class PlayerBasicInfo(BaseModel):
    id: Optional[str] = None
    name: str
    position: str
    age: int
    stats: Dict[str, float] = Field(default_factory=dict)
    salary: float

class TradeParticipant(BaseModel):
    team_name: str
    players: List[PlayerBasicInfo]

class TradeAnalysisInput(BaseModel):
    team1: TradeParticipant
    team2: TradeParticipant

@mcp.tool()
def nba_analyze_trade(team1: TradeParticipant, team2: TradeParticipant) -> Dict[str, Any]:
    """Analyze a potential NBA trade between two teams.
    
    This tool provides a basic analysis of a potential trade between two NBA teams,
    including player value comparisons and salary implications.
    
    Args:
        team1: First team in the trade with list of players
        team2: Second team in the trade with list of players
    
    Returns:
        A dictionary containing analysis of the trade from both teams' perspectives.
    """
    try:
        # Calculate basic trade metrics
        team1_outgoing_salary = sum(p.salary for p in team1.players)
        team2_outgoing_salary = sum(p.salary for p in team2.players)
        
        # Calculate basic player value
        team1_value = sum(_simple_player_value(p) for p in team1.players)
        team2_value = sum(_simple_player_value(p) for p in team2.players)
        
        # Get player names for easy reference
        team1_players = [p.name for p in team1.players]
        team2_players = [p.name for p in team2.players]
        
        # Analyze positions being traded
        team1_positions = {}
        for player in team1.players:
            team1_positions[player.position] = team1_positions.get(player.position, 0) + 1
            
        team2_positions = {}
        for player in team2.players:
            team2_positions[player.position] = team2_positions.get(player.position, 0) + 1
        
        return {
            "trade_summary": {
                "team1": {
                    "name": team1.team_name,
                    "players": team1_players,
                    "outgoing_salary": team1_outgoing_salary,
                    "incoming_salary": team2_outgoing_salary,
                    "salary_difference": team2_outgoing_salary - team1_outgoing_salary,
                    "players_value": team1_value,
                    "positions": team1_positions
                },
                "team2": {
                    "name": team2.team_name,
                    "players": team2_players,
                    "outgoing_salary": team2_outgoing_salary,
                    "incoming_salary": team1_outgoing_salary,
                    "salary_difference": team1_outgoing_salary - team2_outgoing_salary,
                    "players_value": team2_value,
                    "positions": team2_positions
                },
                "value_difference": {
                    "team1_perspective": team2_value - team1_value,
                    "team2_perspective": team1_value - team2_value
                }
            }
        }
    except Exception as e:
        return {"error": f"Error analyzing trade: {str(e)}"}

# -------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------

def _simple_player_value(player: PlayerBasicInfo) -> float:
    """Calculate a simple player value based on stats"""
    # Basic value calculation based on available stats
    ppg = player.stats.get("ppg", 0)
    rpg = player.stats.get("rpg", 0)
    apg = player.stats.get("apg", 0)
    
    # Simple value metric
    value = ppg + (0.7 * rpg) + (0.7 * apg)
    
    # Adjust slightly for age (peak value around age 27)
    age_factor = 1.0 - (abs(27 - player.age) * 0.02)
    
    return value * age_factor

# -------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------

if __name__ == "__main__":
    try:
        print("Starting NBA Trade MCP server")
        print(f"Current working directory: {os.getcwd()}", file=sys.stderr)
        mcp.run()
    except Exception as e:
        print(f"Error: {e}")
        # Sleep before exiting to give time for error logs
        time.sleep(5)