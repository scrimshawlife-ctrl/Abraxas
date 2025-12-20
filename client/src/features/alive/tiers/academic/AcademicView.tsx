/**
 * ALIVE Academic Tier View
 *
 * Comprehensive lens: Full metric visibility, provenance, strain reports.
 * Designed for research and method transparency.
 */

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

interface AcademicViewProps {
  userId?: string;
}

export default function AcademicView({ userId }: AcademicViewProps) {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/alive/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subjectId: userId || "current_user",
          tier: "academic",
          corpusConfig: {
            sources: ["twitter", "github"],
          },
          metricConfig: {
            enableProvisional: true,
            enableStrain: true,
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

  const exportData = async (format: "json" | "csv") => {
    try {
      const response = await fetch("/api/alive/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysisId: analysis?.analysisId,
          format,
          tier: "academic",
          options: {
            includeProvenance: true,
            includeStrainReport: true,
          },
        }),
      });

      const result = await response.json();
      if (result.success) {
        window.open(result.data.downloadUrl, "_blank");
      }
    } catch (error) {
      console.error("Error exporting:", error);
    }
  };

  const renderMetric = (metric: any) => (
    <div key={metric.metricId} className="space-y-2 p-4 border rounded">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="font-mono text-xs text-muted-foreground">{metric.metricId}</p>
          <p className="text-sm">v{metric.metricVersion}</p>
        </div>
        <Badge variant={metric.status === "promoted" ? "default" : "secondary"}>
          {metric.status}
        </Badge>
      </div>
      <div className="space-y-1">
        <div className="flex items-center justify-between text-sm">
          <span>Value: {metric.value.toFixed(3)}</span>
          <span>Confidence: {(metric.confidence * 100).toFixed(0)}%</span>
        </div>
        <Progress value={metric.value * 100} />
      </div>
    </div>
  );

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">ALIVE (Academic)</h1>
          <p className="text-muted-foreground">Full metric transparency and provenance</p>
        </div>
        <div className="space-x-2">
          {analysis && (
            <>
              <Button variant="outline" onClick={() => exportData("json")}>
                Export JSON
              </Button>
              <Button variant="outline" onClick={() => exportData("csv")}>
                Export CSV
              </Button>
            </>
          )}
          <Button onClick={runAnalysis} disabled={loading}>
            {loading ? "Running..." : "Run Analysis"}
          </Button>
        </div>
      </div>

      {analysis && (
        <Tabs defaultValue="metrics">
          <TabsList>
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
            <TabsTrigger value="provenance">Provenance</TabsTrigger>
            <TabsTrigger value="strain">Metric Strain</TabsTrigger>
          </TabsList>

          <TabsContent value="metrics" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Influence Metrics (I)</CardTitle>
                <CardDescription>Social gravity ↔ network position ↔ persuasive reach</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {analysis.influence?.map(renderMetric)}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Vitality Metrics (V)</CardTitle>
                <CardDescription>Creative momentum ↔ discourse velocity ↔ engagement coherence</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {analysis.vitality?.map(renderMetric)}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Life-Logistics Metrics (L)</CardTitle>
                <CardDescription>Lived cost ↔ material condition ↔ operational constraint</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {analysis.lifeLogistics?.map(renderMetric)}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="provenance">
            <Card>
              <CardHeader>
                <CardTitle>Corpus Provenance</CardTitle>
                <CardDescription>Source attribution and weighting</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analysis.corpusProvenance?.map((source: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <p className="font-medium">{source.sourceId}</p>
                        <p className="text-sm text-muted-foreground">{source.sourceType}</p>
                      </div>
                      <Badge>Weight: {source.weight.toFixed(2)}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="strain">
            <Card>
              <CardHeader>
                <CardTitle>Metric Strain Report</CardTitle>
                <CardDescription>Detection of emergent patterns not captured by existing metrics</CardDescription>
              </CardHeader>
              <CardContent>
                {analysis.metricStrain?.detected ? (
                  <div className="space-y-4">
                    <Badge variant="destructive">Strain Detected</Badge>
                    <p className="text-sm">{analysis.metricStrain.strainReport}</p>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No metric strain detected</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {!analysis && !loading && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            <p>Run an analysis to see full metric details and provenance</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
