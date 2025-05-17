interface PlayerProps {
  id: string;
  name: string;
  position: string;
  age: number;
  salary: number;
  stats: Record<string, number>;
  selected?: boolean;
  onClick?: () => void;
}

export default function PlayerCard({ 
  id, 
  name, 
  position, 
  age, 
  salary, 
  stats, 
  selected = false,
  onClick
}: PlayerProps) {
  
  // Format salary in millions
  const formatSalary = (salary: number) => {
    return `$${(salary / 1000000).toFixed(1)}M`;
  };
  
  return (
    <div 
      className={`border rounded-lg overflow-hidden ${
        selected 
          ? 'border-blue-500 bg-blue-50 shadow-md' 
          : 'border-gray-200 bg-white hover:shadow-md'
      } transition-all cursor-pointer`}
      onClick={onClick}
    >
      <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
        <div>
          <h3 className="font-bold">{name}</h3>
          <div className="text-sm text-gray-600">{position} • {age} yrs</div>
        </div>
        <div className="font-medium text-right">
          <div className="text-gray-900">{formatSalary(salary)}</div>
        </div>
      </div>
      
      <div className="p-3 grid grid-cols-4 gap-2 text-center text-sm">
        <div>
          <div className="font-bold">{stats.ppg?.toFixed(1) || '-'}</div>
          <div className="text-xs text-gray-500">PPG</div>
        </div>
        <div>
          <div className="font-bold">{stats.rpg?.toFixed(1) || '-'}</div>
          <div className="text-xs text-gray-500">RPG</div>
        </div>
        <div>
          <div className="font-bold">{stats.apg?.toFixed(1) || '-'}</div>
          <div className="text-xs text-gray-500">APG</div>
        </div>
        <div>
          <div className="font-bold">
            {((stats.fg_pct || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">FG%</div>
        </div>
      </div>
      
      {selected && (
        <div className="bg-blue-500 text-white text-center py-1 text-xs font-medium">
          Selected
        </div>
      )}
    </div>
  );
}