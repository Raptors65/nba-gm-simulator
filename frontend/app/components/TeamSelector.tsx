import { useState } from 'react';
import TeamLogo from './TeamLogo';

interface TeamSelectorProps {
  onSelectTeam: (team: string) => void;
}

const NBA_TEAMS = [
  { name: 'Atlanta Hawks', abbr: 'ATL' },
  { name: 'Boston Celtics', abbr: 'BOS' },
  { name: 'Brooklyn Nets', abbr: 'BKN' },
  { name: 'Charlotte Hornets', abbr: 'CHA' },
  { name: 'Chicago Bulls', abbr: 'CHI' },
  { name: 'Cleveland Cavaliers', abbr: 'CLE' },
  { name: 'Dallas Mavericks', abbr: 'DAL' },
  { name: 'Denver Nuggets', abbr: 'DEN' },
  { name: 'Detroit Pistons', abbr: 'DET' },
  { name: 'Golden State Warriors', abbr: 'GSW' },
  { name: 'Houston Rockets', abbr: 'HOU' },
  { name: 'Indiana Pacers', abbr: 'IND' },
  { name: 'LA Clippers', abbr: 'LAC' },
  { name: 'Los Angeles Lakers', abbr: 'LAL' },
  { name: 'Memphis Grizzlies', abbr: 'MEM' },
  { name: 'Miami Heat', abbr: 'MIA' },
  { name: 'Milwaukee Bucks', abbr: 'MIL' },
  { name: 'Minnesota Timberwolves', abbr: 'MIN' },
  { name: 'New Orleans Pelicans', abbr: 'NOP' },
  { name: 'New York Knicks', abbr: 'NYK' },
  { name: 'Oklahoma City Thunder', abbr: 'OKC' },
  { name: 'Orlando Magic', abbr: 'ORL' },
  { name: 'Philadelphia 76ers', abbr: 'PHI' },
  { name: 'Phoenix Suns', abbr: 'PHX' },
  { name: 'Portland Trail Blazers', abbr: 'POR' },
  { name: 'Sacramento Kings', abbr: 'SAC' },
  { name: 'San Antonio Spurs', abbr: 'SAS' },
  { name: 'Toronto Raptors', abbr: 'TOR' },
  { name: 'Utah Jazz', abbr: 'UTA' },
  { name: 'Washington Wizards', abbr: 'WAS' }
];

export default function TeamSelector({ onSelectTeam }: TeamSelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTeams = searchTerm.trim() === '' 
    ? NBA_TEAMS 
    : NBA_TEAMS.filter(team => 
        team.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
        team.abbr.toLowerCase().includes(searchTerm.toLowerCase())
      );

  return (
    <div className="max-w-4xl mx-auto mt-8 p-6 bg-white rounded-lg shadow-lg border border-gray-200">
      <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">Select an NBA Team</h2>
      
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search for a team..."
          className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {filteredTeams.map((team) => (
          <button
            key={team.abbr}
            onClick={() => onSelectTeam(team.abbr)}
            className="p-3 text-center border border-gray-200 rounded-lg hover:bg-blue-600 hover:text-white transition-colors duration-200 flex flex-col items-center gap-2"
          >
            <TeamLogo team={team.abbr} size={36} />
            <div className="font-bold text-gray-800">{team.abbr}</div>
            <div className="text-sm truncate text-gray-700">{team.name}</div>
          </button>
        ))}
      </div>
    </div>
  );
}