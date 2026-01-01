import { useState } from "react";
import { PlayCircle, Sparkles, TrendingUp, TrendingDown } from "lucide-react";
import {
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

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
  const [watchlists] = useState({
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
    <AalCard variant="ghost" padding="12px">
      <div className="aal-stack-md">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
          <span className="aal-heading-md" style={{ fontSize: "14px" }}>
            {type === 'equity' ? item.ticker : item.pair}
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <AalSigilFrame
              tone={item.edge >= 0 ? "cyan" : "magenta"}
              size={24}
            >
              {item.edge >= 0 ?
                <TrendingUp size={12} /> :
                <TrendingDown size={12} />
              }
            </AalSigilFrame>
            <span
              className="aal-body"
              style={{
                fontFamily: "monospace",
                color: item.edge >= 0 ? "#00D4FF" : "#FF3EF6",
                fontSize: "13px"
              }}
            >
              {item.edge > 0 ? '+' : ''}{item.edge.toFixed(3)}
            </span>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <AalTag>{(item.confidence * 100).toFixed(0)}% conf</AalTag>
          {type === 'equity' && (
            <span className="aal-body" style={{ fontSize: "12px" }}>{item.sector}</span>
          )}
        </div>

        <div className="aal-row-sm">
          {item.rationale.map((reason: string, idx: number) => (
            <span
              key={idx}
              style={{
                fontSize: "11px",
                padding: "4px 8px",
                background: "rgba(0, 212, 255, 0.1)",
                color: "var(--aal-color-muted)",
                borderRadius: "4px"
              }}
            >
              {reason}
            </span>
          ))}
        </div>
      </div>
    </AalCard>
  );

  return (
    <div className="aal-stack-lg">
      <AalCard>
        <div className="aal-stack-md">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
            <div>
              <h2 className="aal-heading-md">Ritual Chamber</h2>
              <p className="aal-body" style={{ fontSize: "13px", marginTop: "4px" }}>
                Channel the market forces through ancient runes
              </p>
            </div>
            <AalButton
              onClick={handleRunRitual}
              disabled={isRunning}
              variant="primary"
              leftIcon={isRunning ? <Sparkles size={16} className={isRunning ? "animate-spin" : ""} /> : <PlayCircle size={16} />}
              data-testid="button-run-ritual"
            >
              {isRunning ? "Channeling..." : "Begin Ritual"}
            </AalButton>
          </div>

          <AalDivider />

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
            <div className="aal-stack-md">
              <h3 className="aal-heading-md" style={{ fontSize: "14px" }}>Equity Watchlist</h3>
              <div className="aal-row-sm">
                {watchlists.equities.map((ticker) => (
                  <AalTag key={ticker}>{ticker}</AalTag>
                ))}
              </div>
            </div>

            <div className="aal-stack-md">
              <h3 className="aal-heading-md" style={{ fontSize: "14px" }}>FX Pairs</h3>
              <div className="aal-row-sm">
                {watchlists.fx.map((pair) => (
                  <AalTag key={pair}>{pair}</AalTag>
                ))}
              </div>
            </div>
          </div>
        </div>
      </AalCard>

      {result && (
        <AalCard>
          <div className="aal-stack-md">
            <h3 className="aal-heading-md">Ritual Results</h3>

            <div className="aal-row-md" style={{ flexWrap: "wrap" }}>
              <span className="aal-body" style={{ fontSize: "13px" }}>
                Date: {result.ritual.date}
              </span>
              <span className="aal-body" style={{ fontSize: "13px" }}>
                Seed: {result.ritual.seed}
              </span>
              <div className="aal-row-sm">
                {result.ritual.runes.map((rune) => (
                  <AalTag key={rune.id}>{rune.name}</AalTag>
                ))}
              </div>
            </div>

            <AalDivider />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
              <div className="aal-stack-md">
                <h4 className="aal-heading-md" style={{ fontSize: "16px" }}>Equities</h4>

                {result.results.equities.conservative.length > 0 && (
                  <div className="aal-stack-md">
                    <h5 className="aal-body" style={{ color: "#00D4FF", fontSize: "13px" }}>
                      Conservative
                    </h5>
                    <div className="aal-stack-md">
                      {result.results.equities.conservative.map((item, idx) => (
                        <ResultCard key={idx} item={item} type="equity" />
                      ))}
                    </div>
                  </div>
                )}

                {result.results.equities.risky.length > 0 && (
                  <div className="aal-stack-md">
                    <h5 className="aal-body" style={{ color: "#F8FF59", fontSize: "13px" }}>
                      High Risk
                    </h5>
                    <div className="aal-stack-md">
                      {result.results.equities.risky.map((item, idx) => (
                        <ResultCard key={idx} item={item} type="equity" />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="aal-stack-md">
                <h4 className="aal-heading-md" style={{ fontSize: "16px" }}>Foreign Exchange</h4>

                {result.results.fx.conservative.length > 0 && (
                  <div className="aal-stack-md">
                    <h5 className="aal-body" style={{ color: "#00D4FF", fontSize: "13px" }}>
                      Conservative
                    </h5>
                    <div className="aal-stack-md">
                      {result.results.fx.conservative.map((item, idx) => (
                        <ResultCard key={idx} item={item} type="fx" />
                      ))}
                    </div>
                  </div>
                )}

                {result.results.fx.risky.length > 0 && (
                  <div className="aal-stack-md">
                    <h5 className="aal-body" style={{ color: "#F8FF59", fontSize: "13px" }}>
                      High Risk
                    </h5>
                    <div className="aal-stack-md">
                      {result.results.fx.risky.map((item, idx) => (
                        <ResultCard key={idx} item={item} type="fx" />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </AalCard>
      )}
    </div>
  );
}
