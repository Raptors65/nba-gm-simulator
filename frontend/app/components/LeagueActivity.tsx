'use client';

import { useState, useEffect } from 'react';
import TeamLogo from './TeamLogo';

interface TradeActivity {
  id: string;
  timestamp: string;
  status: string;
  team1: {
    abbr: string;
    name: string;
    players: string[];
  };
  team2: {
    abbr: string;
    name: string;
    players: string[];
  };
  proposed_by: string;
}

interface LeagueActivityProps {
  refreshKey?: number;
}

export default function LeagueActivity({ refreshKey = 0 }: LeagueActivityProps) {
  const [activity, setActivity] = useState<TradeActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchActivity = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://127.0.0.1:5001/api/league/activity?limit=15');
        if (!response.ok) {
          throw new Error('Failed to fetch league activity');
        }
        const data = await response.json();
        setActivity(data.activity || []);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        console.error('Error fetching activity:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchActivity();
  }, [refreshKey]);

  // Format date
  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Format status
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'accepted':
        return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">Accepted</span>;
      case 'rejected':
        return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">Rejected</span>;
      case 'countered':
        return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">Countered</span>;
      case 'proposed':
        return <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">Proposed</span>;
      default:
        return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">{status}</span>;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow h-full">
      <div className="p-6 pb-4 border-b border-gray-200">
        <h2 className="text-xl font-bold text-gray-800">League Activity</h2>
        <p className="text-sm text-gray-600">Recent trades and negotiations</p>
      </div>
      
      <div className="p-0">
        {loading ? (
          <div className="py-8 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
          </div>
        ) : error ? (
          <div className="p-6 text-center text-red-600">
            <p>{error}</p>
          </div>
        ) : activity.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p>No recent trade activity</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
            {activity.map((item) => (
              <li key={item.id} className="px-6 py-4">
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">{formatDate(item.timestamp)}</span>
                    {getStatusBadge(item.status)}
                  </div>
                  
                  <div className="grid grid-cols-7 items-center gap-2">
                    <div className="col-span-3 flex items-center gap-2">
                      <TeamLogo team={item.team1.abbr} size={24} />
                      <div className="text-sm font-medium truncate text-gray-800">{item.team1.name}</div>
                    </div>
                    
                    <div className="col-span-1 text-center text-xs font-medium text-gray-500">
                      ↔️
                    </div>
                    
                    <div className="col-span-3 flex items-center gap-2">
                      <TeamLogo team={item.team2.abbr} size={24} />
                      <div className="text-sm font-medium truncate text-gray-800">{item.team2.name}</div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-7 items-start gap-2 text-xs text-gray-600">
                    <div className="col-span-3">
                      <p><span className="font-medium">Sent:</span> {item.team1.players.join(', ') || 'None'}</p>
                    </div>
                    
                    <div className="col-span-1"></div>
                    
                    <div className="col-span-3">
                      <p><span className="font-medium">Received:</span> {item.team2.players.join(', ') || 'None'}</p>
                    </div>
                  </div>
                  
                  <div className="text-xs text-gray-500">
                    Proposed by: {item.proposed_by === 'user' 
                      ? 'You' 
                      : item.proposed_by === item.team1.abbr 
                        ? item.team1.name
                        : item.proposed_by === item.team2.abbr
                          ? item.team2.name
                          : item.proposed_by}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}