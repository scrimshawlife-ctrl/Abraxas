/**
 * ALIVE Enterprise Tier View
 *
 * Production lens: Actionable insights + integrations.
 * Includes export to all formats and Slack/email/webhook integrations.
 */

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

interface EnterpriseViewProps {
  userId?: string;
}

export default function EnterpriseView({ userId }: EnterpriseViewProps) {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [slackWebhook, setSlackWebhook] = useState("");
  const [slackEnabled, setSlackEnabled] = useState(false);

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/alive/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subjectId: userId || "current_user",
          tier: "enterprise",
          corpusConfig: {
            sources: ["twitter", "github", "linkedin"],
          },
        }),
      });

      const result = await response.json();
      setAnalysis(result.data);

      // Trigger Slack notification if enabled
      if (slackEnabled && slackWebhook) {
        await notifySlack(result.data);
      }
    } catch (error) {
      console.error("Error running analysis:", error);
    } finally {
      setLoading(false);
    }
  };

  const exportData = async (format: "json" | "csv" | "pdf") => {
    try {
      const response = await fetch("/api/alive/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysisId: analysis?.analysisId,
          format,
          tier: "enterprise",
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

  const notifySlack = async (data: any) => {
    try {
      await fetch("/api/alive/integrations/slack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tier: "enterprise",
          webhookUrl: slackWebhook,
          channel: "#alive-updates",
          fieldSignature: data,
        }),
      });
    } catch (error) {
      console.error("Error sending Slack notification:", error);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">ALIVE (Enterprise)</h1>
          <p className="text-muted-foreground">Production insights with integrations</p>
        </div>
        <div className="space-x-2">
          {analysis && (
            <>
              <Button variant="outline" onClick={() => exportData("json")}>
                JSON
              </Button>
              <Button variant="outline" onClick={() => exportData("csv")}>
                CSV
              </Button>
              <Button variant="outline" onClick={() => exportData("pdf")}>
                PDF
              </Button>
            </>
          )}
          <Button onClick={runAnalysis} disabled={loading}>
            {loading ? "Running..." : "Run Analysis"}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="dashboard">
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-4">
          {analysis && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Overall ALIVE Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-6xl font-bold text-center py-6">
                    {(analysis.compositeScore?.overall * 100).toFixed(0)}%
                  </div>
                  <div className="grid grid-cols-3 gap-4 mt-4">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Influence</p>
                      <p className="text-2xl font-semibold">
                        {(analysis.compositeScore?.influenceWeight * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Vitality</p>
                      <p className="text-2xl font-semibold">
                        {(analysis.compositeScore?.vitalityWeight * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Life-Logistics</p>
                      <p className="text-2xl font-semibold">
                        {(analysis.compositeScore?.lifeLogisticsWeight * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle>Influence</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {analysis.influence?.map((metric: any, idx: number) => (
                      <div key={idx}>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Score</span>
                          <span>{(metric.value * 100).toFixed(0)}%</span>
                        </div>
                        <Progress value={metric.value * 100} />
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Vitality</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {analysis.vitality?.map((metric: any, idx: number) => (
                      <div key={idx}>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Score</span>
                          <span>{(metric.value * 100).toFixed(0)}%</span>
                        </div>
                        <Progress value={metric.value * 100} />
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Life-Logistics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {analysis.lifeLogistics?.map((metric: any, idx: number) => (
                      <div key={idx}>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Score</span>
                          <span>{(metric.value * 100).toFixed(0)}%</span>
                        </div>
                        <Progress value={metric.value * 100} />
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </>
          )}

          {!analysis && !loading && (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                <p>Run an analysis to see your enterprise dashboard</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="integrations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Slack Integration</CardTitle>
              <CardDescription>Receive ALIVE updates in Slack channels</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="slack-enabled"
                  checked={slackEnabled}
                  onCheckedChange={setSlackEnabled}
                />
                <Label htmlFor="slack-enabled">Enable Slack notifications</Label>
              </div>
              {slackEnabled && (
                <div className="space-y-2">
                  <Label htmlFor="slack-webhook">Webhook URL</Label>
                  <Input
                    id="slack-webhook"
                    type="url"
                    placeholder="https://hooks.slack.com/services/..."
                    value={slackWebhook}
                    onChange={(e) => setSlackWebhook(e.target.value)}
                  />
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Email Notifications</CardTitle>
              <CardDescription>Email alerts for analysis completion</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Coming soon</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Webhook Integration</CardTitle>
              <CardDescription>Push ALIVE data to external systems</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Coming soon</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
