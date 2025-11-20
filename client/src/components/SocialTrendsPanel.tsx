import { useState, useEffect } from "react";
import { Scan, TrendingUp, Users, Hash, RefreshCw, Twitter, MessageCircle } from "lucide-react";
import {
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

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
    if (sentiment >= 0.7) return "#00D4FF"; // cyan
    if (sentiment >= 0.5) return "#F8FF59"; // yellow
    return "#FF3EF6"; // magenta
  };

  const getMomentumColor = (momentum: number) => {
    if (momentum >= 0.7) return "#00D4FF"; // cyan
    if (momentum >= 0.4) return "#F8FF59"; // yellow
    return "#FF3EF6"; // magenta
  };

  const getPlatformTone = (platform: string): "cyan" | "yellow" | "magenta" => {
    if (platform.toLowerCase().includes("twitter") || platform.toLowerCase().includes("x")) {
      return "cyan";
    }
    if (platform.toLowerCase().includes("reddit")) {
      return "magenta";
    }
    return "yellow";
  };

  const getPlatformIcon = (platform: string) => {
    if (platform.toLowerCase().includes("twitter") || platform.toLowerCase().includes("x")) {
      return <Twitter size={16} />;
    }
    if (platform.toLowerCase().includes("reddit")) {
      return <MessageCircle size={16} />;
    }
    return <Hash size={16} />;
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
    return volume.toString();
  };

  return (
    <AalCard>
      <div className="aal-stack-md">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", flexWrap: "wrap", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <AalSigilFrame tone="cyan" size={40}>
              <Hash size={20} />
            </AalSigilFrame>
            <div>
              <h2 className="aal-heading-md">Social Oracle</h2>
              <p className="aal-body" style={{ fontSize: "13px", marginTop: "4px" }}>
                Monitoring digital zeitgeist patterns
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {lastUpdate && (
              <span className="aal-body" style={{ fontSize: "12px" }}>
                Last: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
            <AalButton
              onClick={handleScan}
              disabled={isScanning}
              variant="secondary"
              leftIcon={isScanning ? <RefreshCw size={16} className="animate-spin" /> : <Scan size={16} />}
              data-testid="button-scan-trends"
            >
              {isScanning ? "Scanning..." : "Scan Now"}
            </AalButton>
          </div>
        </div>

        <AalDivider />

        {trends.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px 24px" }}>
            <AalSigilFrame tone="cyan" size={56} style={{ margin: "0 auto 16px" }}>
              <Users size={28} />
            </AalSigilFrame>
            <p className="aal-body">Initiate scan to reveal social currents</p>
          </div>
        ) : (
          <div className="aal-stack-lg">
            {trends.map((platformData, idx) => (
              <div key={idx} className="aal-stack-md">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <AalSigilFrame tone={getPlatformTone(platformData.platform)} size={24}>
                      {getPlatformIcon(platformData.platform)}
                    </AalSigilFrame>
                    <h3 className="aal-heading-md" style={{ fontSize: "16px" }}>
                      {platformData.platform}
                    </h3>
                  </div>
                  <AalTag>{platformData.trends.length} signals</AalTag>
                </div>

                <div className="aal-stack-md">
                  {platformData.trends.map((trend, trendIdx) => (
                    <AalCard key={trendIdx} variant="ghost" padding="16px">
                      <div className="aal-stack-md">
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
                          <span className="aal-heading-md" style={{ fontSize: "14px", display: "flex", alignItems: "center", gap: "4px" }}>
                            <Hash size={12} />
                            {trend.keyword}
                          </span>
                          <span className="aal-body" style={{ fontSize: "12px" }}>
                            {formatVolume(trend.volume)} mentions
                          </span>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", textAlign: "center" }}>
                          <div>
                            <div
                              className="aal-heading-md"
                              style={{
                                fontSize: "18px",
                                fontFamily: "monospace",
                                color: getMomentumColor(trend.momentum)
                              }}
                            >
                              {(trend.momentum * 100).toFixed(0)}%
                            </div>
                            <div className="aal-body" style={{ fontSize: "11px" }}>
                              Momentum
                            </div>
                          </div>

                          <div>
                            <div
                              className="aal-heading-md"
                              style={{
                                fontSize: "18px",
                                fontFamily: "monospace",
                                color: getSentimentColor(trend.sentiment)
                              }}
                            >
                              {trend.sentiment >= 0.5 ? '+' : ''}{((trend.sentiment - 0.5) * 200).toFixed(0)}%
                            </div>
                            <div className="aal-body" style={{ fontSize: "11px" }}>
                              Sentiment
                            </div>
                          </div>

                          <div>
                            <AalSigilFrame
                              tone={trend.momentum > 0.7 ? "cyan" : "yellow"}
                              size={28}
                              style={{ margin: "0 auto" }}
                            >
                              <TrendingUp size={14} />
                            </AalSigilFrame>
                            <div className="aal-body" style={{ fontSize: "11px", marginTop: "4px" }}>
                              Trending
                            </div>
                          </div>
                        </div>
                      </div>
                    </AalCard>
                  ))}
                </div>

                {idx < trends.length - 1 && <AalDivider />}
              </div>
            ))}
          </div>
        )}
      </div>
    </AalCard>
  );
}
