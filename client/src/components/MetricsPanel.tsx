import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Activity, Target, TrendingUp, Clock, Zap, RefreshCw } from "lucide-react";

interface MetricsSnapshot {
  day: {
    uniqueSources: number;
    uniqueSignals: number;
    fxShiftAbs: number;
    accuracy: { acc: number | null; n: number };
  };
  week: {
    uniqueSources: number;
    uniqueSignals: number; 
    fxShiftAbs: number;
    accuracy: { acc: number | null; n: number };
  };
  month: {
    uniqueSources: number;
    uniqueSignals: number;
    fxShiftAbs: number;
    accuracy: { acc: number | null; n: number };
  };
  lifetime: {
    uniqueSources: number;
    uniqueSignals: number;
    fxShiftAbs: number;
    accuracy: { acc: number | null; n: number };
  };
}

interface DailyOracle {
  ciphergram: string;
  note: string;
}

export default function MetricsPanel() {
  const [metrics, setMetrics] = useState<MetricsSnapshot | null>(null);
  const [oracle, setOracle] = useState<DailyOracle | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchMetrics = () => {
    setIsRefreshing(true);
    console.log('Fetching metrics and oracle...');
    
    setTimeout(() => {
      // Mock metrics data
      const mockMetrics: MetricsSnapshot = {
        day: {
          uniqueSources: 12,
          uniqueSignals: 34,
          fxShiftAbs: 2.45,
          accuracy: { acc: 0.73, n: 15 }
        },
        week: {
          uniqueSources: 67,
          uniqueSignals: 142,
          fxShiftAbs: 18.72,
          accuracy: { acc: 0.68, n: 89 }
        },
        month: {
          uniqueSources: 234,
          uniqueSignals: 587,
          fxShiftAbs: 67.34,
          accuracy: { acc: 0.71, n: 312 }
        },
        lifetime: {
          uniqueSources: 1456,
          uniqueSignals: 3789,
          fxShiftAbs: 445.67,
          accuracy: { acc: 0.69, n: 2134 }
        }
      };

      const mockOracle: DailyOracle = {
        ciphergram: "⟟Σ Q2F4N8D7·R9B3M1C6·H5K2L8P4·W7V9X3 Σ⟟",
        note: 'Litany (ascending): "Vectors converge; witnesses veiled."'
      };

      setMetrics(mockMetrics);
      setOracle(mockOracle);
      setIsRefreshing(false);
    }, 1200);
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const getAccuracyColor = (acc: number | null) => {
    if (acc === null) return "text-muted-foreground";
    if (acc >= 0.7) return "text-green-400";
    if (acc >= 0.6) return "text-yellow-400";
    return "text-red-400";
  };

  const getConfidenceTone = (acc: number | null) => {
    if (acc === null) return "neutral";
    if (acc > 0.6) return "ascending";
    if (acc > 0.52) return "tempered";
    return "probing";
  };

  const formatPercentage = (acc: number | null) => {
    return acc ? `${(acc * 100).toFixed(1)}%` : "—";
  };

  return (
    <div className="space-y-6">
      {/* Daily Oracle */}
      {oracle && (
        <Card className="p-6 bg-gradient-to-r from-primary/5 to-accent/5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-primary flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Daily Oracle
            </h2>
            <Badge variant="secondary" className="text-xs">
              {getConfidenceTone(metrics?.lifetime.accuracy.acc ?? null)}
            </Badge>
          </div>
          
          <div className="text-center">
            <div className="font-mono text-accent text-lg mb-3 break-all">
              {oracle.ciphergram}
            </div>
            <p className="text-sm text-muted-foreground italic">
              {oracle.note}
            </p>
          </div>
        </Card>
      )}

      {/* Metrics */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-primary flex items-center gap-2">
            <Activity className="w-5 h-5" />
            System Metrics
          </h2>
          <Button 
            onClick={fetchMetrics}
            disabled={isRefreshing}
            size="sm"
            variant="outline"
            data-testid="button-refresh-metrics"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {metrics && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Day */}
            <div>
              <h3 className="font-semibold mb-3 text-primary flex items-center gap-2">
                <Clock className="w-4 h-4" />
                24h
              </h3>
              <div className="space-y-3">
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className="text-xl font-mono text-cyan-400">
                    {metrics.day.uniqueSources}
                  </div>
                  <div className="text-xs text-muted-foreground">Sources</div>
                </div>
                
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className="text-xl font-mono text-purple-400">
                    {metrics.day.uniqueSignals}
                  </div>
                  <div className="text-xs text-muted-foreground">Signals</div>
                </div>
                
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className={`text-xl font-mono ${getAccuracyColor(metrics.day.accuracy.acc)}`}>
                    {formatPercentage(metrics.day.accuracy.acc)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Accuracy ({metrics.day.accuracy.n})
                  </div>
                </div>
              </div>
            </div>

            {/* Week */}
            <div>
              <h3 className="font-semibold mb-3 text-primary">7d</h3>
              <div className="space-y-3">
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className="text-xl font-mono text-cyan-400">
                    {metrics.week.uniqueSources}
                  </div>
                  <div className="text-xs text-muted-foreground">Sources</div>
                </div>
                
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className="text-xl font-mono text-purple-400">
                    {metrics.week.uniqueSignals}
                  </div>
                  <div className="text-xs text-muted-foreground">Signals</div>
                </div>
                
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className={`text-xl font-mono ${getAccuracyColor(metrics.week.accuracy.acc)}`}>
                    {formatPercentage(metrics.week.accuracy.acc)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Accuracy ({metrics.week.accuracy.n})
                  </div>
                </div>
              </div>
            </div>

            {/* Month */}
            <div>
              <h3 className="font-semibold mb-3 text-primary">30d</h3>
              <div className="space-y-3">
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className="text-xl font-mono text-cyan-400">
                    {metrics.month.uniqueSources}
                  </div>
                  <div className="text-xs text-muted-foreground">Sources</div>
                </div>
                
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className="text-xl font-mono text-purple-400">
                    {metrics.month.uniqueSignals}
                  </div>
                  <div className="text-xs text-muted-foreground">Signals</div>
                </div>
                
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className={`text-xl font-mono ${getAccuracyColor(metrics.month.accuracy.acc)}`}>
                    {formatPercentage(metrics.month.accuracy.acc)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Accuracy ({metrics.month.accuracy.n})
                  </div>
                </div>
              </div>
            </div>

            {/* Lifetime */}
            <div>
              <h3 className="font-semibold mb-3 text-primary flex items-center gap-2">
                <Target className="w-4 h-4" />
                All Time
              </h3>
              <div className="space-y-3">
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className="text-xl font-mono text-cyan-400">
                    {metrics.lifetime.uniqueSources.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted-foreground">Sources</div>
                </div>
                
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className="text-xl font-mono text-purple-400">
                    {metrics.lifetime.uniqueSignals.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted-foreground">Signals</div>
                </div>
                
                <div className="text-center p-3 bg-card/50 rounded-lg">
                  <div className={`text-xl font-mono ${getAccuracyColor(metrics.lifetime.accuracy.acc)}`}>
                    {formatPercentage(metrics.lifetime.accuracy.acc)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Accuracy ({metrics.lifetime.accuracy.n.toLocaleString()})
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}