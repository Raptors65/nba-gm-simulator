'use client';

import { useState } from 'react';
import TeamSelector from './components/TeamSelector';
import ChatInterface from './components/ChatInterface';
import Image from 'next/image';

export default function Home() {
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 dark:from-gray-900 dark:to-blue-950 p-4 md:p-8">
      <header className="max-w-4xl mx-auto flex flex-col items-center justify-center py-8">
        <h1 className="text-4xl md:text-5xl font-bold text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-blue-800 dark:from-blue-400 dark:to-blue-600 mb-2">
          🏀 NBA GM Simulator
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300 text-center max-w-xl">
          Chat with any NBA team's General Manager and get insights about their team
        </p>
      </header>

      <main className="max-w-6xl mx-auto">
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
              <div className="text-xl font-bold text-gray-800 dark:text-gray-200">
                {selectedTeam} General Manager
              </div>
            </div>
            <ChatInterface team={selectedTeam} />
          </div>
        ) : (
          <TeamSelector onSelectTeam={setSelectedTeam} />
        )}
      </main>

      <footer className="max-w-4xl mx-auto mt-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        <p>Created with Next.js for the MCP Hackathon</p>
      </footer>
    </div>
  );
}