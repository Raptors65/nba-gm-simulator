interface TeamLogoProps {
  team: string;
  size?: number;
}

export default function TeamLogo({ team, size = 40 }: TeamLogoProps) {
  // This is a placeholder, in a real app you would use actual team logos
  // For the hackathon, we're using a simple colored circle with the team abbreviation
  
  // Get a consistent color based on the team abbreviation
  const getTeamColor = (abbr: string) => {
    const colorMap: Record<string, string> = {
      'ATL': '#E03A3E', // Hawks
      'BOS': '#007A33', // Celtics
      'BKN': '#000000', // Nets
      'CHA': '#1D1160', // Hornets
      'CHI': '#CE1141', // Bulls
      'CLE': '#860038', // Cavaliers
      'DAL': '#00538C', // Mavericks
      'DEN': '#0E2240', // Nuggets
      'DET': '#C8102E', // Pistons
      'GSW': '#1D428A', // Warriors
      'HOU': '#CE1141', // Rockets
      'IND': '#002D62', // Pacers
      'LAC': '#C8102E', // Clippers
      'LAL': '#552583', // Lakers
      'MEM': '#5D76A9', // Grizzlies
      'MIA': '#98002E', // Heat
      'MIL': '#00471B', // Bucks
      'MIN': '#0C2340', // Timberwolves
      'NOP': '#0C2340', // Pelicans
      'NYK': '#F58426', // Knicks
      'OKC': '#007AC1', // Thunder
      'ORL': '#0077C0', // Magic
      'PHI': '#006BB6', // 76ers
      'PHX': '#1D1160', // Suns
      'POR': '#E03A3E', // Trail Blazers
      'SAC': '#5A2D81', // Kings
      'SAS': '#C4CED4', // Spurs
      'TOR': '#CE1141', // Raptors
      'UTA': '#002B5C', // Jazz
      'WAS': '#002B5C'  // Wizards
    };
    
    return colorMap[abbr] || '#1D428A'; // Default to NBA blue
  };

  return (
    <div 
      style={{ 
        width: size, 
        height: size, 
        backgroundColor: getTeamColor(team),
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontWeight: 'bold',
        fontSize: size * 0.4
      }}
    >
      {team}
    </div>
  );
}