import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Scan, TrendingUp, Users, Hash, RefreshCw } from "lucide-react";

interface SocialTrend {
  platform: string;
  trends: Array<{
    keyword: string;
    momentum: number;
    sentiment: number;
    volume: number;
  }>;
  timestamp: number;
}

export default function SocialTrendsPanel() {
  const [isScanning, setIsScanning] = useState(false);
  const [trends, setTrends] = useState<SocialTrend[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const handleScan = async () => {
    setIsScanning(true);
    console.log('Starting social trends scan...');
    
    setTimeout(() => {
      // Mock social trends data
      const mockTrends: SocialTrend[] = [
        {
          platform: "Twitter/X",
          trends: [
            { keyword: "#AI", momentum: 0.85, sentiment: 0.72, volume: 125000 },
            { keyword: "blockchain", momentum: 0.43, sentiment: 0.58, volume: 89000 },
            { keyword: "quantum", momentum: 0.67, sentiment: 0.81, volume: 45000 }
          ],
          timestamp: Date.now()
        },
        {
          platform: "Reddit", 
          trends: [
            { keyword: "DeFi", momentum: 0.59, sentiment: 0.45, volume: 67000 },
            { keyword: "renewable energy", momentum: 0.71, sentiment: 0.79, volume: 34000 }
          ],
          timestamp: Date.now()
        }
      ];
      
      setTrends(mockTrends);
      setLastUpdate(new Date());
      setIsScanning(false);
    }, 2500);
  };

  // Auto-refresh every 12 hours (simulated)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!isScanning) {
        handleScan();
      }
    }, 10000); // Demo: refresh after 10 seconds
    
    return () => clearTimeout(timer);
  }, [isScanning]);

  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return "text-green-400";
    if (sentiment >= 0.5) return "text-yellow-400"; 
    return "text-red-400";
  };

  const getMomentumColor = (momentum: number) => {
    if (momentum >= 0.7) return "text-emerald-400";
    if (momentum >= 0.4) return "text-cyan-400";
    return "text-slate-400";
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
    return volume.toString();
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Hash className="w-5 h-5" />
            Social Oracle
          </h2>
          <p className="text-sm text-muted-foreground">
            Monitoring digital zeitgeist patterns
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {lastUpdate && (
            <span className="text-xs text-muted-foreground">
              Last: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <Button 
            onClick={handleScan}
            disabled={isScanning}
            size="sm"
            variant="outline"
            data-testid="button-scan-trends"
          >
            {isScanning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                Scanning...
              </>
            ) : (
              <>
                <Scan className="w-4 h-4 mr-2" />
                Scan Now
              </>
            )}
          </Button>
        </div>
      </div>

      {trends.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Initiate scan to reveal social currents</p>
        </div>
      ) : (
        <div className="space-y-6">
          {trends.map((platformData, idx) => (
            <div key={idx}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-accent">{platformData.platform}</h3>
                <Badge variant="secondary" className="text-xs">
                  {platformData.trends.length} signals
                </Badge>
              </div>
              
              <div className="grid gap-3">
                {platformData.trends.map((trend, trendIdx) => (
                  <Card key={trendIdx} className="p-4 bg-card/50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-medium text-sm flex items-center gap-2">
                        <Hash className="w-3 h-3" />
                        {trend.keyword}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatVolume(trend.volume)} mentions
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className={`text-lg font-mono ${getMomentumColor(trend.momentum)}`}>
                          {(trend.momentum * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-muted-foreground">Momentum</div>
                      </div>
                      
                      <div>
                        <div className={`text-lg font-mono ${getSentimentColor(trend.sentiment)}`}>
                          {trend.sentiment >= 0.5 ? '+' : ''}{((trend.sentiment - 0.5) * 200).toFixed(0)}%
                        </div>
                        <div className="text-xs text-muted-foreground">Sentiment</div>
                      </div>
                      
                      <div>
                        <div className="text-lg font-mono text-primary">
                          <TrendingUp className="w-4 h-4 mx-auto" />
                        </div>
                        <div className="text-xs text-muted-foreground">Trending</div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
              
              {idx < trends.length - 1 && <Separator className="mt-6" />}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}