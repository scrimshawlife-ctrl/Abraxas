import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
import {
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

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

function WatchlistCard({ watchlistData, onRefresh }: { watchlistData: WatchlistWithItems; onRefresh: () => void }) {
  const { watchlist, items } = watchlistData;

  const getRiskTone = (risk: string): "cyan" | "yellow" | "magenta" => {
    switch (risk) {
      case "low": return "cyan";
      case "medium": return "yellow";
      case "high": return "magenta";
      default: return "yellow";
    }
  };

  const getScoreColor = (score: number, type: string) => {
    if (type === "growth") {
      return score > 0.6 ? "var(--aal-color-cyan)" :
             score > 0.3 ? "var(--aal-color-yellow)" :
             "var(--aal-color-muted)";
    } else {
      return Math.abs(score) > 0.6 ? "var(--aal-color-magenta)" :
             Math.abs(score) > 0.3 ? "var(--aal-color-yellow)" :
             "var(--aal-color-muted)";
    }
  };

  return (
    <AalCard data-testid={`watchlist-${watchlist.type}`}>
      <div className="aal-stack-md">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <AalSigilFrame tone={watchlist.type === "growth" ? "cyan" : "magenta"} size={36}>
              {watchlist.type === "growth" ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
            </AalSigilFrame>
            <div>
              <h3 className="aal-heading-md" data-testid={`text-watchlist-name-${watchlist.id}`}>
                {watchlist.name}
              </h3>
              <p className="aal-body" style={{ fontSize: "12px" }} data-testid={`text-watchlist-description-${watchlist.id}`}>
                {watchlist.description || `${watchlist.type} analysis watchlist`}
              </p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <AalTag data-testid={`badge-item-count-${watchlist.id}`}>{items.length} items</AalTag>
            <AalButton
              onClick={onRefresh}
              variant="ghost"
              leftIcon={<RefreshCw size={14} />}
              data-testid={`button-refresh-${watchlist.id}`}
            >
              Refresh
            </AalButton>
          </div>
        </div>

        {watchlist.lastAnalyzed && (
          <p className="aal-body" style={{ fontSize: "11px" }} data-testid={`text-last-analyzed-${watchlist.id}`}>
            Last analyzed: {new Date(watchlist.lastAnalyzed).toLocaleString()}
          </p>
        )}

        <AalDivider />

        <div className="aal-stack-md">
          {items.length === 0 ? (
            <p className="aal-body" style={{ textAlign: "center", padding: "24px" }} data-testid={`text-empty-${watchlist.id}`}>
              No items in this watchlist yet.
            </p>
          ) : (
            items
              .sort((a, b) => Math.abs(b.analysisScore) - Math.abs(a.analysisScore))
              .map((item) => (
                <AalCard
                  key={item.id}
                  variant="ghost"
                  padding="12px"
                  data-testid={`item-${item.symbol}`}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span className="aal-heading-md" style={{ fontSize: "14px" }} data-testid={`text-symbol-${item.symbol}`}>
                          {item.symbol}
                        </span>
                        <AalTag>{item.symbolType}</AalTag>
                        {item.sector && (
                          <AalTag data-testid={`badge-sector-${item.symbol}`}>{item.sector}</AalTag>
                        )}
                      </div>
                      <p className="aal-body" style={{ fontSize: "12px", marginTop: "4px" }} data-testid={`text-rationale-${item.symbol}`}>
                        {item.rationale}
                      </p>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                      <div style={{ textAlign: "right" }}>
                        <div
                          className="aal-heading-md"
                          style={{
                            fontSize: "16px",
                            fontFamily: "monospace",
                            color: getScoreColor(item.analysisScore, watchlist.type)
                          }}
                        >
                          {watchlist.type === "growth" ? "+" : ""}{(item.analysisScore * 100).toFixed(1)}%
                        </div>
                        <div className="aal-body" style={{ fontSize: "11px" }}>
                          {(item.confidence * 100).toFixed(0)}% confidence
                        </div>
                      </div>
                      <AalSigilFrame tone={getRiskTone(item.riskLevel)} size={28} data-testid={`icon-risk-${item.symbol}`}>
                        <span style={{ fontSize: "10px" }}>{item.riskLevel[0].toUpperCase()}</span>
                      </AalSigilFrame>
                    </div>
                  </div>
                </AalCard>
              ))
          )}
        </div>
      </div>
    </AalCard>
  );
}

export default function DynamicWatchlist() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"growth" | "short">("growth");

  // Fetch all watchlists for authenticated user
  const { data: watchlistsData, isLoading, error } = useQuery({
    queryKey: ["/api/watchlists"],
    queryFn: async () => {
      const response = await fetch("/api/watchlists");
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
          analysisType,
          limit: 8
        })
      });
      if (!response.ok) throw new Error("Failed to generate watchlist");
      return await response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/watchlists"] });
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
      <AalCard>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", padding: "48px" }}>
          <RefreshCw size={16} className="animate-spin" />
          <span className="aal-body">Loading watchlists...</span>
        </div>
      </AalCard>
    );
  }

  if (error) {
    return (
      <AalCard>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", padding: "48px", color: "var(--aal-color-magenta)" }}>
          <AlertTriangle size={16} />
          <span>Failed to load watchlists</span>
        </div>
      </AalCard>
    );
  }

  return (
    <div className="aal-stack-lg" data-testid="dynamic-watchlist">
      <AalCard>
        <div className="aal-stack-md">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", flexWrap: "wrap", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <AalSigilFrame tone="cyan" size={48}>
                <TrendingUp size={24} />
              </AalSigilFrame>
              <div>
                <h2 className="aal-heading-md" data-testid="text-watchlist-title">Dynamic Market Watchlists</h2>
                <p className="aal-body" style={{ fontSize: "13px", marginTop: "4px" }} data-testid="text-watchlist-subtitle">
                  AI-powered analysis of growth opportunities and short candidates
                </p>
              </div>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <AalButton
                onClick={() => handleGenerateWatchlist("growth")}
                disabled={generateWatchlistMutation.isPending}
                variant="primary"
                leftIcon={generateWatchlistMutation.isPending ? <RefreshCw size={14} className="animate-spin" /> : <TrendingUp size={14} />}
                data-testid="button-generate-growth"
              >
                Generate Growth
              </AalButton>
              <AalButton
                onClick={() => handleGenerateWatchlist("short")}
                disabled={generateWatchlistMutation.isPending}
                variant="secondary"
                leftIcon={generateWatchlistMutation.isPending ? <RefreshCw size={14} className="animate-spin" /> : <TrendingDown size={14} />}
                data-testid="button-generate-short"
              >
                Generate Short
              </AalButton>
            </div>
          </div>

          <AalDivider />

          {/* Tabs */}
          <div style={{ display: "flex", gap: "8px" }} data-testid="tabs-watchlist-types">
            <AalButton
              onClick={() => setActiveTab("growth")}
              variant={activeTab === "growth" ? "primary" : "ghost"}
              leftIcon={<TrendingUp size={14} />}
              data-testid="tab-growth"
            >
              Growth Opportunities
            </AalButton>
            <AalButton
              onClick={() => setActiveTab("short")}
              variant={activeTab === "short" ? "primary" : "ghost"}
              leftIcon={<TrendingDown size={14} />}
              data-testid="tab-short"
            >
              Short Candidates
            </AalButton>
          </div>
        </div>
      </AalCard>

      {/* Tab Content */}
      {activeTab === "growth" && (
        growthWatchlist ? (
          <WatchlistCard
            watchlistData={{
              watchlist: growthWatchlist,
              items: growthItems
            }}
            onRefresh={() => handleRefreshWatchlist(growthWatchlist.id)}
          />
        ) : (
          <AalCard>
            <div style={{ textAlign: "center", padding: "48px" }}>
              <AalSigilFrame tone="cyan" size={56} style={{ margin: "0 auto 16px" }}>
                <TrendingUp size={28} />
              </AalSigilFrame>
              <h3 className="aal-heading-md" style={{ marginBottom: "8px" }}>No Growth Watchlist Yet</h3>
              <p className="aal-body" style={{ marginBottom: "16px" }}>
                Generate a growth opportunities watchlist to see the most promising equity and FX opportunities.
              </p>
              <AalButton
                onClick={() => handleGenerateWatchlist("growth")}
                variant="primary"
                leftIcon={<TrendingUp size={14} />}
                data-testid="button-create-growth"
              >
                Create Growth Watchlist
              </AalButton>
            </div>
          </AalCard>
        )
      )}

      {activeTab === "short" && (
        shortWatchlist ? (
          <WatchlistCard
            watchlistData={{
              watchlist: shortWatchlist,
              items: shortItems
            }}
            onRefresh={() => handleRefreshWatchlist(shortWatchlist.id)}
          />
        ) : (
          <AalCard>
            <div style={{ textAlign: "center", padding: "48px" }}>
              <AalSigilFrame tone="magenta" size={56} style={{ margin: "0 auto 16px" }}>
                <TrendingDown size={28} />
              </AalSigilFrame>
              <h3 className="aal-heading-md" style={{ marginBottom: "8px" }}>No Short Watchlist Yet</h3>
              <p className="aal-body" style={{ marginBottom: "16px" }}>
                Generate a short candidates watchlist to identify potential short opportunities.
              </p>
              <AalButton
                onClick={() => handleGenerateWatchlist("short")}
                variant="secondary"
                leftIcon={<TrendingDown size={14} />}
                data-testid="button-create-short"
              >
                Create Short Watchlist
              </AalButton>
            </div>
          </AalCard>
        )
      )}
    </div>
  );
}
