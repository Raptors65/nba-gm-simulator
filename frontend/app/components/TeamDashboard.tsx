'use client';

import { useState, useEffect } from 'react';
import TeamLogo from './TeamLogo';
import PlayerCard from './PlayerCard';
import TradeModal from './TradeModal';
import LeagueActivity from './LeagueActivity';

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

interface TeamInfo {
  id: string;
  name: string;
  abbreviation: string;
  city: string;
  conference: string;
  division: string;
}

interface SalaryInfo {
  total: number;
  cap: number;
  luxury_tax: number;
  available_space: number;
  over_cap: boolean;
  over_tax: boolean;
}

interface TeamRosterResponse {
  team: TeamInfo;
  players: Player[];
  salary_info: SalaryInfo;
  error?: string;
}

export default function TeamDashboard({ team }: { team: string }) {
  const [rosterData, setRosterData] = useState<TeamRosterResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [simulationInProgress, setSimulationInProgress] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0); // Use to force refresh of components

  useEffect(() => {
    const fetchRoster = async () => {
      try {
        setLoading(true);
        const response = await fetch(`http://127.0.0.1:5000/api/team/roster/${team}`);
        if (!response.ok) {
          throw new Error('Failed to fetch team roster');
        }
        const data = await response.json();
        setRosterData(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        console.error('Error fetching roster:', err);
      } finally {
        setLoading(false);
      }
    };

    if (team) {
      fetchRoster();
    }
  }, [team, refreshKey]);

  // Function to simulate league trades
  const simulateLeague = async () => {
    try {
      setSimulationInProgress(true);
      console.log("Starting league simulation...");
      
      const response = await fetch('http://127.0.0.1:5000/api/league/simulate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });
      
      if (!response.ok) {
        console.error("API response not OK:", response.status);
        throw new Error('Failed to simulate league');
      }
      
      const data = await response.json();
      console.log("Simulation response:", data);
      
      if (data.success) {
        // Log activity to see if there's any data
        if (data.activity && data.activity.length > 0) {
          console.log(`Received ${data.activity.length} league activity items`);
        } else {
          console.warn("No league activity received from simulation");
        }
        
        // Show a success message (temporary for debugging)
        const activityCount = data.activity ? data.activity.length : 0;
        const tradesCount = data.trades ? data.trades.length : 0;
        setError(`Simulation completed: ${tradesCount} trades processed, ${activityCount} activity items`);
        
        // Refresh components with a slight delay to ensure API changes are reflected
        setTimeout(() => {
          setRefreshKey(prev => prev + 1);
          setError(null); // Clear the message after refresh
        }, 300);
      } else {
        setError(data.message || 'Simulation failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during simulation');
      console.error('Simulation error:', err);
    } finally {
      setSimulationInProgress(false);
    }
  };

  // Format dollar amount
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  // Format salary in millions
  const formatSalaryInMillions = (salary: number) => {
    return `$${(salary / 1000000).toFixed(2)}M`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 text-red-800 rounded-lg">
        <h3 className="font-bold">Error</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (!rosterData) {
    return (
      <div className="p-4 bg-yellow-100 text-yellow-800 rounded-lg">
        <h3 className="font-bold">No Data</h3>
        <p>No roster data available for this team.</p>
      </div>
    );
  }

  const { team: teamInfo, players, salary_info } = rosterData;

  return (
    <div className="container mx-auto p-4">
      <div className="mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          <TeamLogo team={team} size={64} />
          <div>
            <h1 className="text-3xl font-bold">{teamInfo.city} {teamInfo.name}</h1>
            <p className="text-gray-600">{teamInfo.conference} Conference / {teamInfo.division} Division</p>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <button 
            onClick={() => setShowTradeModal(true)}
            className="bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded-lg font-medium transition"
          >
            Propose Trade
          </button>
          
          <button 
            onClick={simulateLeague}
            disabled={simulationInProgress}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              simulationInProgress 
                ? "bg-gray-400 cursor-not-allowed" 
                : "bg-blue-700 hover:bg-blue-800 text-white"
            }`}
          >
            {simulationInProgress ? 'Simulating...' : 'Simulate League Activity'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
        {/* Roster and Salary Section - 3 columns wide */}
        <div className="lg:col-span-3 space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 border-b pb-2">Salary Information</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <h3 className="text-sm text-gray-600">Total Salary</h3>
                <p className={`text-lg font-medium ${salary_info.over_cap ? 'text-red-600' : 'text-green-600'}`}>
                  {formatSalaryInMillions(salary_info.total)}
                </p>
              </div>
              <div>
                <h3 className="text-sm text-gray-600">Salary Cap</h3>
                <p className="text-lg font-medium">{formatSalaryInMillions(salary_info.cap)}</p>
              </div>
              <div>
                <h3 className="text-sm text-gray-600">Luxury Tax</h3>
                <p className="text-lg font-medium">{formatSalaryInMillions(salary_info.luxury_tax)}</p>
              </div>
              <div>
                <h3 className="text-sm text-gray-600">Cap Space</h3>
                <p className={`text-lg font-medium ${salary_info.available_space > 0 ? 'text-green-600' : 'text-gray-600'}`}>
                  {salary_info.available_space > 0 
                    ? formatSalaryInMillions(salary_info.available_space)
                    : 'None (Over Cap)'}
                </p>
              </div>
              <div>
                <h3 className="text-sm text-gray-600">Cap Status</h3>
                <p className={`text-lg font-medium ${salary_info.over_cap ? 'text-red-600' : 'text-green-600'}`}>
                  {salary_info.over_cap ? 'Over Cap' : 'Under Cap'}
                </p>
              </div>
              <div>
                <h3 className="text-sm text-gray-600">Tax Status</h3>
                <p className={`text-lg font-medium ${salary_info.over_tax ? 'text-red-600' : 'text-green-600'}`}>
                  {salary_info.over_tax ? 'Taxpayer' : 'Non-Taxpayer'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-6 pb-4">
              <h2 className="text-xl font-bold mb-2">Team Roster</h2>
              <p className="text-sm text-gray-600">{players.length} players</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-6 py-3">Player</th>
                    <th className="px-6 py-3">Pos</th>
                    <th className="px-6 py-3">Age</th>
                    <th className="px-6 py-3">Salary</th>
                    <th className="px-6 py-3">Years</th>
                    <th className="px-6 py-3">PPG</th>
                    <th className="px-6 py-3">RPG</th>
                    <th className="px-6 py-3">APG</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {players.map((player) => (
                    <tr key={player.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium">{player.name}</td>
                      <td className="px-6 py-4">{player.position}</td>
                      <td className="px-6 py-4">{player.age}</td>
                      <td className="px-6 py-4">{formatSalaryInMillions(player.salary)}</td>
                      <td className="px-6 py-4">{player.contract_years}</td>
                      <td className="px-6 py-4">{player.stats.ppg?.toFixed(1) || '-'}</td>
                      <td className="px-6 py-4">{player.stats.rpg?.toFixed(1) || '-'}</td>
                      <td className="px-6 py-4">{player.stats.apg?.toFixed(1) || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* League Activity Section - 2 columns wide */}
        <div className="lg:col-span-2">
          <LeagueActivity refreshKey={refreshKey} />
        </div>
      </div>

      {showTradeModal && (
        <TradeModal 
          userTeam={team}
          currentPlayers={players}
          onClose={() => setShowTradeModal(false)}
          onTradeComplete={() => {
            setShowTradeModal(false);
            setRefreshKey(prev => prev + 1); // Refresh data
          }}
        />
      )}
    </div>
  );
}