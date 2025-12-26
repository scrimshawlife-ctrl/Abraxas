import { useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Eye, Brain, Building2, Globe, Calendar, TrendingUp, DollarSign } from "lucide-react";
import {
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

interface VCAnalysis {
  industry: string;
  region: string;
  horizon: number;
  forecast: {
    dealVolume: {
      prediction: number;
      confidence: number;
      factors: string[];
    };
    hotSectors: Array<{
      name: string;
      score: number;
      reasoning: string;
    }>;
    riskFactors: string[];
    opportunities: string[];
  };
  timestamp: number;
}

export default function VCOracle() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<VCAnalysis | null>(null);
  const [settings, setSettings] = useState({
    industry: "Technology",
    region: "US",
    horizonDays: 90
  });

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    console.log('Running VC analysis with settings:', settings);

    setTimeout(() => {
      // Mock VC analysis result
      const mockAnalysis: VCAnalysis = {
        industry: settings.industry,
        region: settings.region,
        horizon: settings.horizonDays,
        forecast: {
          dealVolume: {
            prediction: 847,
            confidence: 0.73,
            factors: ["Fed rate stability", "Public market recovery", "AI sector momentum"]
          },
          hotSectors: [
            { name: "Generative AI", score: 0.91, reasoning: "Enterprise adoption accelerating" },
            { name: "Climate Tech", score: 0.78, reasoning: "Policy tailwinds strengthening" },
            { name: "Biotech", score: 0.65, reasoning: "Pipeline maturation cycles" }
          ],
          riskFactors: [
            "Geopolitical tension escalation",
            "Interest rate volatility",
            "Late-stage valuation compression"
          ],
          opportunities: [
            "Corporate venture arm expansions",
            "Secondary market repricing",
            "Infrastructure software consolidation"
          ]
        },
        timestamp: Date.now()
      };

      setAnalysis(mockAnalysis);
      setIsAnalyzing(false);
    }, 3500);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "#00D4FF"; // cyan
    if (score >= 0.6) return "#F8FF59"; // yellow
    return "#FF3EF6"; // magenta
  };

  const getSigilTone = (score: number): "cyan" | "yellow" | "magenta" => {
    if (score >= 0.8) return "cyan";
    if (score >= 0.6) return "yellow";
    return "magenta";
  };

  return (
    <div className="aal-stack-lg">
      <AalCard>
        <div className="aal-stack-md">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <AalSigilFrame tone="yellow" size={40}>
                <Eye size={20} />
              </AalSigilFrame>
              <div>
                <h2 className="aal-heading-md">VC Oracle • Athena</h2>
                <p className="aal-body" style={{ fontSize: "13px", marginTop: "4px" }}>
                  Venture capital pattern recognition engine
                </p>
              </div>
            </div>

            <AalButton
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              variant="primary"
              leftIcon={<Brain size={16} className={isAnalyzing ? "animate-pulse" : ""} />}
              data-testid="button-analyze-vc"
            >
              {isAnalyzing ? "Analyzing..." : "Divine Markets"}
            </AalButton>
          </div>

          <AalDivider />

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
            <div>
              <label className="aal-body" style={{ fontSize: "13px", marginBottom: "8px", display: "flex", alignItems: "center", gap: "4px" }}>
                <Building2 size={14} />
                Industry
              </label>
              <Select value={settings.industry} onValueChange={(value) => setSettings({...settings, industry: value})}>
                <SelectTrigger data-testid="select-industry">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Technology">Technology</SelectItem>
                  <SelectItem value="Healthcare">Healthcare</SelectItem>
                  <SelectItem value="Fintech">Fintech</SelectItem>
                  <SelectItem value="Climate">Climate Tech</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="aal-body" style={{ fontSize: "13px", marginBottom: "8px", display: "flex", alignItems: "center", gap: "4px" }}>
                <Globe size={14} />
                Region
              </label>
              <Select value={settings.region} onValueChange={(value) => setSettings({...settings, region: value})}>
                <SelectTrigger data-testid="select-region">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="US">North America</SelectItem>
                  <SelectItem value="EU">Europe</SelectItem>
                  <SelectItem value="APAC">Asia Pacific</SelectItem>
                  <SelectItem value="Global">Global</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="aal-body" style={{ fontSize: "13px", marginBottom: "8px", display: "flex", alignItems: "center", gap: "4px" }}>
                <Calendar size={14} />
                Horizon (Days)
              </label>
              <Select value={settings.horizonDays.toString()} onValueChange={(value) => setSettings({...settings, horizonDays: parseInt(value)})}>
                <SelectTrigger data-testid="select-horizon">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="30">30 Days</SelectItem>
                  <SelectItem value="90">90 Days</SelectItem>
                  <SelectItem value="180">180 Days</SelectItem>
                  <SelectItem value="365">1 Year</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </AalCard>

      {analysis && (
        <AalCard>
          <div className="aal-stack-md">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
              <h3 className="aal-heading-md">Oracle Vision</h3>
              <div className="aal-row-sm">
                <AalTag>{analysis.industry}</AalTag>
                <AalTag>{analysis.region}</AalTag>
                <AalTag>{analysis.horizon} days</AalTag>
              </div>
            </div>

            <AalDivider />

            {/* Deal Volume Forecast */}
            <div className="aal-stack-md">
              <h4 className="aal-heading-md" style={{ fontSize: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
                <DollarSign size={16} />
                Deal Volume Forecast
              </h4>
              <AalCard variant="ghost">
                <div className="aal-stack-md">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
                    <span className="aal-heading-md" style={{ fontSize: "28px", color: "var(--aal-color-cyan)" }}>
                      ${analysis.forecast.dealVolume.prediction}M
                    </span>
                    <AalTag>
                      {(analysis.forecast.dealVolume.confidence * 100).toFixed(0)}% confidence
                    </AalTag>
                  </div>
                  <div className="aal-row-sm">
                    {analysis.forecast.dealVolume.factors.map((factor, idx) => (
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
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              </AalCard>
            </div>

            <AalDivider />

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "24px" }}>
              {/* Hot Sectors */}
              <div className="aal-stack-md">
                <h4 className="aal-heading-md" style={{ fontSize: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
                  <TrendingUp size={16} />
                  Hot Sectors
                </h4>
                <div className="aal-stack-md">
                  {analysis.forecast.hotSectors.map((sector, idx) => (
                    <AalCard key={idx} variant="ghost" padding="12px">
                      <div className="aal-stack-md">
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <AalSigilFrame tone={getSigilTone(sector.score)} size={24}>
                              <TrendingUp size={12} />
                            </AalSigilFrame>
                            <span className="aal-heading-md" style={{ fontSize: "14px" }}>
                              {sector.name}
                            </span>
                          </div>
                          <span
                            className="aal-body"
                            style={{
                              fontFamily: "monospace",
                              fontSize: "13px",
                              color: getScoreColor(sector.score)
                            }}
                          >
                            {(sector.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="aal-body" style={{ fontSize: "12px" }}>
                          {sector.reasoning}
                        </p>
                      </div>
                    </AalCard>
                  ))}
                </div>
              </div>

              {/* Risks & Opportunities */}
              <div className="aal-stack-lg">
                <div className="aal-stack-md">
                  <h4 className="aal-heading-md" style={{ fontSize: "16px", color: "#FF3EF6" }}>
                    Risk Factors
                  </h4>
                  <div className="aal-stack-md">
                    {analysis.forecast.riskFactors.map((risk, idx) => (
                      <div
                        key={idx}
                        className="aal-body"
                        style={{
                          fontSize: "13px",
                          padding: "8px 12px",
                          background: "rgba(255, 62, 246, 0.08)",
                          border: "1px solid rgba(255, 62, 246, 0.2)",
                          borderRadius: "6px"
                        }}
                      >
                        {risk}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="aal-stack-md">
                  <h4 className="aal-heading-md" style={{ fontSize: "16px", color: "#00D4FF" }}>
                    Opportunities
                  </h4>
                  <div className="aal-stack-md">
                    {analysis.forecast.opportunities.map((opp, idx) => (
                      <div
                        key={idx}
                        className="aal-body"
                        style={{
                          fontSize: "13px",
                          padding: "8px 12px",
                          background: "rgba(0, 212, 255, 0.08)",
                          border: "1px solid rgba(0, 212, 255, 0.2)",
                          borderRadius: "6px"
                        }}
                      >
                        {opp}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </AalCard>
      )}
    </div>
  );
}
