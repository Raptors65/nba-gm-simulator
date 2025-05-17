'use client';

import { useState, useEffect } from 'react';
import TeamLogo from './TeamLogo';
import PlayerCard from './PlayerCard';

interface Player {
  id: string;
  name: string;
  position: string;
  age: number;
  height: string;
  weight: number;
  salary: number;
  contract_years: number;
  stats: Record<string, number>;
}

interface Team {
  id: string;
  name: string;
  abbreviation: string;
  city: string;
  conference: string;
  division: string;
}

interface TradeModalProps {
  userTeam: string;
  currentPlayers: Player[];
  onClose: () => void;
  onTradeComplete: () => void;
}

export default function TradeModal({
  userTeam,
  currentPlayers,
  onClose,
  onTradeComplete
}: TradeModalProps) {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [targetTeamPlayers, setTargetTeamPlayers] = useState<Player[]>([]);
  const [selectedUserPlayers, setSelectedUserPlayers] = useState<string[]>([]);
  const [selectedTargetPlayers, setSelectedTargetPlayers] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tradeMessage, setTradeMessage] = useState('');
  const [responseMessage, setResponseMessage] = useState<string | null>(null);
  const [tradeStatus, setTradeStatus] = useState<string | null>(null);
  const [counterTrade, setCounterTrade] = useState<any>(null);

  // Fetch teams on mount
  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5001/api/teams');
        if (!response.ok) {
          throw new Error('Failed to fetch teams');
        }
        const data = await response.json();
        // Filter out the user's team
        const filteredTeams = data.teams.filter((team: Team) => team.abbreviation !== userTeam);
        setTeams(filteredTeams);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        console.error('Error fetching teams:', err);
      }
    };

    fetchTeams();
  }, [userTeam]);

  // Fetch team players when a team is selected
  useEffect(() => {
    if (selectedTeam) {
      const fetchTeamPlayers = async () => {
        try {
          setLoading(true);
          const response = await fetch(`http://127.0.0.1:5001/api/team/roster/${selectedTeam.abbreviation}`);
          if (!response.ok) {
            throw new Error('Failed to fetch team roster');
          }
          const data = await response.json();
          setTargetTeamPlayers(data.players || []);
          setError(null);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'An error occurred');
          console.error('Error fetching roster:', err);
        } finally {
          setLoading(false);
        }
      };

      fetchTeamPlayers();
    }
  }, [selectedTeam]);

  // Handle user player selection
  const toggleUserPlayer = (playerId: string) => {
    setSelectedUserPlayers(prev => 
      prev.includes(playerId) 
        ? prev.filter(id => id !== playerId)
        : [...prev, playerId]
    );
  };

  // Handle target player selection
  const toggleTargetPlayer = (playerId: string) => {
    setSelectedTargetPlayers(prev => 
      prev.includes(playerId) 
        ? prev.filter(id => id !== playerId)
        : [...prev, playerId]
    );
  };

  // Calculate total salary
  const calculateTotalSalary = (players: Player[], selectedIds: string[]) => {
    return players
      .filter(player => selectedIds.includes(player.id))
      .reduce((sum, player) => sum + player.salary, 0);
  };

  const userTotalSalary = calculateTotalSalary(currentPlayers, selectedUserPlayers);
  const targetTotalSalary = calculateTotalSalary(targetTeamPlayers, selectedTargetPlayers);
  const salaryDifference = targetTotalSalary - userTotalSalary;

  // Format salary in millions
  const formatSalaryInMillions = (salary: number) => {
    return `$${(salary / 1000000).toFixed(2)}M`;
  };

  // Submit trade proposal
  const submitTradeProposal = async () => {
    if (!selectedTeam) {
      setError('No team selected');
      return;
    }

    if (selectedUserPlayers.length === 0 && selectedTargetPlayers.length === 0) {
      setError('You must select at least one player to trade');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      
      const tradeData = {
        trade: {
          team1: userTeam,
          team2: selectedTeam.abbreviation,
          team1_players: selectedUserPlayers,
          team2_players: selectedTargetPlayers,
          team1_picks: [],
          team2_picks: []
        },
        message: tradeMessage || 'Trade proposal from user'
      };

      const response = await fetch('http://127.0.0.1:5001/api/trade/propose', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tradeData),
      });

      if (!response.ok) {
        throw new Error('Failed to submit trade proposal');
      }

      const result = await response.json();
      
      if (result.success) {
        setResponseMessage(result.message);
        setTradeStatus(result.status);
        setCounterTrade(result.counter_trade);
        
        if (result.status === 'accepted') {
          // If accepted, notify parent to refresh
          setTimeout(() => {
            onTradeComplete();
          }, 3000);
        }
      } else {
        setError(result.message || 'Trade proposal failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error submitting trade:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Accept counter offer
  const acceptCounterOffer = async () => {
    if (!counterTrade || !counterTrade.id) {
      setError('No counter trade to accept');
      return;
    }

    try {
      setSubmitting(true);
      
      const response = await fetch('http://127.0.0.1:5001/api/trade/respond', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          trade_id: counterTrade.id,
          action: 'accept'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to accept counter trade');
      }

      const result = await response.json();
      
      if (result.success) {
        setResponseMessage('Counter offer accepted! Trade completed.');
        
        // Notify parent to refresh
        setTimeout(() => {
          onTradeComplete();
        }, 2000);
      } else {
        setError(result.message || 'Failed to accept counter trade');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error accepting counter:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Reject counter offer
  const rejectCounterOffer = async () => {
    if (!counterTrade || !counterTrade.id) {
      setError('No counter trade to reject');
      return;
    }

    try {
      setSubmitting(true);
      
      const response = await fetch('http://127.0.0.1:5001/api/trade/respond', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          trade_id: counterTrade.id,
          action: 'reject'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to reject counter trade');
      }

      const result = await response.json();
      
      if (result.success) {
        setResponseMessage('Counter offer rejected.');
        setCounterTrade(null);
      } else {
        setError(result.message || 'Failed to reject counter trade');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error rejecting counter:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Render counter trade details
  const renderCounterTradeDetails = () => {
    if (!counterTrade || !selectedTeam) return null;

    // Find what players are in the counter offer
    const userPlayersInCounter = counterTrade.team1 === userTeam
      ? counterTrade.team1_players
      : counterTrade.team2_players;

    const targetPlayersInCounter = counterTrade.team1 === selectedTeam.abbreviation
      ? counterTrade.team1_players
      : counterTrade.team2_players;

    // Get player names
    const userPlayerNames = currentPlayers
      .filter(p => userPlayersInCounter.includes(p.id))
      .map(p => p.name);

    const targetPlayerNames = targetTeamPlayers
      .filter(p => targetPlayersInCounter.includes(p.id))
      .map(p => p.name);

    return (
      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="font-bold text-lg mb-3">Counter Offer Received</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <h4 className="font-medium text-sm text-gray-700 mb-1">You Send:</h4>
            <ul className="list-disc list-inside">
              {userPlayerNames.length > 0 ? (
                userPlayerNames.map((name, i) => (
                  <li key={i} className="text-sm">{name}</li>
                ))
              ) : (
                <li className="text-sm text-gray-500">No players</li>
              )}
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium text-sm text-gray-700 mb-1">You Receive:</h4>
            <ul className="list-disc list-inside">
              {targetPlayerNames.length > 0 ? (
                targetPlayerNames.map((name, i) => (
                  <li key={i} className="text-sm">{name}</li>
                ))
              ) : (
                <li className="text-sm text-gray-500">No players</li>
              )}
            </ul>
          </div>
        </div>
        
        <div className="flex gap-3 mt-4">
          <button
            onClick={acceptCounterOffer}
            disabled={submitting}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-medium text-sm"
          >
            Accept Counter
          </button>
          <button
            onClick={rejectCounterOffer}
            disabled={submitting}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded font-medium text-sm"
          >
            Reject Counter
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-2xl font-bold">Trade Proposal</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto flex-grow">
          {responseMessage ? (
            <div className={`mb-6 p-4 rounded-lg ${
              tradeStatus === 'accepted' 
                ? 'bg-green-100 text-green-800' 
                : tradeStatus === 'rejected'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
            }`}>
              <h3 className="font-bold text-lg">{
                tradeStatus === 'accepted' 
                  ? '✅ Trade Accepted!' 
                  : tradeStatus === 'rejected'
                    ? '❌ Trade Rejected'
                    : '⚠️ Counter Offer'
              }</h3>
              <p>{responseMessage}</p>
              
              {tradeStatus === 'countered' && renderCounterTradeDetails()}
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-6 p-4 bg-red-100 text-red-800 rounded-lg">
                  <p>{error}</p>
                </div>
              )}
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select a team to trade with:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {teams.map((team) => (
                    <button
                      key={team.id}
                      onClick={() => setSelectedTeam(team)}
                      className={`p-3 border rounded-lg flex flex-col items-center gap-2 ${
                        selectedTeam?.id === team.id 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <TeamLogo team={team.abbreviation} size={36} />
                      <span className="text-sm font-medium">{team.abbreviation}</span>
                    </button>
                  ))}
                </div>
              </div>
              
              {selectedTeam && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div>
                      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                        <TeamLogo team={userTeam} size={24} />
                        Your Players
                      </h3>
                      
                      {loading ? (
                        <div className="py-8 flex justify-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 gap-3 max-h-[400px] overflow-y-auto p-1">
                          {currentPlayers.map((player) => (
                            <PlayerCard
                              key={player.id}
                              {...player}
                              selected={selectedUserPlayers.includes(player.id)}
                              onClick={() => toggleUserPlayer(player.id)}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div>
                      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                        <TeamLogo team={selectedTeam.abbreviation} size={24} />
                        {selectedTeam.city} {selectedTeam.name} Players
                      </h3>
                      
                      {loading ? (
                        <div className="py-8 flex justify-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 gap-3 max-h-[400px] overflow-y-auto p-1">
                          {targetTeamPlayers.map((player) => (
                            <PlayerCard
                              key={player.id}
                              {...player}
                              selected={selectedTargetPlayers.includes(player.id)}
                              onClick={() => toggleTargetPlayer(player.id)}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-lg mb-6">
                    <h3 className="font-medium mb-3">Trade Summary</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <div className="text-sm text-gray-600">Your Outgoing Salary:</div>
                        <div className="font-medium">{formatSalaryInMillions(userTotalSalary)}</div>
                      </div>
                      
                      <div>
                        <div className="text-sm text-gray-600">Incoming Salary:</div>
                        <div className="font-medium">{formatSalaryInMillions(targetTotalSalary)}</div>
                      </div>
                      
                      <div>
                        <div className="text-sm text-gray-600">Difference:</div>
                        <div className={`font-medium ${salaryDifference > 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {salaryDifference > 0 ? '+' : ''}{formatSalaryInMillions(salaryDifference)}
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <label htmlFor="tradeMessage" className="block text-sm font-medium text-gray-700 mb-1">
                        Message (optional):
                      </label>
                      <textarea
                        id="tradeMessage"
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Add a message to the GM..."
                        value={tradeMessage}
                        onChange={(e) => setTradeMessage(e.target.value)}
                      />
                    </div>
                  </div>
                </>
              )}
            </>
          )}
        </div>
        
        <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Close
          </button>
          
          {!responseMessage && selectedTeam && (
            <button
              onClick={submitTradeProposal}
              disabled={submitting || (!selectedUserPlayers.length && !selectedTargetPlayers.length)}
              className={`px-4 py-2 rounded-md shadow-sm text-sm font-medium text-white ${
                submitting || (!selectedUserPlayers.length && !selectedTargetPlayers.length)
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {submitting ? 'Submitting...' : 'Submit Trade Proposal'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}