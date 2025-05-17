import asyncio
import json
import os
import sys
from datetime import datetime
from models import LeagueState, Trade, TradeProposal, initialize_league
from gm_agent import GMAgentManager

# Initialize the league state path
LEAGUE_STATE_PATH = "league_state.json"

async def test_league_initialization():
    """Test the league initialization process"""
    print("\n=== Testing League Initialization ===")
    
    # Initialize league
    if os.path.exists(LEAGUE_STATE_PATH):
        os.remove(LEAGUE_STATE_PATH)
    
    league = initialize_league(LEAGUE_STATE_PATH)
    
    # Verify league state
    assert league is not None, "League initialization failed"
    assert len(league.teams) == 30, f"Expected 30 teams, got {len(league.teams)}"
    
    # Verify team data
    for abbr, team in league.teams.items():
        assert len(team.players) > 0, f"Team {abbr} has no players"
        assert len(team.draft_picks) > 0, f"Team {abbr} has no draft picks"
    
    print("✅ League initialization successful")
    return league

async def test_trade_proposal_acceptance():
    """Test a trade proposal that should be accepted"""
    print("\n=== Testing Trade Proposal Acceptance ===")
    
    # Initialize manager
    manager = GMAgentManager(LEAGUE_STATE_PATH)
    
    # Select user team
    user_team = "LAL"  # Lakers
    manager.select_user_team(user_team)
    
    # Get a trade partner
    trade_partner = "BOS"  # Celtics
    
    # Get players from both teams
    lal_roster = manager.get_team_roster(user_team)
    bos_roster = manager.get_team_roster(trade_partner)
    
    # Select players for the trade (lowest value players to increase acceptance chances)
    lal_players = lal_roster["players"][-2:]  # Last two players (likely lowest value)
    bos_players = bos_roster["players"][-1:]  # Last player (likely lowest value)
    
    # Create trade that should be accepted (giving more than receiving)
    trade = Trade(
        team1=user_team,
        team2=trade_partner,
        team1_players=[p["id"] for p in lal_players],
        team2_players=[p["id"] for p in bos_players],
        proposed_by="user"
    )
    
    # Create proposal
    proposal = TradeProposal(
        trade=trade,
        message="Test trade proposal for acceptance"
    )
    
    # Submit proposal
    print(f"Proposing trade: {len(lal_players)} LAL players for {len(bos_players)} BOS players")
    response = await manager.process_user_trade_proposal(proposal)
    
    print(f"Trade response: {response.status} - {response.message}")
    
    return response

async def test_trade_proposal_rejection():
    """Test a trade proposal that should be rejected"""
    print("\n=== Testing Trade Proposal Rejection ===")
    
    # Initialize manager
    manager = GMAgentManager(LEAGUE_STATE_PATH)
    
    # Select user team
    user_team = "LAL"  # Lakers
    manager.select_user_team(user_team)
    
    # Get a trade partner
    trade_partner = "MIA"  # Heat
    
    # Get players from both teams
    lal_roster = manager.get_team_roster(user_team)
    mia_roster = manager.get_team_roster(trade_partner)
    
    # Select players for the trade (create an imbalanced trade)
    lal_players = lal_roster["players"][-1:]  # Last player (lowest value)
    mia_players = mia_roster["players"][:2]   # First two players (likely highest value)
    
    # Create trade that should be rejected (asking for too much)
    trade = Trade(
        team1=user_team,
        team2=trade_partner,
        team1_players=[p["id"] for p in lal_players],
        team2_players=[p["id"] for p in mia_players],
        proposed_by="user"
    )
    
    # Create proposal
    proposal = TradeProposal(
        trade=trade,
        message="Test trade proposal for rejection"
    )
    
    # Submit proposal
    print(f"Proposing imbalanced trade: {len(lal_players)} LAL players for {len(mia_players)} MIA players")
    response = await manager.process_user_trade_proposal(proposal)
    
    print(f"Trade response: {response.status} - {response.message}")
    
    return response

async def test_trade_counter_offer():
    """Test a trade proposal that should result in a counter offer"""
    print("\n=== Testing Trade Counter Offer ===")
    
    # Initialize manager
    manager = GMAgentManager(LEAGUE_STATE_PATH)
    
    # Select user team
    user_team = "LAL"  # Lakers
    manager.select_user_team(user_team)
    
    # Get a trade partner
    trade_partner = "GSW"  # Warriors
    
    # Get players from both teams
    lal_roster = manager.get_team_roster(user_team)
    gsw_roster = manager.get_team_roster(trade_partner)
    
    # Select players for the trade (medium value on both sides, but slightly imbalanced)
    lal_players = lal_roster["players"][5:6]   # Middle-tier player
    gsw_players = gsw_roster["players"][3:4]   # Slightly better player
    
    # Create trade that could be countered (slightly imbalanced)
    trade = Trade(
        team1=user_team,
        team2=trade_partner,
        team1_players=[p["id"] for p in lal_players],
        team2_players=[p["id"] for p in gsw_players],
        proposed_by="user"
    )
    
    # Create proposal
    proposal = TradeProposal(
        trade=trade,
        message="Test trade proposal for counter offer"
    )
    
    # Submit proposal
    print(f"Proposing slightly imbalanced trade: {len(lal_players)} LAL players for {len(gsw_players)} GSW players")
    response = await manager.process_user_trade_proposal(proposal)
    
    print(f"Trade response: {response.status} - {response.message}")
    
    if response.status == "countered" and response.counter_trade:
        print("Received counter offer!")
        team1_players = response.counter_trade.team1_players
        team2_players = response.counter_trade.team2_players
        print(f"Counter trade: {len(team1_players)} {response.counter_trade.team1} players for {len(team2_players)} {response.counter_trade.team2} players")
    
    return response

async def test_agent_to_agent_trades():
    """Test agent-to-agent trading"""
    print("\n=== Testing Agent-to-Agent Trading ===")
    
    # Initialize manager
    manager = GMAgentManager(LEAGUE_STATE_PATH)
    
    # Select user team
    user_team = "LAL"  # Lakers
    manager.select_user_team(user_team)
    
    # Run a few agent trade cycles
    print("Running 3 agent trade cycles...")
    
    for i in range(3):
        print(f"\nCycle {i+1}:")
        results = await manager.run_agent_trade_cycle()
        
        if results:
            for idx, result in enumerate(results):
                proposal = result["proposal"]
                response = result["response"]
                
                print(f"Trade {idx+1}: {proposal.trade.team1} → {proposal.trade.team2}")
                print(f"Status: {response.status}")
                print(f"Message: {response.message[:50]}..." if len(response.message) > 50 else f"Message: {response.message}")
        else:
            print("No agent trades in this cycle")
    
    # Check league activity
    activity = manager.get_league_activity(5)
    print(f"\nRecent League Activity (last {len(activity)} events):")
    
    for item in activity:
        print(f"{item['team1']['abbr']} ↔️ {item['team2']['abbr']} ({item['status']})")
    
    return activity

async def main():
    """Run all tests"""
    print("=== Starting Trade System Tests ===\n")
    
    try:
        # Initialize league
        await test_league_initialization()
        
        # Test trade acceptance
        accept_response = await test_trade_proposal_acceptance()
        
        # Test trade rejection
        reject_response = await test_trade_proposal_rejection()
        
        # Test counter offer
        counter_response = await test_trade_counter_offer()
        
        # Test agent-to-agent trades
        activity = await test_agent_to_agent_trades()
        
        print("\n=== Test Summary ===")
        print(f"Trade Acceptance Test: {'✅ Passed' if accept_response.status == 'accepted' else '❌ Failed'}")
        print(f"Trade Rejection Test: {'✅ Passed' if reject_response.status == 'rejected' else '❌ Failed'}")
        print(f"Trade Counter Test: {'✅ Passed' if counter_response.status == 'countered' else '❌ Failed'}")
        print(f"Agent-to-Agent Test: {'✅ Passed' if activity else '❌ Failed'}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Testing Complete ===")

if __name__ == "__main__":
    asyncio.run(main())