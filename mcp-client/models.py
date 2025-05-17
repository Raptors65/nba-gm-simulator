from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime

class Player(BaseModel):
    id: str
    name: str
    position: str
    age: int
    height: str
    weight: int
    salary: float
    contract_years: int
    stats: Dict[str, float] = Field(default_factory=dict)
    
class DraftPick(BaseModel):
    year: int
    round: int
    original_team: str
    protected: bool = False
    protection_details: Optional[str] = None
    
class Team(BaseModel):
    id: str
    name: str
    abbreviation: str
    city: str
    conference: str
    division: str
    players: List[Player]
    draft_picks: List[DraftPick]
    salary_cap: float = 123000000  # Default 2023-24 NBA salary cap
    luxury_tax: float = 150000000  # Default 2023-24 NBA luxury tax threshold
    
    def total_salary(self) -> float:
        return sum(player.salary for player in self.players)
    
    def is_over_cap(self) -> bool:
        return self.total_salary() > self.salary_cap
    
    def is_over_luxury_tax(self) -> bool:
        return self.total_salary() > self.luxury_tax
    
    def available_cap_space(self) -> float:
        if self.is_over_cap():
            return 0
        return self.salary_cap - self.total_salary()

class Trade(BaseModel):
    id: str = Field(default_factory=lambda: f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    team1: str  # Team abbreviation
    team2: str  # Team abbreviation
    team1_players: List[str] = Field(default_factory=list)  # Player IDs
    team2_players: List[str] = Field(default_factory=list)  # Player IDs
    team1_picks: List[Dict[str, Any]] = Field(default_factory=list)  # Draft pick details
    team2_picks: List[Dict[str, Any]] = Field(default_factory=list)  # Draft pick details
    status: str = "proposed"  # proposed, accepted, rejected, countered
    proposed_by: str  # Team abbreviation or "user"
    timestamp: datetime = Field(default_factory=datetime.now)
    counter_trade_id: Optional[str] = None
    
class TradeProposal(BaseModel):
    trade: Trade
    message: str

class TradeResponse(BaseModel):
    trade_id: str
    status: str  # accepted, rejected, countered
    message: str
    counter_trade: Optional[Trade] = None

class LeagueState(BaseModel):
    teams: Dict[str, Team]
    trades: List[Trade] = Field(default_factory=list)
    
    def save(self, filepath: str):
        """Save the league state to a JSON file"""
        # Convert to dict and handle datetime serialization
        data = self.model_dump()
        for trade in data['trades']:
            trade['timestamp'] = trade['timestamp'].isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> "LeagueState":
        """Load the league state from a JSON file"""
        if not os.path.exists(filepath):
            return cls(teams={})
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Handle datetime deserialization
        for trade in data['trades']:
            trade['timestamp'] = datetime.fromisoformat(trade['timestamp'])
        
        return cls.model_validate(data)
    
    def get_team_by_abbreviation(self, abbreviation: str) -> Optional[Team]:
        """Get a team by its abbreviation"""
        for team in self.teams.values():
            if team.abbreviation == abbreviation:
                return team
        return None
    
    def get_player_by_id(self, player_id: str) -> Optional[tuple[Player, Team]]:
        """Get a player by ID and return the player and their team"""
        for team in self.teams.values():
            for player in team.players:
                if player.id == player_id:
                    return (player, team)
        return None
    
    def execute_trade(self, trade: Trade) -> bool:
        """Execute a trade between two teams"""
        team1 = self.get_team_by_abbreviation(trade.team1)
        team2 = self.get_team_by_abbreviation(trade.team2)
        
        if not team1 or not team2:
            return False
        
        # Move players from team1 to team2
        team1_players_to_trade = []
        for player_id in trade.team1_players:
            for i, player in enumerate(team1.players):
                if player.id == player_id:
                    team1_players_to_trade.append(player)
                    break
        
        # Move players from team2 to team1
        team2_players_to_trade = []
        for player_id in trade.team2_players:
            for i, player in enumerate(team2.players):
                if player.id == player_id:
                    team2_players_to_trade.append(player)
                    break
        
        # Remove players from original teams
        team1.players = [p for p in team1.players if p.id not in trade.team1_players]
        team2.players = [p for p in team2.players if p.id not in trade.team2_players]
        
        # Add players to new teams
        team1.players.extend(team2_players_to_trade)
        team2.players.extend(team1_players_to_trade)
        
        # TODO: Handle draft picks exchange
        
        # Mark trade as executed
        for i, existing_trade in enumerate(self.trades):
            if existing_trade.id == trade.id:
                self.trades[i].status = "accepted"
                break
        
        # Add to trades list if not already there
        if trade.id not in [t.id for t in self.trades]:
            trade.status = "accepted"
            self.trades.append(trade)
        
        return True

# Helper functions to generate sample data
def generate_sample_players(team_abbr: str, count: int = 15) -> List[Player]:
    """Generate sample players for a team"""
    positions = ["PG", "SG", "SF", "PF", "C"]
    sample_players = []
    
    for i in range(1, count + 1):
        position_index = (i - 1) % 5
        salary_multiplier = 1.5 if i <= 5 else 0.8 if i <= 10 else 0.5
        
        player = Player(
            id=f"{team_abbr}_{i}",
            name=f"{team_abbr} Player {i}",
            position=positions[position_index],
            age=22 + (i % 10),
            height=f"{6 + (i % 3)}'{i % 12}\"",
            weight=180 + (i * 5) % 70,
            salary=1_000_000 * (15 - i) * salary_multiplier,
            contract_years=1 + (i % 5),
            stats={
                "ppg": 10 + (i % 20),
                "rpg": 3 + (i % 10),
                "apg": 2 + (i % 8),
                "spg": 0.5 + (i % 2),
                "bpg": 0.3 + (i % 3),
                "fg_pct": 0.4 + (i % 10) / 100,
                "fg3_pct": 0.3 + (i % 15) / 100
            }
        )
        sample_players.append(player)
    
    return sample_players

def generate_sample_draft_picks(team_abbr: str) -> List[DraftPick]:
    """Generate sample draft picks for a team"""
    current_year = datetime.now().year
    return [
        DraftPick(year=current_year + 1, round=1, original_team=team_abbr),
        DraftPick(year=current_year + 1, round=2, original_team=team_abbr),
        DraftPick(year=current_year + 2, round=1, original_team=team_abbr),
        DraftPick(year=current_year + 2, round=2, original_team=team_abbr),
        DraftPick(year=current_year + 3, round=1, original_team=team_abbr),
    ]

def generate_sample_league() -> LeagueState:
    """Generate a sample league with all 30 NBA teams"""
    teams_data = [
        {"id": "1", "name": "Hawks", "abbreviation": "ATL", "city": "Atlanta", "conference": "East", "division": "Southeast"},
        {"id": "2", "name": "Celtics", "abbreviation": "BOS", "city": "Boston", "conference": "East", "division": "Atlantic"},
        {"id": "3", "name": "Nets", "abbreviation": "BKN", "city": "Brooklyn", "conference": "East", "division": "Atlantic"},
        {"id": "4", "name": "Hornets", "abbreviation": "CHA", "city": "Charlotte", "conference": "East", "division": "Southeast"},
        {"id": "5", "name": "Bulls", "abbreviation": "CHI", "city": "Chicago", "conference": "East", "division": "Central"},
        {"id": "6", "name": "Cavaliers", "abbreviation": "CLE", "city": "Cleveland", "conference": "East", "division": "Central"},
        {"id": "7", "name": "Mavericks", "abbreviation": "DAL", "city": "Dallas", "conference": "West", "division": "Southwest"},
        {"id": "8", "name": "Nuggets", "abbreviation": "DEN", "city": "Denver", "conference": "West", "division": "Northwest"},
        {"id": "9", "name": "Pistons", "abbreviation": "DET", "city": "Detroit", "conference": "East", "division": "Central"},
        {"id": "10", "name": "Warriors", "abbreviation": "GSW", "city": "Golden State", "conference": "West", "division": "Pacific"},
        {"id": "11", "name": "Rockets", "abbreviation": "HOU", "city": "Houston", "conference": "West", "division": "Southwest"},
        {"id": "12", "name": "Pacers", "abbreviation": "IND", "city": "Indiana", "conference": "East", "division": "Central"},
        {"id": "13", "name": "Clippers", "abbreviation": "LAC", "city": "Los Angeles", "conference": "West", "division": "Pacific"},
        {"id": "14", "name": "Lakers", "abbreviation": "LAL", "city": "Los Angeles", "conference": "West", "division": "Pacific"},
        {"id": "15", "name": "Grizzlies", "abbreviation": "MEM", "city": "Memphis", "conference": "West", "division": "Southwest"},
        {"id": "16", "name": "Heat", "abbreviation": "MIA", "city": "Miami", "conference": "East", "division": "Southeast"},
        {"id": "17", "name": "Bucks", "abbreviation": "MIL", "city": "Milwaukee", "conference": "East", "division": "Central"},
        {"id": "18", "name": "Timberwolves", "abbreviation": "MIN", "city": "Minnesota", "conference": "West", "division": "Northwest"},
        {"id": "19", "name": "Pelicans", "abbreviation": "NOP", "city": "New Orleans", "conference": "West", "division": "Southwest"},
        {"id": "20", "name": "Knicks", "abbreviation": "NYK", "city": "New York", "conference": "East", "division": "Atlantic"},
        {"id": "21", "name": "Thunder", "abbreviation": "OKC", "city": "Oklahoma City", "conference": "West", "division": "Northwest"},
        {"id": "22", "name": "Magic", "abbreviation": "ORL", "city": "Orlando", "conference": "East", "division": "Southeast"},
        {"id": "23", "name": "76ers", "abbreviation": "PHI", "city": "Philadelphia", "conference": "East", "division": "Atlantic"},
        {"id": "24", "name": "Suns", "abbreviation": "PHX", "city": "Phoenix", "conference": "West", "division": "Pacific"},
        {"id": "25", "name": "Trail Blazers", "abbreviation": "POR", "city": "Portland", "conference": "West", "division": "Northwest"},
        {"id": "26", "name": "Kings", "abbreviation": "SAC", "city": "Sacramento", "conference": "West", "division": "Pacific"},
        {"id": "27", "name": "Spurs", "abbreviation": "SAS", "city": "San Antonio", "conference": "West", "division": "Southwest"},
        {"id": "28", "name": "Raptors", "abbreviation": "TOR", "city": "Toronto", "conference": "East", "division": "Atlantic"},
        {"id": "29", "name": "Jazz", "abbreviation": "UTA", "city": "Utah", "conference": "West", "division": "Northwest"},
        {"id": "30", "name": "Wizards", "abbreviation": "WAS", "city": "Washington", "conference": "East", "division": "Southeast"}
    ]
    
    teams = {}
    for team_data in teams_data:
        team = Team(
            id=team_data["id"],
            name=team_data["name"],
            abbreviation=team_data["abbreviation"],
            city=team_data["city"],
            conference=team_data["conference"],
            division=team_data["division"],
            players=generate_sample_players(team_data["abbreviation"]),
            draft_picks=generate_sample_draft_picks(team_data["abbreviation"])
        )
        teams[team.abbreviation] = team
    
    return LeagueState(teams=teams)

# Initialize league if needed
def initialize_league(filepath: str = "league_state.json"):
    if not os.path.exists(filepath):
        league = generate_sample_league()
        league.save(filepath)
        return league
    return LeagueState.load(filepath)