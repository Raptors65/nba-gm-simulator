'use client';

import { useState, useEffect } from 'react';
import TeamSelector from './components/TeamSelector';
import ChatInterface from './components/ChatInterface';
import TeamDashboard from './components/TeamDashboard';
import Image from 'next/image';

export default function Home() {
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'chat' | 'gm'>('chat');
  const [userGmTeam, setUserGmTeam] = useState<string | null>(null);

  // Set user GM team on server when selecting a team in GM mode
  useEffect(() => {
    if (viewMode === 'gm' && selectedTeam && selectedTeam !== userGmTeam) {
      const selectTeamOnServer = async () => {
        try {
          const response = await fetch('http://127.0.0.1:5000/api/team/select', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ team: selectedTeam }),
          });
          
          if (response.ok) {
            setUserGmTeam(selectedTeam);
          }
        } catch (error) {
          console.error('Error selecting team:', error);
        }
      };
      
      selectTeamOnServer();
    }
  }, [selectedTeam, viewMode, userGmTeam]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 dark:from-gray-900 dark:to-blue-950 p-4 md:p-8">
      <header className="max-w-6xl mx-auto flex flex-col items-center justify-center py-8">
        <h1 className="text-4xl md:text-5xl font-bold text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-blue-800 dark:from-blue-400 dark:to-blue-600 mb-2">
          🏀 NBA GM Simulator
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300 text-center max-w-xl mb-6">
          Chat with NBA team General Managers and simulate trades
        </p>
        
        {/* Mode Selector */}
        <div className="flex rounded-lg overflow-hidden border border-gray-300 mb-6">
          <button
            onClick={() => setViewMode('chat')}
            className={`px-6 py-2 font-medium ${
              viewMode === 'chat'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Chat Mode
          </button>
          <button
            onClick={() => setViewMode('gm')}
            className={`px-6 py-2 font-medium ${
              viewMode === 'gm'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            GM Mode
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto mb-12">
        {selectedTeam ? (
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <button
                onClick={() => setSelectedTeam(null)}
                className="flex items-center text-blue-600 hover:text-blue-800 font-medium"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Team Selection
              </button>
            </div>
            
            {viewMode === 'chat' ? (
              <ChatInterface team={selectedTeam} />
            ) : (
              <TeamDashboard team={selectedTeam} />
            )}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="p-6 mb-2">
              <h2 className="text-2xl font-bold mb-2">
                {viewMode === 'chat' 
                  ? 'Select a team to chat with their GM'
                  : 'Select a team to manage as GM'
                }
              </h2>
              <p className="text-gray-600">
                {viewMode === 'chat'
                  ? 'Get insights about the team, players, and strategy.'
                  : 'Make trades with other teams and build your roster.'
                }
              </p>
            </div>
            <TeamSelector onSelectTeam={setSelectedTeam} />
          </div>
        )}
      </main>

      <footer className="max-w-4xl mx-auto mt-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        <p>Created with Next.js for the MCP Hackathon</p>
      </footer>
    </div>
  );
}