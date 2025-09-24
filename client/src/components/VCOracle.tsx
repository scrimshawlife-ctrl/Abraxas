import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Eye, Brain, Building2, Globe, Calendar, TrendingUp, DollarSign } from "lucide-react";

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
    if (score >= 0.8) return "text-emerald-400";
    if (score >= 0.6) return "text-cyan-400";
    if (score >= 0.4) return "text-yellow-400";
    return "text-red-400";
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-primary flex items-center gap-2">
              <Eye className="w-5 h-5" />
              VC Oracle • Athena
            </h2>
            <p className="text-sm text-muted-foreground">
              Venture capital pattern recognition engine
            </p>
          </div>
          
          <Button 
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="flex items-center gap-2"
            data-testid="button-analyze-vc"
          >
            {isAnalyzing ? (
              <>
                <Brain className="w-4 h-4 animate-pulse" />
                Analyzing...
              </>
            ) : (
              <>
                <Brain className="w-4 h-4" />
                Divine Markets
              </>
            )}
          </Button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium text-primary mb-2 block">
              <Building2 className="w-4 h-4 inline mr-1" />
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
            <label className="text-sm font-medium text-primary mb-2 block">
              <Globe className="w-4 h-4 inline mr-1" />
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
            <label className="text-sm font-medium text-primary mb-2 block">
              <Calendar className="w-4 h-4 inline mr-1" />
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
      </Card>

      {analysis && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-primary">Oracle Vision</h3>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span>{analysis.industry}</span>
              <span>•</span>
              <span>{analysis.region}</span>
              <span>•</span>
              <span>{analysis.horizon} days</span>
            </div>
          </div>

          {/* Deal Volume Forecast */}
          <div className="mb-6">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Deal Volume Forecast
            </h4>
            <Card className="p-4 bg-primary/5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl font-bold text-primary">
                  ${analysis.forecast.dealVolume.prediction}M
                </span>
                <Badge variant="secondary">
                  {(analysis.forecast.dealVolume.confidence * 100).toFixed(0)}% confidence
                </Badge>
              </div>
              <div className="flex flex-wrap gap-2">
                {analysis.forecast.dealVolume.factors.map((factor, idx) => (
                  <span key={idx} className="text-xs px-2 py-1 bg-accent/20 text-accent rounded">
                    {factor}
                  </span>
                ))}
              </div>
            </Card>
          </div>

          <Separator className="mb-6" />

          <div className="grid grid-cols-2 gap-6">
            {/* Hot Sectors */}
            <div>
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Hot Sectors
              </h4>
              <div className="space-y-3">
                {analysis.forecast.hotSectors.map((sector, idx) => (
                  <Card key={idx} className="p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">{sector.name}</span>
                      <span className={`text-sm font-mono ${getScoreColor(sector.score)}`}>
                        {(sector.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">{sector.reasoning}</p>
                  </Card>
                ))}
              </div>
            </div>

            {/* Risks & Opportunities */}
            <div className="space-y-6">
              <div>
                <h4 className="font-semibold mb-3 text-red-400">Risk Factors</h4>
                <div className="space-y-2">
                  {analysis.forecast.riskFactors.map((risk, idx) => (
                    <div key={idx} className="text-sm p-2 bg-red-950/20 border border-red-900/20 rounded">
                      {risk}
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-3 text-green-400">Opportunities</h4>
                <div className="space-y-2">
                  {analysis.forecast.opportunities.map((opp, idx) => (
                    <div key={idx} className="text-sm p-2 bg-green-950/20 border border-green-900/20 rounded">
                      {opp}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}