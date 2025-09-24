import { Card } from "@/components/ui/card";

interface RuneProps {
  rune: {
    id: string;
    name: string;
    color: string;
    svgPath: string;
    feature_map: string[];
  };
  isActive?: boolean;
  onClick?: () => void;
}

export default function RuneComponent({ rune, isActive = false, onClick }: RuneProps) {
  return (
    <Card 
      className={`p-4 cursor-pointer transition-all hover-elevate ${
        isActive ? 'ring-2 ring-primary' : ''
      }`}
      onClick={onClick}
      data-testid={`rune-${rune.id}`}
    >
      <div className="flex flex-col items-center space-y-3">
        <div className="relative">
          <svg 
            width="80" 
            height="80" 
            viewBox="0 0 100 100" 
            className="filter drop-shadow-lg"
            style={{ filter: `drop-shadow(0 0 8px ${rune.color}40)` }}
          >
            <path 
              d={rune.svgPath} 
              fill={rune.color} 
              stroke={rune.color} 
              strokeWidth="1"
            />
          </svg>
        </div>
        <div className="text-center">
          <h3 className="font-semibold text-sm" style={{ color: rune.color }}>
            {rune.name}
          </h3>
          <div className="flex flex-wrap gap-1 mt-2 justify-center">
            {rune.feature_map.map((feature, idx) => (
              <span 
                key={idx} 
                className="text-xs px-2 py-1 bg-muted rounded-md text-muted-foreground"
              >
                {feature.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}