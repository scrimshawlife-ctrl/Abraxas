import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RefreshCw, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
// Note: Will implement API requests directly for now

interface WatchlistItem {
  id: string;
  symbol: string;
  symbolType: "equity" | "fx";
  analysisScore: number;
  confidence: number;
  growthPotential?: number;
  shortPotential?: number;
  riskLevel: "low" | "medium" | "high";
  sector?: string;
  rationale: string;
  metadata: any;
  addedAt: string;
  lastUpdated: string;
}

interface Watchlist {
  id: string;
  name: string;
  type: "growth" | "short" | "custom";
  description?: string;
  isActive: boolean;
  lastAnalyzed?: string;
  createdAt: string;
  updatedAt: string;
}

interface WatchlistWithItems {
  watchlist: Watchlist;
  items: WatchlistItem[];
}

const MOCK_USER_ID = "test-user"; // For demo purposes

function WatchlistCard({ watchlistData, onRefresh }: { watchlistData: WatchlistWithItems; onRefresh: () => void }) {
  const { watchlist, items } = watchlistData;

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case "low": return "🟢";
      case "medium": return "🟡";
      case "high": return "🔴";
      default: return "⚪";
    }
  };

  const getScoreColor = (score: number, type: string) => {
    if (type === "growth") {
      return score > 0.6 ? "text-green-600 dark:text-green-400" : 
             score > 0.3 ? "text-yellow-600 dark:text-yellow-400" : 
             "text-gray-600 dark:text-gray-400";
    } else {
      return Math.abs(score) > 0.6 ? "text-red-600 dark:text-red-400" : 
             Math.abs(score) > 0.3 ? "text-orange-600 dark:text-orange-400" : 
             "text-gray-600 dark:text-gray-400";
    }
  };

  return (
    <Card className="w-full" data-testid={`watchlist-${watchlist.type}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="flex items-center gap-2" data-testid={`text-watchlist-name-${watchlist.id}`}>
            {watchlist.type === "growth" ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
            {watchlist.name}
          </CardTitle>
          <CardDescription data-testid={`text-watchlist-description-${watchlist.id}`}>
            {watchlist.description || `${watchlist.type} analysis watchlist`}
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" data-testid={`badge-item-count-${watchlist.id}`}>
            {items.length} items
          </Badge>
          <Button
            size="sm"
            variant="outline"
            onClick={onRefresh}
            data-testid={`button-refresh-${watchlist.id}`}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {watchlist.lastAnalyzed && (
          <p className="text-sm text-muted-foreground mb-4" data-testid={`text-last-analyzed-${watchlist.id}`}>
            Last analyzed: {new Date(watchlist.lastAnalyzed).toLocaleString()}
          </p>
        )}
        <div className="space-y-3">
          {items.length === 0 ? (
            <p className="text-muted-foreground text-center py-4" data-testid={`text-empty-${watchlist.id}`}>
              No items in this watchlist yet.
            </p>
          ) : (
            items
              .sort((a, b) => Math.abs(b.analysisScore) - Math.abs(a.analysisScore))
              .map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover-elevate"
                  data-testid={`item-${item.symbol}`}
                >
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium" data-testid={`text-symbol-${item.symbol}`}>
                          {item.symbol}
                        </span>
                        <Badge variant={item.symbolType === "equity" ? "default" : "secondary"}>
                          {item.symbolType}
                        </Badge>
                        {item.sector && (
                          <Badge variant="outline" data-testid={`badge-sector-${item.symbol}`}>
                            {item.sector}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1" data-testid={`text-rationale-${item.symbol}`}>
                        {item.rationale}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className={`font-semibold ${getScoreColor(item.analysisScore, watchlist.type)}`}>
                        {watchlist.type === "growth" ? "+" : ""}{(item.analysisScore * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {(item.confidence * 100).toFixed(0)}% confidence
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <span data-testid={`icon-risk-${item.symbol}`}>{getRiskIcon(item.riskLevel)}</span>
                      <span className="text-xs text-muted-foreground">{item.riskLevel}</span>
                    </div>
                  </div>
                </div>
              ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function DynamicWatchlist() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("growth");

  // Fetch all watchlists
  const { data: watchlistsData, isLoading, error } = useQuery({
    queryKey: ["/api/watchlists"],
    queryFn: async () => {
      const response = await fetch(`/api/watchlists?userId=${MOCK_USER_ID}`);
      if (!response.ok) {
        throw new Error("Failed to fetch watchlists");
      }
      return await response.json();
    }
  });

  // Process watchlists data first
  const watchlists = watchlistsData?.watchlists || [];
  const growthWatchlist = watchlists.find((w: Watchlist) => w.type === "growth");
  const shortWatchlist = watchlists.find((w: Watchlist) => w.type === "short");

  // Fetch items for growth watchlist
  const { data: growthItems = [] } = useQuery({
    queryKey: ["/api/watchlists", growthWatchlist?.id, "items"],
    queryFn: async () => {
      if (!growthWatchlist?.id) return [];
      const response = await fetch(`/api/watchlists/${growthWatchlist.id}/items`);
      if (!response.ok) throw new Error("Failed to fetch growth watchlist items");
      return await response.json();
    },
    enabled: !!growthWatchlist?.id
  });

  // Fetch items for short watchlist
  const { data: shortItems = [] } = useQuery({
    queryKey: ["/api/watchlists", shortWatchlist?.id, "items"],
    queryFn: async () => {
      if (!shortWatchlist?.id) return [];
      const response = await fetch(`/api/watchlists/${shortWatchlist.id}/items`);
      if (!response.ok) throw new Error("Failed to fetch short watchlist items");
      return await response.json();
    },
    enabled: !!shortWatchlist?.id
  });

  // Auto-generate watchlist mutation
  const generateWatchlistMutation = useMutation({
    mutationFn: async ({ analysisType }: { analysisType: "growth" | "short" }) => {
      const response = await fetch("/api/watchlists/auto-generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId: MOCK_USER_ID,
          analysisType,
          limit: 8
        })
      });
      if (!response.ok) throw new Error("Failed to generate watchlist");
      return await response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/watchlists"] });
      // Also invalidate items queries
      queryClient.invalidateQueries({ queryKey: ["/api/watchlists", undefined, "items"] });
    }
  });

  // Refresh watchlist mutation
  const refreshWatchlistMutation = useMutation({
    mutationFn: async (watchlistId: string) => {
      const response = await fetch(`/api/watchlists/${watchlistId}/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (!response.ok) throw new Error("Failed to refresh watchlist");
      return await response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/watchlists"] });
      // Also invalidate items queries
      queryClient.invalidateQueries({ queryKey: ["/api/watchlists", undefined, "items"] });
    }
  });

  const handleGenerateWatchlist = (analysisType: "growth" | "short") => {
    generateWatchlistMutation.mutate({ analysisType });
  };

  const handleRefreshWatchlist = (watchlistId: string) => {
    refreshWatchlistMutation.mutate(watchlistId);
  };


  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading watchlists...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-2 text-destructive">
            <AlertTriangle className="h-4 w-4" />
            <span>Failed to load watchlists</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full space-y-6" data-testid="dynamic-watchlist">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold" data-testid="text-watchlist-title">Dynamic Market Watchlists</h2>
          <p className="text-muted-foreground" data-testid="text-watchlist-subtitle">
            AI-powered analysis of growth opportunities and short candidates
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => handleGenerateWatchlist("growth")}
            disabled={generateWatchlistMutation.isPending}
            data-testid="button-generate-growth"
          >
            {generateWatchlistMutation.isPending ? (
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <TrendingUp className="h-4 w-4 mr-2" />
            )}
            Generate Growth
          </Button>
          <Button
            variant="outline"
            onClick={() => handleGenerateWatchlist("short")}
            disabled={generateWatchlistMutation.isPending}
            data-testid="button-generate-short"
          >
            {generateWatchlistMutation.isPending ? (
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <TrendingDown className="h-4 w-4 mr-2" />
            )}
            Generate Short
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2" data-testid="tabs-watchlist-types">
          <TabsTrigger value="growth" data-testid="tab-growth">
            <TrendingUp className="h-4 w-4 mr-2" />
            Growth Opportunities
          </TabsTrigger>
          <TabsTrigger value="short" data-testid="tab-short">
            <TrendingDown className="h-4 w-4 mr-2" />
            Short Candidates
          </TabsTrigger>
        </TabsList>

        <TabsContent value="growth" className="space-y-4">
          {growthWatchlist ? (
            <WatchlistCard
              watchlistData={{
                watchlist: growthWatchlist,
                items: growthItems
              }}
              onRefresh={() => handleRefreshWatchlist(growthWatchlist.id)}
            />
          ) : (
            <Card>
              <CardContent className="p-6 text-center">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No Growth Watchlist Yet</h3>
                <p className="text-muted-foreground mb-4">
                  Generate a growth opportunities watchlist to see the most promising equity and FX opportunities.
                </p>
                <Button onClick={() => handleGenerateWatchlist("growth")} data-testid="button-create-growth">
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Create Growth Watchlist
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="short" className="space-y-4">
          {shortWatchlist ? (
            <WatchlistCard
              watchlistData={{
                watchlist: shortWatchlist,
                items: shortItems
              }}
              onRefresh={() => handleRefreshWatchlist(shortWatchlist.id)}
            />
          ) : (
            <Card>
              <CardContent className="p-6 text-center">
                <TrendingDown className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No Short Watchlist Yet</h3>
                <p className="text-muted-foreground mb-4">
                  Generate a short candidates watchlist to identify potential short opportunities.
                </p>
                <Button 
                  variant="outline" 
                  onClick={() => handleGenerateWatchlist("short")}
                  data-testid="button-create-short"
                >
                  <TrendingDown className="h-4 w-4 mr-2" />
                  Create Short Watchlist
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}