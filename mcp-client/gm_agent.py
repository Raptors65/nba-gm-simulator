import asyncio
import json
import os
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from models import LeagueState, Team, Player, Trade, TradeProposal, TradeResponse
import sys
from contextlib import AsyncExitStack
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from anthropic import Anthropic

# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic client with API key from environment
anthropic = Anthropic()

class GMAgent:
    def __init__(self, team_abbr: str, league_state: LeagueState):
        # MCP session for accessing NBA API tools
        self.mcp_session = None
        self.exit_stack = AsyncExitStack()
        self.team_abbr = team_abbr
        self.league_state = league_state
        self.team = league_state.get_team_by_abbreviation(team_abbr)
        self.pending_trades: List[Trade] = []
        self.last_trade_check = datetime.now()
        self.trading_cool_down = 30  # seconds - reduced to encourage more trades
        
        # Trade strategies and preferences
        self.needs = self._analyze_team_needs()
        
    def _analyze_team_needs(self) -> Dict[str, float]:
        """Analyze team needs based on roster composition"""
        positions = {
            "PG": 0, "SG": 0, "SF": 0, "SF": 0, "PF": 0, "C": 0
        }
        
        # Count players by position
        for player in self.team.players:
            if player.position in positions:
                positions[player.position] += 1
        
        # Calculate needs (lower value = higher need)
        needs = {}
        ideal_counts = {"PG": 2, "SG": 2, "SF": 2, "PF": 2, "C": 2}
        
        for pos, count in positions.items():
            ideal = ideal_counts.get(pos, 2)
            needs[pos] = (count / ideal) if ideal > 0 else 1.0
            
        return needs
    
    def evaluate_player(self, player: Player) -> float:
        """Evaluate a player's value based on stats, salary, and team needs"""
        # Basic value from stats
        ppg = player.stats.get("ppg", 0)
        rpg = player.stats.get("rpg", 0)
        apg = player.stats.get("apg", 0)
        
        # Base value from raw stats
        base_value = ppg * 1.0 + rpg * 0.7 + apg * 0.7
        
        # Adjust for position need
        position_need_factor = 1.0
        if player.position in self.needs:
            # If needs[position] is low, we need this position more
            position_need_factor = 2.0 - self.needs[player.position]
        
        # Age factor (prime years 24-29)
        age_factor = 1.0
        if player.age < 23:
            age_factor = 0.8 + (player.age - 19) * 0.05  # potential upside
        elif 24 <= player.age <= 29:
            age_factor = 1.0  # prime years
        else:
            age_factor = 1.0 - (player.age - 30) * 0.05  # declining value
            
        # Contract factor
        # Shorter contracts are more valuable (flexibility)
        contract_factor = 1.0 - (player.contract_years - 1) * 0.05
        
        # Salary efficiency (value per dollar)
        # Higher value = better efficiency
        salary_million = player.salary / 1_000_000
        if salary_million > 0:
            salary_efficiency = base_value / salary_million
        else:
            salary_efficiency = base_value
            
        # Normalize salary efficiency (0.5 to 1.5)
        normalized_efficiency = min(max(salary_efficiency / 10, 0.5), 1.5)
        
        # Calculate final value
        value = base_value * position_need_factor * age_factor * contract_factor * normalized_efficiency
        
        return value
    
    def evaluate_trade(self, trade: Trade) -> Dict[str, Any]:
        """Evaluate a trade proposal from another team"""
        # Determine which side we're on
        our_side = 1 if trade.team1 == self.team_abbr else 2
        our_players_ids = trade.team1_players if our_side == 1 else trade.team2_players
        their_players_ids = trade.team2_players if our_side == 1 else trade.team1_players
        other_team_abbr = trade.team2 if our_side == 1 else trade.team1
        
        # Get the actual player objects
        our_players = [p for p in self.team.players if p.id in our_players_ids]
        other_team = self.league_state.get_team_by_abbreviation(other_team_abbr)
        their_players = [p for p in other_team.players if p.id in their_players_ids]
        
        # Calculate value of our players in the trade
        our_value = sum(self.evaluate_player(player) for player in our_players)
        
        # Calculate value of their players for our team
        their_value_to_us = sum(self.evaluate_player(player) for player in their_players)
        
        # Calculate salary impact
        our_salary_out = sum(p.salary for p in our_players)
        their_salary_in = sum(p.salary for p in their_players)
        salary_difference = their_salary_in - our_salary_out
        
        # Salary cap and luxury tax considerations
        current_salary = self.team.total_salary()
        new_salary = current_salary - our_salary_out + their_salary_in
        
        # Cap considerations
        cap_status = {
            "current_over_cap": current_salary > self.team.salary_cap,
            "new_over_cap": new_salary > self.team.salary_cap,
            "current_over_tax": current_salary > self.team.luxury_tax,
            "new_over_tax": new_salary > self.team.luxury_tax,
        }
        
        # Evaluate position balance after trade
        new_position_count = {
            "PG": 0, "SG": 0, "SF": 0, "PF": 0, "C": 0
        }
        
        # Count current positions excluding our players in the trade
        for player in self.team.players:
            if player.id not in our_players_ids and player.position in new_position_count:
                new_position_count[player.position] += 1
        
        # Add positions from players we would receive
        for player in their_players:
            if player.position in new_position_count:
                new_position_count[player.position] += 1
        
        # Determine position imbalance
        position_balance = {}
        ideal_counts = {"PG": 2, "SG": 2, "SF": 2, "PF": 2, "C": 2}
        
        for pos, count in new_position_count.items():
            ideal = ideal_counts.get(pos, 2)
            balance = count - ideal
            position_balance[pos] = balance
        
        # Calculate overall trade value
        value_difference = their_value_to_us - our_value
        
        # Adjust for cap implications
        if not cap_status["current_over_tax"] and cap_status["new_over_tax"]:
            value_difference -= 10  # Big penalty for going into tax
        elif cap_status["current_over_tax"] and cap_status["new_over_tax"]:
            if salary_difference > 0:
                value_difference -= salary_difference / 10_000_000  # Penalty for increasing tax bill
            else:
                value_difference += abs(salary_difference) / 10_000_000  # Bonus for reducing tax bill
        
        # Adjust for positional need
        for pos, balance in position_balance.items():
            if balance < 0:  # We're short at this position after trade
                value_difference -= abs(balance) * 5
            elif balance > 1:  # We have too many at this position
                value_difference -= (balance - 1) * 3
        
        # Return detailed evaluation
        return {
            "our_value": our_value,
            "their_value": their_value_to_us,
            "value_difference": value_difference,
            "salary_difference": salary_difference,
            "cap_status": cap_status,
            "position_balance": position_balance,
            "acceptable": value_difference > -5,  # Allow slightly unfavorable trades
            "counter_needed": -10 < value_difference < -5,  # Counter if close but not acceptable
            "reasoning": self._get_trade_reasoning(
                our_players, their_players, value_difference, 
                salary_difference, cap_status, position_balance
            )
        }
    
    def _get_trade_reasoning(
        self, our_players, their_players, value_difference, 
        salary_difference, cap_status, position_balance
    ) -> str:
        """Generate reasoning for a trade evaluation"""
        if value_difference > 10:
            return "This trade is highly favorable for our team, providing significant value."
        elif value_difference > 0:
            return "This trade provides good value for our team."
        elif value_difference > -5:
            return "This trade is close to fair value, with only minor disadvantages."
        elif value_difference > -10:
            return "This trade is slightly unfavorable but could be acceptable with modifications."
        else:
            return "This trade provides insufficient value for our team."
    
    def create_counter_offer(self, original_trade: Trade) -> Optional[Trade]:
        """Create a counter offer to an unfavorable trade"""
        # Determine which side we're on
        our_side = 1 if original_trade.team1 == self.team_abbr else 2
        other_team_abbr = original_trade.team2 if our_side == 1 else original_trade.team1
        other_team = self.league_state.get_team_by_abbreviation(other_team_abbr)
        
        # Copy the original trade
        counter = Trade(
            team1=original_trade.team1,
            team2=original_trade.team2,
            team1_players=original_trade.team1_players.copy(),
            team2_players=original_trade.team2_players.copy(),
            team1_picks=original_trade.team1_picks.copy(),
            team2_picks=original_trade.team2_picks.copy(),
            proposed_by=self.team_abbr,
            counter_trade_id=original_trade.id
        )
        
        # Get our players to trade
        if our_side == 1:
            our_players_ids = counter.team1_players
            their_players_ids = counter.team2_players
        else:
            our_players_ids = counter.team2_players
            their_players_ids = counter.team1_players
        
        # Evaluate their players
        their_players = [p for p in other_team.players if p.id in their_players_ids]
        their_value = sum(self.evaluate_player(player) for player in their_players)
        
        # Find our players not in the trade
        our_available_players = [p for p in self.team.players if p.id not in our_players_ids]
        
        # Sort by value (ascending)
        our_available_players.sort(key=self.evaluate_player)
        
        # Current trade value
        our_players = [p for p in self.team.players if p.id in our_players_ids]
        our_value = sum(self.evaluate_player(player) for player in our_players)
        
        # Target: remove one of our higher-value players or add one of their lower-value players
        if len(our_players_ids) > 0 and random.random() < 0.7:
            # Try removing one of our players from the trade
            our_players_in_trade = sorted([(p, self.evaluate_player(p)) for p in our_players], 
                                         key=lambda x: x[1], reverse=True)
            
            if our_players_in_trade:
                player_to_remove, _ = our_players_in_trade[0]  # Highest value player
                
                # Remove from the right list
                if our_side == 1:
                    counter.team1_players.remove(player_to_remove.id)
                else:
                    counter.team2_players.remove(player_to_remove.id)
        else:
            # Try adding one of their players to the trade
            their_available_players = [p for p in other_team.players if p.id not in their_players_ids]
            
            if their_available_players:
                # Sort by value (to us)
                sorted_players = sorted([(p, self.evaluate_player(p)) for p in their_available_players], 
                                      key=lambda x: x[1], reverse=True)
                
                if sorted_players:
                    # Pick a player in the middle-to-lower range to be reasonable
                    index = min(len(sorted_players) - 1, len(sorted_players) // 3)
                    player_to_add, _ = sorted_players[index]
                    
                    # Add to the right list
                    if our_side == 1:
                        counter.team2_players.append(player_to_add.id)
                    else:
                        counter.team1_players.append(player_to_add.id)
        
        # Check if the counter offer is different
        if ((our_side == 1 and counter.team1_players == original_trade.team1_players and 
             counter.team2_players == original_trade.team2_players) or
            (our_side == 2 and counter.team1_players == original_trade.team1_players and 
             counter.team2_players == original_trade.team2_players)):
            return None  # No changes made
        
        return counter
    
    def generate_trade_proposal(self, target_team_abbr: str) -> Optional[TradeProposal]:
        """Generate a new trade proposal targeting another team"""
        target_team = self.league_state.get_team_by_abbreviation(target_team_abbr)

        print(target_team, file=sys.stderr)
        
        if not target_team:
            return None
        
        # Analyze our needs
        our_needs = self._analyze_team_needs()
        
        # Find positions we need most
        needed_positions = sorted(our_needs.items(), key=lambda x: x[1])
        
        # Start with an empty trade
        trade = Trade(
            team1=self.team_abbr,
            team2=target_team_abbr,
            proposed_by=self.team_abbr
        )
        
        # Find players from target team that match our needs
        target_players = []
        
        # Debug team info
        print(f"Target team: {target_team_abbr}, players: {len(target_team.players)}")
        print(f"Our needs: {our_needs}")
        
        # The 0.8 threshold is too strict - relax it to 1.5
        for position, need_value in needed_positions[:2]:  # Focus on top 2 needs
            print(f"Checking position {position} with need value {need_value}")
            # Accept any position with a need value under 1.5 (instead of 0.8)
            if need_value < 1.5:
                matching_players = [
                    p for p in target_team.players 
                    # Always consider players regardless of our cap space
                    if p.position == position
                ]
                
                print(f"Found {len(matching_players)} matching players for position {position}")
                
                if matching_players:
                    # Sort by our evaluation of their value
                    matching_players.sort(key=self.evaluate_player, reverse=True)
                    # Take best player that fits
                    target_players.append(matching_players[0])
        
        # If no positional needs found, just look for value
        if not target_players:
            print("No positional matches, looking for value")
            # Get any players from their team - don't limit by cap space
            affordable_players = target_team.players
            
            if affordable_players:
                # Sort by value to limit to reasonable players
                sorted_players = sorted(affordable_players, key=self.evaluate_player, reverse=True)
                # Take a player from the middle range (don't take their best player)
                idx = min(len(sorted_players) // 3, len(sorted_players) - 1)
                target_players = [sorted_players[idx]]
                print(f"Selected player by value: {sorted_players[idx].name}")
        
        if not target_players:
            print("no suitable players found", file=sys.stderr)
            return None  # No suitable players found
        
        # Calculate incoming salary
        incoming_salary = sum(p.salary for p in target_players)
        
        # Find players from our team to match salary
        our_players = []
        # Aim for a reasonable match but don't be too strict
        target_outgoing_salary = max(incoming_salary * 0.7, 1000000)  # At least $1M but try for 70% match
        
        print(f"Incoming salary: ${incoming_salary/1000000:.1f}M, Target outgoing: ${target_outgoing_salary/1000000:.1f}M")
        
        # Sort our players by value (ascending)
        our_sorted_players = sorted(self.team.players, key=self.evaluate_player)
        
        # Print our players for debugging
        print(f"Our team has {len(our_sorted_players)} players available")
        
        # Always include at least one player regardless of value
        current_salary = 0
        for player in our_sorted_players:
            # Skip super high value players but be more generous with threshold
            if self.evaluate_player(player) > 50:  # Increased from 30 to 50
                continue
                
            our_players.append(player)
            current_salary += player.salary
            print(f"Adding {player.name} with salary ${player.salary/1000000:.1f}M to trade")
            
            # Add at least one player but stop if we've reached salary target
            if len(our_players) >= 1 and current_salary >= target_outgoing_salary:
                break
        
        # If we couldn't find any players, take the lowest value player
        if not our_players and our_sorted_players:
            player = our_sorted_players[0]
            our_players.append(player)
            current_salary = player.salary
            print(f"Falling back to lowest value player: {player.name} with salary ${player.salary/1000000:.1f}M")
        
        # Always allow trades to proceed - don't be too strict
        print(f"Final outgoing salary: ${current_salary/1000000:.1f}M")
        
        # Add players to trade
        for player in target_players:
            trade.team2_players.append(player.id)
        
        for player in our_players:
            trade.team1_players.append(player.id)
        
        # Generate a message
        message = f"I'm proposing a trade where we send "
        message += ", ".join([p.name for p in our_players])
        message += f" to the {target_team.city} {target_team.name} in exchange for "
        message += ", ".join([p.name for p in target_players])
        message += ". This trade addresses our need for "
        message += ", ".join([p.position for p in target_players])
        
        return TradeProposal(trade=trade, message=message)
    
    async def connect_to_mcp_server(self, server_script_path: str = "nba_server.py"):
        """Connect to the NBA MCP server for enhanced trade evaluations"""
        try:
            server_params = StdioServerParameters(
                command="python",
                args=[server_script_path],
                env=None
            )
            
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            self.mcp_session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
            
            await self.mcp_session.initialize()
            print("reached the end, connected to MCP", self.mcp_session, file=sys.stderr)
            return True
        except Exception as e:
            print(f"Error connecting to MCP server: {e}")
            return False
    
    async def disconnect_from_mcp_server(self):
        """Disconnect from the NBA MCP server"""
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.exit_stack = AsyncExitStack()
            self.mcp_session = None
    
    async def evaluate_trade_with_claude(self, trade: Trade) -> Dict[str, Any]:
        """Use Claude to evaluate a trade in more detail"""
        # Determine which side we're on
        our_side = 1 if trade.team1 == self.team_abbr else 2
        our_players_ids = trade.team1_players if our_side == 1 else trade.team2_players
        their_players_ids = trade.team2_players if our_side == 1 else trade.team1_players
        other_team_abbr = trade.team2 if our_side == 1 else trade.team1
        
        # Get the teams
        our_team = self.team
        other_team = self.league_state.get_team_by_abbreviation(other_team_abbr)
        
        # Get the actual player objects
        our_players = [p for p in our_team.players if p.id in our_players_ids]
        their_players = [p for p in other_team.players if p.id in their_players_ids]
        
        # Format player data
        our_players_data = [
            {
                "name": p.name, 
                "position": p.position, 
                "age": p.age,
                "salary": f"${p.salary/1000000:.1f}M",
                "contract_years": p.contract_years,
                "stats": {k: f"{v:.1f}" for k, v in p.stats.items()}
            } 
            for p in our_players
        ]
        
        their_players_data = [
            {
                "name": p.name, 
                "position": p.position, 
                "age": p.age,
                "salary": f"${p.salary/1000000:.1f}M",
                "contract_years": p.contract_years,
                "stats": {k: f"{v:.1f}" for k, v in p.stats.items()}
            } 
            for p in their_players
        ]
        
        # Try to connect to the MCP server if not already connected
        have_mcp_tools = False
        available_tools = []
        if not self.mcp_session:
            connected = await self.connect_to_mcp_server()
        if self.mcp_session:
            try:
                # Get available tools from MCP server
                response = await self.mcp_session.list_tools()
                available_tools = [{ 
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]
                have_mcp_tools = len(available_tools) > 0
            except Exception as e:
                print(f"Error listing MCP tools: {e}")
        
        # Create prompt for Claude
        prompt = f"""You are the General Manager of the {our_team.city} {our_team.name}. 
You're considering a trade with the {other_team.city} {other_team.name}.

In this trade:
You send: {json.dumps(our_players_data, indent=2)}

You receive: {json.dumps(their_players_data, indent=2)}

Your current team needs are: {self._analyze_team_needs()}
Your current salary situation: ${our_team.total_salary()/1000000:.1f}M (Cap: ${our_team.salary_cap/1000000:.1f}M, Tax: ${our_team.luxury_tax/1000000:.1f}M)

Evaluate this trade from your perspective. Consider:
1. Player value and team fit
2. Salary implications
3. Position balance
4. Short and long-term impact

Then respond in the following JSON format:
{{
    "decision": "accept" or "reject" or "counter",
    "value_for_us": A number from 1-10,
    "value_for_them": A number from 1-10,
    "reasoning": Your reasoning in 2-3 sentences,
    "message": What you would tell the other GM
}}"""

        try:
            # Set up messages for Claude
            messages = [{
                "role": "user", 
                "content": prompt
            }]
            
            # Create parameters for Claude API call
            claude_params = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1000,
                "temperature": 0.7,
                "system": "You are an experienced NBA General Manager making trade decisions. Your response must be valid JSON.",
                "messages": messages
            }
            
            # Add available tools if we have them
            print("do i have mcp", have_mcp_tools, file=sys.stderr)
            if have_mcp_tools:
                claude_params["tools"] = available_tools
            
            # Call Claude with or without tools
            response = anthropic.messages.create(**claude_params)

            print("called claude!1!", file=sys.stderr)
            
            # Process response and handle tool calls
            tool_results = []
            final_text = []
            
            for content in response.content:
                if content.type == 'text':
                    final_text.append(content.text)
                elif content.type == 'tool_use' and self.mcp_session:
                    tool_name = content.name
                    tool_args = content.input

                    print("calling tool", tool_name, file=sys.stderr)
                    
                    # Execute tool call through MCP
                    try:
                        result = await self.mcp_session.call_tool(tool_name, tool_args)
                        tool_results.append({"call": tool_name, "result": result})
                        
                        # Continue conversation with tool results
                        if hasattr(content, 'text') and content.text:
                            messages.append({"role": "assistant", "content": content.text})
                        messages.append({"role": "user", "content": result.content})
                        
                        # Get next response from Claude
                        follow_up = anthropic.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=1000,
                            temperature=0.7,
                            system="You are an experienced NBA General Manager making trade decisions. Your response must be valid JSON.",
                            messages=messages
                        )
                        
                        if follow_up.content and len(follow_up.content) > 0 and follow_up.content[0].type == 'text':
                            final_text.append(follow_up.content[0].text)
                    except Exception as e:
                        print(f"Error executing tool {tool_name}: {e}")
            
            # Get the final text response (prefer the last text response if multiple)
            text_response = final_text[-1] if final_text else ""
            
            # Extract JSON
            try:
                json_start = text_response.find("{")
                json_end = text_response.rfind("}") + 1
                json_str = text_response[json_start:json_end]
                result = json.loads(json_str)
                return result
            except (json.JSONDecodeError, ValueError):
                # Fallback to basic evaluation if parsing fails
                return {
                    "decision": "reject" if random.random() < 0.7 else "counter",
                    "value_for_us": random.randint(3, 6),
                    "value_for_them": random.randint(5, 8),
                    "reasoning": "Failed to parse Claude's response, using fallback evaluation.",
                    "message": "I've considered your offer, but I don't think it works for our team right now."
                }
                
        except Exception as e:
            print(f"Error querying Claude: {e}")
            # Fallback to basic evaluation
            eval_result = self.evaluate_trade(trade)
            return {
                "decision": "accept" if eval_result["acceptable"] else "reject",
                "value_for_us": 7 if eval_result["acceptable"] else 4,
                "value_for_them": 6,
                "reasoning": eval_result["reasoning"],
                "message": "Thanks for the offer, but it's not the right fit for our team." if not eval_result["acceptable"] else "This looks like a deal that works for both sides."
            }
    
    async def respond_to_trade(self, trade: Trade) -> TradeResponse:
        """Generate a response to a trade proposal"""
        # Use Claude to evaluate the trade
        evaluation = await self.evaluate_trade_with_claude(trade)
        
        decision = evaluation.get("decision", "reject")
        message = evaluation.get("message", "Thank you for your trade proposal.")
        
        if decision == "accept":
            return TradeResponse(
                trade_id=trade.id,
                status="accepted",
                message=message
            )
        elif decision == "counter":
            counter_trade = self.create_counter_offer(trade)
            if counter_trade:
                return TradeResponse(
                    trade_id=trade.id,
                    status="countered",
                    message=message + " I have a counter-proposal that might work better for us.",
                    counter_trade=counter_trade
                )
            else:
                return TradeResponse(
                    trade_id=trade.id,
                    status="rejected",
                    message=message + " I couldn't find a counter-offer that works for us."
                )
        else:  # reject
            return TradeResponse(
                trade_id=trade.id,
                status="rejected",
                message=message
            )
    
    async def consider_initiating_trades(self) -> List[TradeProposal]:
        """Consider initiating trades with other teams"""
        # Check if enough time has passed since last check
        now = datetime.now()
        if (now - self.last_trade_check).total_seconds() < self.trading_cool_down:
            return []
        
        self.last_trade_check = now
        
        # Only initiate trades sometimes
        # Higher probability (0.7) to encourage more trades
        if random.random() > 0.7:
            return []
        
        # Get teams to potentially trade with
        other_teams = [abbr for abbr in self.league_state.teams.keys() if abbr != self.team_abbr]
        
        # Choose 2-3 random teams to consider trades with
        num_teams = random.randint(2, 3)
        target_teams = random.sample(other_teams, min(num_teams, len(other_teams)))
        
        proposals = []
        for target_team in target_teams:
            proposal = self.generate_trade_proposal(target_team)
            if proposal:
                proposals.append(proposal)
        
        return proposals

# Manager class to coordinate multiple GM agents
class GMAgentManager:
    def __init__(self, league_state_path: str = "league_state.json", mcp_server_path: str = "nba_server.py"):
        self.league_state_path = league_state_path
        self.mcp_server_path = mcp_server_path
        self.league_state = LeagueState.load(league_state_path)
        if not self.league_state.teams:
            from models import initialize_league
            self.league_state = initialize_league(league_state_path)
        
        # Create agents for each team
        self.agents = {
            abbr: GMAgent(abbr, self.league_state)
            for abbr in self.league_state.teams.keys()
        }
        
        # User's selected team
        self.user_team = None
    
    def select_user_team(self, team_abbr: str):
        """Set the user's team"""
        if team_abbr in self.agents:
            self.user_team = team_abbr
            return True
        return False
    
    async def process_user_trade_proposal(self, proposal: TradeProposal) -> TradeResponse:
        """Process a trade proposal from the user"""
        trade = proposal.trade
        target_team = trade.team2 if trade.team1 == self.user_team else trade.team1
        
        if target_team not in self.agents:
            return TradeResponse(
                trade_id=trade.id,
                status="rejected",
                message="Invalid target team."
            )
        
        # Add to league state
        self.league_state.trades.append(trade)
        
        # Initialize MCP for target team agent if needed
        target_agent = self.agents[target_team]
        if not target_agent.mcp_session:
            await target_agent.connect_to_mcp_server(self.mcp_server_path)
        
        # Let the target team's agent evaluate
        response = await target_agent.respond_to_trade(trade)
        
        # If accepted, execute the trade
        if response.status == "accepted":
            self.league_state.execute_trade(trade)
        elif response.status == "countered" and response.counter_trade:
            self.league_state.trades.append(response.counter_trade)
        
        # Save league state
        self.league_state.save(self.league_state_path)
        
        return response
    
    async def process_agent_trade_proposal(self, source_team: str, proposal: TradeProposal) -> TradeResponse:
        """Process a trade proposal from an agent to another agent"""
        trade = proposal.trade
        target_team = trade.team2 if trade.team1 == source_team else trade.team1
        
        # Add to league state
        self.league_state.trades.append(trade)
        
        # Initialize MCP for target team agent if needed
        target_agent = self.agents[target_team]
        if not target_agent.mcp_session:
            await target_agent.connect_to_mcp_server(self.mcp_server_path)
        
        # Let the target team's agent evaluate
        response = await target_agent.respond_to_trade(trade)
        
        # If accepted, execute the trade
        if response.status == "accepted":
            self.league_state.execute_trade(trade)
        elif response.status == "countered" and response.counter_trade:
            self.league_state.trades.append(response.counter_trade)
        
        # Save league state
        self.league_state.save(self.league_state_path)
        
        return response
    
    async def run_agent_trade_cycle(self):
        """Run a cycle of agent-to-agent trade proposals"""

        print("hey", file=sys.stderr)
        # Skip if user hasn't selected a team
        if not self.user_team:
            return []
        
        results = []
        
        # Let agents initiate trades
        # Create a list of teams to process
        team_list = list(self.agents.keys())
        random.shuffle(team_list)  # Randomize order for fairness
        
        print("hey??", file=sys.stderr)
        # Process more teams to generate more trades
        for team_abbr in team_list:
            # Skip user's team
            if team_abbr == self.user_team:
                continue
            
            # Consider initiating trades
            agent = self.agents[team_abbr]
            proposals = await agent.consider_initiating_trades()
            
            for proposal in proposals:
                # Process each proposal
                try:
                    response = await self.process_agent_trade_proposal(team_abbr, proposal)
                    
                    results.append({
                        "proposal": proposal,
                        "response": response
                    })
                except Exception as e:
                    print(f"Error processing trade proposal from {team_abbr}: {str(e)}")
        
        # Force some AI-to-AI trades for better simulation
        # Let's make sure we have at least a few trades every cycle
        if len(results) < 2 and len(team_list) > 3:
            try:
                # Get two random teams
                available_teams = [t for t in team_list if t != self.user_team]
                if len(available_teams) >= 2:
                    source_team = random.choice(available_teams)
                    available_teams.remove(source_team)
                    target_team = random.choice(available_teams)
                    
                    # Force a trade proposal (with additional logging)
                    print(f"Forcing trade proposal from {source_team} to {target_team}")
                    proposal = self.agents[source_team].generate_trade_proposal(target_team)
                    if proposal:
                        print(f"Generated proposal: {source_team} proposes trade to {target_team} with {len(proposal.trade.team1_players)} for {len(proposal.trade.team2_players)}")
                        response = await self.process_agent_trade_proposal(source_team, proposal)
                        results.append({
                            "proposal": proposal,
                            "response": response
                        })
                        print(f"Trade response: {response.status}")
                    else:
                        print(f"Failed to generate proposal from {source_team} to {target_team}")
            except Exception as e:
                print(f"Error forcing AI-to-AI trade: {str(e)}")
        
        return results
    
    def get_league_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent league activity"""
        # Sort trades by timestamp, most recent first
        sorted_trades = sorted(
            self.league_state.trades, 
            key=lambda t: t.timestamp, 
            reverse=True
        )
        
        activity = []
        for trade in sorted_trades[:limit]:
            team1 = self.league_state.get_team_by_abbreviation(trade.team1)
            team2 = self.league_state.get_team_by_abbreviation(trade.team2)
            
            if not team1 or not team2:
                continue
            
            # Get player names
            team1_players = []
            for player_id in trade.team1_players:
                result = self.league_state.get_player_by_id(player_id)
                if result:
                    player, _ = result
                    team1_players.append(player.name)
            
            team2_players = []
            for player_id in trade.team2_players:
                result = self.league_state.get_player_by_id(player_id)
                if result:
                    player, _ = result
                    team2_players.append(player.name)
            
            activity.append({
                "id": trade.id,
                "timestamp": trade.timestamp.isoformat(),
                "status": trade.status,
                "team1": {
                    "abbr": trade.team1,
                    "name": f"{team1.city} {team1.name}",
                    "players": team1_players
                },
                "team2": {
                    "abbr": trade.team2,
                    "name": f"{team2.city} {team2.name}",
                    "players": team2_players
                },
                "proposed_by": trade.proposed_by
            })
        
        return activity
    
    def get_team_roster(self, team_abbr: str) -> Dict[str, Any]:
        """Get a team's roster"""
        team = self.league_state.get_team_by_abbreviation(team_abbr)
        if not team:
            return {"error": "Team not found"}
        
        players = []
        for player in team.players:
            players.append({
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "age": player.age,
                "height": player.height,
                "weight": player.weight,
                "salary": player.salary,
                "contract_years": player.contract_years,
                "stats": player.stats
            })
        
        # Sort by salary descending
        players.sort(key=lambda p: p["salary"], reverse=True)
        
        return {
            "team": {
                "id": team.id,
                "name": team.name,
                "abbreviation": team.abbreviation,
                "city": team.city,
                "conference": team.conference,
                "division": team.division,
            },
            "players": players,
            "salary_info": {
                "total": team.total_salary(),
                "cap": team.salary_cap,
                "luxury_tax": team.luxury_tax,
                "available_space": team.available_cap_space(),
                "over_cap": team.is_over_cap(),
                "over_tax": team.is_over_luxury_tax()
            }
        }

# Initialize the manager
manager = GMAgentManager()

async def main():
    """Test function"""
    # Initialize league
    from models import initialize_league
    league = initialize_league()
    
    # Create an agent
    agent = GMAgent("LAL", league)
    
    try:
        # Connect to MCP server
        connected = await agent.connect_to_mcp_server()
        if connected:
            print("Connected to NBA MCP server successfully.")
        else:
            print("Warning: Could not connect to NBA MCP server, proceeding without NBA API tools.")
        
        # Test trade generation
        proposal = agent.generate_trade_proposal("BOS")
        print(f"Trade Proposal: {proposal}")
        
        # Test trade evaluation
        if proposal:
            evaluation = await agent.evaluate_trade_with_claude(proposal.trade)
            print(f"Evaluation: {evaluation}")
    finally:
        # Clean up MCP resources
        if hasattr(agent, 'disconnect_from_mcp_server'):
            await agent.disconnect_from_mcp_server()

if __name__ == "__main__":
    asyncio.run(main())