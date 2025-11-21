import { useState, useEffect } from "react";
import { Activity, Target, Clock, Zap, RefreshCw } from "lucide-react";
import {
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

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

  const getAccuracyTone = (acc: number | null): "cyan" | "yellow" | "magenta" => {
    if (acc === null) return "yellow";
    if (acc >= 0.7) return "cyan";
    if (acc >= 0.6) return "yellow";
    return "magenta";
  };

  const getAccuracyColor = (acc: number | null) => {
    if (acc === null) return "var(--aal-color-muted)";
    if (acc >= 0.7) return "var(--aal-color-cyan)";
    if (acc >= 0.6) return "var(--aal-color-yellow)";
    return "var(--aal-color-magenta)";
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

  const renderMetricBlock = (
    label: string,
    value: string | number,
    color: string,
    subLabel?: string
  ) => (
    <AalCard variant="ghost" padding="12px" style={{ textAlign: "center" }}>
      <div
        className="aal-heading-md"
        style={{ fontSize: "20px", fontFamily: "monospace", color }}
      >
        {value}
      </div>
      <div className="aal-body" style={{ fontSize: "11px" }}>
        {label}
        {subLabel && <span> ({subLabel})</span>}
      </div>
    </AalCard>
  );

  const renderPeriodColumn = (
    title: string,
    data: MetricsSnapshot["day"],
    icon?: React.ReactNode
  ) => (
    <div className="aal-stack-md">
      <h3
        className="aal-heading-md"
        style={{ fontSize: "14px", display: "flex", alignItems: "center", gap: "8px" }}
      >
        {icon}
        {title}
      </h3>
      <div className="aal-stack-md">
        {renderMetricBlock("Sources", data.uniqueSources, "var(--aal-color-cyan)")}
        {renderMetricBlock("Signals", data.uniqueSignals, "var(--aal-color-magenta)")}
        {renderMetricBlock(
          "Accuracy",
          formatPercentage(data.accuracy.acc),
          getAccuracyColor(data.accuracy.acc),
          data.accuracy.n.toLocaleString()
        )}
      </div>
    </div>
  );

  return (
    <div className="aal-stack-lg">
      {/* Daily Oracle */}
      {oracle && (
        <AalCard>
          <div className="aal-stack-md">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <AalSigilFrame tone="yellow" size={40}>
                  <Zap size={20} />
                </AalSigilFrame>
                <h2 className="aal-heading-md">Daily Oracle</h2>
              </div>
              <AalTag>{getConfidenceTone(metrics?.lifetime.accuracy.acc ?? null)}</AalTag>
            </div>

            <AalDivider />

            <div style={{ textAlign: "center", padding: "16px 0" }}>
              <div
                className="aal-heading-md"
                style={{
                  fontFamily: "monospace",
                  fontSize: "18px",
                  color: "var(--aal-color-yellow)",
                  wordBreak: "break-all",
                  marginBottom: "12px"
                }}
              >
                {oracle.ciphergram}
              </div>
              <p className="aal-body" style={{ fontStyle: "italic", fontSize: "13px" }}>
                {oracle.note}
              </p>
            </div>
          </div>
        </AalCard>
      )}

      {/* System Metrics */}
      <AalCard>
        <div className="aal-stack-md">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <AalSigilFrame tone="cyan" size={40}>
                <Activity size={20} />
              </AalSigilFrame>
              <h2 className="aal-heading-md">System Metrics</h2>
            </div>
            <AalButton
              onClick={fetchMetrics}
              disabled={isRefreshing}
              variant="secondary"
              leftIcon={<RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />}
              data-testid="button-refresh-metrics"
            >
              Refresh
            </AalButton>
          </div>

          <AalDivider />

          {metrics && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "24px" }}>
              {renderPeriodColumn("24h", metrics.day, <Clock size={14} />)}
              {renderPeriodColumn("7d", metrics.week)}
              {renderPeriodColumn("30d", metrics.month)}
              {renderPeriodColumn("All Time", metrics.lifetime, <Target size={14} />)}
            </div>
          )}
        </div>
      </AalCard>
    </div>
  );
}
