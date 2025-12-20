/**
 * ALIVE Psychonaut Tier View
 *
 * Minimal lens: Essential field signature with intuitive presentation.
 * No provisional metrics, no internal IDs, minimal provenance.
 */

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface PsychonautViewProps {
  userId?: string;
}

export default function PsychonautView({ userId }: PsychonautViewProps) {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);

  const runAnalysis = async () => {
    setLoading(true);
    try {
      // TODO: Call ALIVE API
      const response = await fetch("/api/alive/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subjectId: userId || "current_user",
          tier: "psychonaut",
          corpusConfig: {
            sources: ["twitter", "github"],
          },
        }),
      });

      const result = await response.json();
      setAnalysis(result.data);
    } catch (error) {
      console.error("Error running analysis:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">ALIVE</h1>
          <p className="text-muted-foreground">Autonomous Life-Influence Vitality Engine</p>
        </div>
        <Button onClick={runAnalysis} disabled={loading}>
          {loading ? "Running..." : "Run Analysis"}
        </Button>
      </div>

      {analysis && (
        <div className="grid gap-4 md:grid-cols-3">
          {/* Influence Card */}
          <Card>
            <CardHeader>
              <CardTitle>Influence</CardTitle>
              <CardDescription>Social reach and impact</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analysis.influence?.map((metric: any, idx: number) => (
                <div key={idx} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">Score</span>
                    <span>{(metric.value * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={metric.value * 100} />
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Vitality Card */}
          <Card>
            <CardHeader>
              <CardTitle>Vitality</CardTitle>
              <CardDescription>Creative energy and momentum</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analysis.vitality?.map((metric: any, idx: number) => (
                <div key={idx} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">Score</span>
                    <span>{(metric.value * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={metric.value * 100} />
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Life-Logistics Card */}
          <Card>
            <CardHeader>
              <CardTitle>Life-Logistics</CardTitle>
              <CardDescription>Material conditions and capacity</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analysis.lifeLogistics?.map((metric: any, idx: number) => (
                <div key={idx} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">Score</span>
                    <span>{(metric.value * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={metric.value * 100} />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {analysis && (
        <Card>
          <CardHeader>
            <CardTitle>Composite Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-center">
              {(analysis.compositeScore?.overall * 100).toFixed(0)}%
            </div>
          </CardContent>
        </Card>
      )}

      {!analysis && !loading && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            <p>Run an analysis to see your ALIVE field signature</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
