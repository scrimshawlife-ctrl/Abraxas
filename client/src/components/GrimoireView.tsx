import { useState, useEffect } from "react";
import { History, Sparkles, Eye } from "lucide-react";
import {
  AalCard,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

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
    <div className="aal-stack-lg">
      <AalCard>
        <div className="aal-stack-md">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <AalSigilFrame tone="yellow" size={48}>
              <History size={24} />
            </AalSigilFrame>
            <div>
              <h1 className="aal-heading-xl">Grimoire</h1>
              <p className="aal-body" style={{ fontSize: "13px", marginTop: "4px" }}>
                Archive of rituals, sigils, and mystical workings
              </p>
            </div>
          </div>

          <AalDivider />

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
            {/* Ritual History */}
            <div className="aal-stack-md">
              <h2 className="aal-heading-md" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Sparkles size={16} />
                Ritual Records
              </h2>

              <div className="aal-stack-md">
                {rituals.map((ritual) => (
                  <AalCard
                    key={ritual.id}
                    variant="ghost"
                    padding="16px"
                    onClick={() => setSelectedRitual(ritual)}
                    style={{
                      cursor: "pointer",
                      border: selectedRitual?.id === ritual.id ? "1px solid var(--aal-color-cyan)" : undefined
                    }}
                    data-testid={`ritual-record-${ritual.id}`}
                  >
                    <div className="aal-stack-md">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                        <div>
                          <div className="aal-heading-md" style={{ fontSize: "14px" }}>{ritual.date}</div>
                          <div className="aal-body" style={{ fontSize: "12px" }}>
                            Seed: {ritual.seed}
                          </div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div className="aal-body" style={{ fontSize: "11px" }}>
                            {formatDate(ritual.created_at)}
                          </div>
                          {ritual.results && (
                            <AalTag style={{ marginTop: "4px" }}>
                              {getTotalPredictions(ritual)} predictions
                            </AalTag>
                          )}
                        </div>
                      </div>

                      {ritual.runes && (
                        <div style={{ display: "flex", gap: "4px" }}>
                          {ritual.runes.map((rune) => (
                            <div
                              key={rune.id}
                              style={{
                                width: "8px",
                                height: "8px",
                                borderRadius: "50%",
                                backgroundColor: rune.color
                              }}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  </AalCard>
                ))}
              </div>
            </div>

            {/* Sigil Archive */}
            <div className="aal-stack-md">
              <h2 className="aal-heading-md" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Eye size={16} />
                Sigil Archive
              </h2>

              <div className="aal-stack-md">
                {sigils.map((sigil) => (
                  <AalCard key={sigil.id} variant="ghost" padding="16px" data-testid={`sigil-record-${sigil.id}`}>
                    <div className="aal-stack-md">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div
                          className="aal-heading-md"
                          style={{ fontFamily: "monospace", color: "var(--aal-color-magenta)" }}
                        >
                          {sigil.core}
                        </div>
                        <div className="aal-body" style={{ fontSize: "11px" }}>
                          {formatDate(sigil.created_at)}
                        </div>
                      </div>

                      <div className="aal-body" style={{ fontSize: "11px", wordBreak: "break-all" }}>
                        {sigil.seed}
                      </div>

                      <AalTag>Grid 3x3 + Quadratic</AalTag>
                    </div>
                  </AalCard>
                ))}
              </div>
            </div>
          </div>
        </div>
      </AalCard>

      {/* Ritual Details */}
      {selectedRitual && selectedRitual.results && (
        <AalCard>
          <div className="aal-stack-md">
            <h3 className="aal-heading-md" style={{ color: "var(--aal-color-cyan)" }}>
              Ritual Details - {selectedRitual.date}
            </h3>

            <AalDivider />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
              <div className="aal-stack-md">
                <h4 className="aal-heading-md" style={{ fontSize: "14px" }}>Equity Predictions</h4>
                <div className="aal-stack-md">
                  {selectedRitual.results.equities.conservative.map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "8px 12px",
                        background: "rgba(0, 212, 255, 0.08)",
                        border: "1px solid rgba(0, 212, 255, 0.2)",
                        borderRadius: "6px",
                        fontSize: "13px"
                      }}
                    >
                      <span>{item.ticker}</span>
                      <div style={{ display: "flex", gap: "12px" }}>
                        <span style={{ color: "var(--aal-color-cyan)" }}>+{item.edge.toFixed(3)}</span>
                        <span className="aal-body">({item.confidence.toFixed(2)})</span>
                      </div>
                    </div>
                  ))}

                  {selectedRitual.results.equities.risky.map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "8px 12px",
                        background: "rgba(255, 62, 246, 0.08)",
                        border: "1px solid rgba(255, 62, 246, 0.2)",
                        borderRadius: "6px",
                        fontSize: "13px"
                      }}
                    >
                      <span>{item.ticker}</span>
                      <div style={{ display: "flex", gap: "12px" }}>
                        <span style={{ color: "var(--aal-color-magenta)" }}>{item.edge.toFixed(3)}</span>
                        <span className="aal-body">({item.confidence.toFixed(2)})</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="aal-stack-md">
                <h4 className="aal-heading-md" style={{ fontSize: "14px" }}>FX Predictions</h4>
                <div className="aal-stack-md">
                  {selectedRitual.results.fx.conservative.map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "8px 12px",
                        background: "rgba(0, 212, 255, 0.08)",
                        border: "1px solid rgba(0, 212, 255, 0.2)",
                        borderRadius: "6px",
                        fontSize: "13px"
                      }}
                    >
                      <span>{item.pair}</span>
                      <div style={{ display: "flex", gap: "12px" }}>
                        <span style={{ color: "var(--aal-color-cyan)" }}>+{item.edge.toFixed(3)}</span>
                        <span className="aal-body">({item.confidence.toFixed(2)})</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </AalCard>
      )}
    </div>
  );
}
