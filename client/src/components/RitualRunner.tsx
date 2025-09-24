import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { PlayCircle, Sparkles, TrendingUp, TrendingDown } from "lucide-react";

interface RitualResult {
  ritual: {
    date: string;
    seed: number;
    runes: Array<{
      id: string;
      name: string;
      color: string;
    }>;
  };
  results: {
    equities: {
      conservative: Array<{
        ticker: string;
        edge: number;
        confidence: number;
        sector: string;
        rationale: string[];
      }>;
      risky: Array<{
        ticker: string;
        edge: number;
        confidence: number;
        sector: string;
        rationale: string[];
      }>;
    };
    fx: {
      conservative: Array<{
        pair: string;
        edge: number;
        confidence: number;
        rationale: string[];
      }>;
      risky: Array<{
        pair: string;
        edge: number;
        confidence: number;
        rationale: string[];
      }>;
    };
  };
}

export default function RitualRunner() {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<RitualResult | null>(null);
  const [watchlists, setWatchlists] = useState({
    equities: ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
    fx: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
  });

  const handleRunRitual = async () => {
    setIsRunning(true);
    console.log('Running ritual with watchlists:', watchlists);
    
    // Simulate ritual running
    setTimeout(() => {
      // Mock ritual result
      const mockResult: RitualResult = {
        ritual: {
          date: new Date().toISOString().slice(0, 10),
          seed: Math.floor(Math.random() * 1000000),
          runes: [
            { id: "aether", name: "Aether", color: "#FFD166" },
            { id: "tide", name: "Tide", color: "#4CC9F0" }
          ]
        },
        results: {
          equities: {
            conservative: [
              {
                ticker: "AAPL",
                edge: 0.125,
                confidence: 0.73,
                sector: "Technology",
                rationale: ["Contract scope ↑", "Night-lights ↑"]
              }
            ],
            risky: [
              {
                ticker: "TSLA", 
                edge: -0.087,
                confidence: 0.45,
                sector: "Automotive",
                rationale: ["IPR pressure easing", "Planetary align"]
              }
            ]
          },
          fx: {
            conservative: [
              {
                pair: "EURUSD",
                edge: 0.032,
                confidence: 0.68,
                rationale: ["Funding stress ↓", "Trade flow ↑"]
              }
            ],
            risky: []
          }
        }
      };
      
      setResult(mockResult);
      setIsRunning(false);
    }, 3000);
  };

  const ResultCard = ({ item, type }: { item: any; type: 'equity' | 'fx' }) => (
    <Card className="p-3">
      <div className="flex justify-between items-start mb-2">
        <span className="font-semibold text-sm">
          {type === 'equity' ? item.ticker : item.pair}
        </span>
        <div className="flex items-center gap-2">
          {item.edge >= 0 ? 
            <TrendingUp className="w-4 h-4 text-green-400" /> : 
            <TrendingDown className="w-4 h-4 text-red-400" />
          }
          <span className={`text-sm font-mono ${item.edge >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {item.edge > 0 ? '+' : ''}{item.edge}
          </span>
        </div>
      </div>
      
      <div className="flex justify-between items-center mb-2">
        <Badge variant="secondary" className="text-xs">
          {item.confidence}% conf
        </Badge>
        {type === 'equity' && (
          <span className="text-xs text-muted-foreground">{item.sector}</span>
        )}
      </div>
      
      <div className="flex flex-wrap gap-1">
        {item.rationale.map((reason: string, idx: number) => (
          <span 
            key={idx}
            className="text-xs px-2 py-1 bg-accent/20 text-accent rounded"
          >
            {reason}
          </span>
        ))}
      </div>
    </Card>
  );

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-primary">Ritual Chamber</h2>
            <p className="text-sm text-muted-foreground">
              Channel the market forces through ancient runes
            </p>
          </div>
          <Button 
            onClick={handleRunRitual}
            disabled={isRunning}
            className="flex items-center gap-2"
            data-testid="button-run-ritual"
          >
            {isRunning ? (
              <>
                <Sparkles className="w-4 h-4 animate-spin" />
                Channeling...
              </>
            ) : (
              <>
                <PlayCircle className="w-4 h-4" />
                Begin Ritual
              </>
            )}
          </Button>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold mb-3 text-primary">Equity Watchlist</h3>
            <div className="flex flex-wrap gap-2">
              {watchlists.equities.map((ticker) => (
                <Badge key={ticker} variant="outline" className="text-xs">
                  {ticker}
                </Badge>
              ))}
            </div>
          </div>
          
          <div>
            <h3 className="font-semibold mb-3 text-primary">FX Pairs</h3>
            <div className="flex flex-wrap gap-2">
              {watchlists.fx.map((pair) => (
                <Badge key={pair} variant="outline" className="text-xs">
                  {pair}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {result && (
        <Card className="p-6">
          <h3 className="text-lg font-bold mb-4 text-primary">Ritual Results</h3>
          
          <div className="mb-6">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>Date: {result.ritual.date}</span>
              <span>Seed: {result.ritual.seed}</span>
              <div className="flex gap-2">
                {result.ritual.runes.map((rune) => (
                  <Badge key={rune.id} style={{ backgroundColor: rune.color + '20', color: rune.color }}>
                    {rune.name}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          <Separator className="mb-6" />

          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-3">Equities</h4>
              
              {result.results.equities.conservative.length > 0 && (
                <div className="mb-4">
                  <h5 className="text-sm text-green-400 mb-2">Conservative</h5>
                  <div className="space-y-2">
                    {result.results.equities.conservative.map((item, idx) => (
                      <ResultCard key={idx} item={item} type="equity" />
                    ))}
                  </div>
                </div>
              )}
              
              {result.results.equities.risky.length > 0 && (
                <div>
                  <h5 className="text-sm text-amber-400 mb-2">High Risk</h5>
                  <div className="space-y-2">
                    {result.results.equities.risky.map((item, idx) => (
                      <ResultCard key={idx} item={item} type="equity" />
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div>
              <h4 className="font-semibold mb-3">Foreign Exchange</h4>
              
              {result.results.fx.conservative.length > 0 && (
                <div className="mb-4">
                  <h5 className="text-sm text-green-400 mb-2">Conservative</h5>
                  <div className="space-y-2">
                    {result.results.fx.conservative.map((item, idx) => (
                      <ResultCard key={idx} item={item} type="fx" />
                    ))}
                  </div>
                </div>
              )}
              
              {result.results.fx.risky.length > 0 && (
                <div>
                  <h5 className="text-sm text-amber-400 mb-2">High Risk</h5>
                  <div className="space-y-2">
                    {result.results.fx.risky.map((item, idx) => (
                      <ResultCard key={idx} item={item} type="fx" />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}