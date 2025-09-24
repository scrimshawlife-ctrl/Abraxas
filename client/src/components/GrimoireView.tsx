import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { History, Calendar, Sparkles, Eye } from "lucide-react";

interface RitualRecord {
  id: string;
  date: string;
  seed: string;
  created_at: number;
  runes?: Array<{
    id: string;
    name: string;
    color: string;
  }>;
  results?: {
    equities: {
      conservative: Array<{ ticker: string; edge: number; confidence: number }>;
      risky: Array<{ ticker: string; edge: number; confidence: number }>;
    };
    fx: {
      conservative: Array<{ pair: string; edge: number; confidence: number }>;
      risky: Array<{ pair: string; edge: number; confidence: number }>;
    };
  };
}

interface SigilRecord {
  id: string;
  core: string;
  seed: string;
  method: string;
  created_at: number;
}

export default function GrimoireView() {
  const [rituals, setRituals] = useState<RitualRecord[]>([]);
  const [sigils, setSigils] = useState<SigilRecord[]>([]);
  const [selectedRitual, setSelectedRitual] = useState<RitualRecord | null>(null);

  useEffect(() => {
    // Mock ritual history
    const mockRituals: RitualRecord[] = [
      {
        id: "ritual-001",
        date: "2025-01-15",
        seed: "847293",
        created_at: Date.now() - 86400000,
        runes: [
          { id: "aether", name: "Aether", color: "#FFD166" },
          { id: "tide", name: "Tide", color: "#4CC9F0" }
        ],
        results: {
          equities: {
            conservative: [
              { ticker: "AAPL", edge: 0.125, confidence: 0.73 },
              { ticker: "MSFT", edge: 0.087, confidence: 0.68 }
            ],
            risky: [
              { ticker: "TSLA", edge: -0.045, confidence: 0.42 }
            ]
          },
          fx: {
            conservative: [
              { pair: "EURUSD", edge: 0.032, confidence: 0.65 }
            ],
            risky: []
          }
        }
      },
      {
        id: "ritual-002", 
        date: "2025-01-14",
        seed: "592847",
        created_at: Date.now() - 172800000,
        runes: [
          { id: "ward", name: "Ward", color: "#F87171" },
          { id: "glyph", name: "Glyph", color: "#C6F6D5" }
        ]
      }
    ];

    const mockSigils: SigilRecord[] = [
      {
        id: "sigil-001",
        core: "PRFT",
        seed: "a7b3c9d2e8f1",
        method: "traditional_strip+grid3x3+seeded_quadratic",
        created_at: Date.now() - 3600000
      },
      {
        id: "sigil-002",
        core: "GRWTH",
        seed: "f1e8d2c9b3a7", 
        method: "traditional_strip+grid3x3+seeded_quadratic",
        created_at: Date.now() - 7200000
      }
    ];

    setRituals(mockRituals);
    setSigils(mockSigils);
  }, []);

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTotalPredictions = (ritual: RitualRecord) => {
    if (!ritual.results) return 0;
    return (
      ritual.results.equities.conservative.length +
      ritual.results.equities.risky.length +
      ritual.results.fx.conservative.length +
      ritual.results.fx.risky.length
    );
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <History className="w-6 h-6 text-primary" />
          <div>
            <h1 className="text-2xl font-bold text-primary">Grimoire</h1>
            <p className="text-sm text-muted-foreground">
              Archive of rituals, sigils, and mystical workings
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Ritual History */}
          <div>
            <h2 className="font-semibold mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              Ritual Records
            </h2>
            
            <div className="space-y-3">
              {rituals.map((ritual) => (
                <Card 
                  key={ritual.id}
                  className={`p-4 cursor-pointer hover-elevate ${
                    selectedRitual?.id === ritual.id ? 'ring-2 ring-primary' : ''
                  }`}
                  onClick={() => setSelectedRitual(ritual)}
                  data-testid={`ritual-record-${ritual.id}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="font-medium text-sm">{ritual.date}</div>
                      <div className="text-xs text-muted-foreground">
                        Seed: {ritual.seed}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-muted-foreground">
                        {formatDate(ritual.created_at)}
                      </div>
                      {ritual.results && (
                        <Badge variant="secondary" className="text-xs mt-1">
                          {getTotalPredictions(ritual)} predictions
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  {ritual.runes && (
                    <div className="flex gap-1">
                      {ritual.runes.map((rune) => (
                        <div 
                          key={rune.id}
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: rune.color }}
                        />
                      ))}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </div>

          {/* Sigil Archive */}
          <div>
            <h2 className="font-semibold mb-4 flex items-center gap-2">
              <Eye className="w-4 h-4" />
              Sigil Archive
            </h2>
            
            <div className="space-y-3">
              {sigils.map((sigil) => (
                <Card key={sigil.id} className="p-4" data-testid={`sigil-record-${sigil.id}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-mono text-primary font-medium">
                      {sigil.core}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatDate(sigil.created_at)}
                    </div>
                  </div>
                  
                  <div className="text-xs text-muted-foreground mb-2 break-all">
                    {sigil.seed}
                  </div>
                  
                  <Badge variant="outline" className="text-xs">
                    Grid 3x3 + Quadratic
                  </Badge>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Ritual Details */}
      {selectedRitual && selectedRitual.results && (
        <Card className="p-6">
          <h3 className="font-semibold mb-4 text-primary">
            Ritual Details • {selectedRitual.date}
          </h3>
          
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-3">Equity Predictions</h4>
              <div className="space-y-2">
                {selectedRitual.results.equities.conservative.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm p-2 bg-green-950/20 rounded">
                    <span>{item.ticker}</span>
                    <div className="flex gap-2">
                      <span className="text-green-400">+{item.edge.toFixed(3)}</span>
                      <span className="text-muted-foreground">({item.confidence.toFixed(2)})</span>
                    </div>
                  </div>
                ))}
                
                {selectedRitual.results.equities.risky.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm p-2 bg-red-950/20 rounded">
                    <span>{item.ticker}</span>
                    <div className="flex gap-2">
                      <span className="text-red-400">{item.edge.toFixed(3)}</span>
                      <span className="text-muted-foreground">({item.confidence.toFixed(2)})</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium mb-3">FX Predictions</h4>
              <div className="space-y-2">
                {selectedRitual.results.fx.conservative.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm p-2 bg-green-950/20 rounded">
                    <span>{item.pair}</span>
                    <div className="flex gap-2">
                      <span className="text-green-400">+{item.edge.toFixed(3)}</span>
                      <span className="text-muted-foreground">({item.confidence.toFixed(2)})</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}