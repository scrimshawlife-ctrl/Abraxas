import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchComponentRegistry, postComponentApproval } from "@/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/hooks/use-toast";

type ComponentKind = "metrics" | "operators" | "artifacts";

interface ApprovalRecord {
  decision: "approved" | "needs-review" | "rejected";
  reviewer: string;
  reason: string;
  recorded_at: string;
}

interface ManifestSummary {
  id: string;
  kind: string;
  domain: string;
  description: string;
  owner_module: string;
  version: string;
  created_at: string;
  source_file: string;
}

interface ComponentRegistryResponse {
  generated_at: string;
  registry: Record<ComponentKind, string[]>;
  manifests: Record<ComponentKind, ManifestSummary[]>;
  unmanifested: Record<ComponentKind, string[]>;
  approvals: Record<string, ApprovalRecord>;
  rune_adaptations: RuneAdaptation[];
  totals: {
    registry_count: number;
    manifested_count: number;
    unmanifested_count: number;
  };
}

interface RuneAdaptation {
  module: string;
  capability_id: string;
  rune_id: string;
  status: "registered" | "pending";
  draft: boolean;
}

const kindLabels: Record<ComponentKind, string> = {
  metrics: "Metrics",
  operators: "Operators",
  artifacts: "Artifacts",
};

function decisionBadge(decision?: ApprovalRecord["decision"]) {
  if (decision === "approved") {
    return <Badge variant="secondary">Approved</Badge>;
  }
  if (decision === "rejected") {
    return <Badge variant="destructive">Rejected</Badge>;
  }
  if (decision === "needs-review") {
    return <Badge variant="outline">Needs Review</Badge>;
  }
  return <Badge variant="outline">Unreviewed</Badge>;
}

export default function GovernanceRegistry() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("");
  const [notes, setNotes] = useState<Record<string, string>>({});

  const { data, isLoading, error } = useQuery<ComponentRegistryResponse>({
    queryKey: ["component-registry"],
    queryFn: fetchComponentRegistry,
  });

  const approvalMutation = useMutation({
    mutationFn: postComponentApproval,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["component-registry"] });
      toast({ title: "Approval recorded", description: "Registry decision saved." });
    },
    onError: (err: Error) => {
      toast({ title: "Approval failed", description: err.message, variant: "destructive" });
    },
  });

  const filteredUnmanifested = useMemo(() => {
    if (!data) {
      return null;
    }
    const query = filter.trim().toLowerCase();
    const filtered: Record<ComponentKind, string[]> = {
      metrics: data.unmanifested.metrics,
      operators: data.unmanifested.operators,
      artifacts: data.unmanifested.artifacts,
    };
    if (!query) {
      return filtered;
    }
    (Object.keys(filtered) as ComponentKind[]).forEach((kind) => {
      filtered[kind] = filtered[kind].filter((module) => module.toLowerCase().includes(query));
    });
    return filtered;
  }, [data, filter]);

  const handleDecision = (module: string, decision: ApprovalRecord["decision"]) => {
    approvalMutation.mutate({
      module,
      decision,
      reason: notes[module] ?? "",
    });
  };

  if (isLoading) {
    return <div className="text-muted-foreground">Loading registry...</div>;
  }

  if (error || !data) {
    return <div className="text-destructive">Failed to load registry.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">Governance Registry</h1>
        <p className="text-sm text-muted-foreground">
          Review live component discovery and approve new modules as they surface.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Registry Total</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{data.totals.registry_count}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Manifested</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{data.totals.manifested_count}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Unmanifested</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{data.totals.unmanifested_count}</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Unmanifested Components</CardTitle>
            <p className="text-sm text-muted-foreground">
              Approve or flag modules that need rent manifests.
            </p>
          </div>
          <Input
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="Filter modules..."
            className="md:w-64"
          />
        </CardHeader>
        <CardContent className="space-y-6">
          {(Object.keys(kindLabels) as ComponentKind[]).map((kind) => {
            const modules = filteredUnmanifested?.[kind] ?? [];
            return (
              <div key={kind} className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">{kindLabels[kind]}</h3>
                  <Badge variant="outline">{modules.length} pending</Badge>
                </div>
                {modules.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No unmanifested modules found.</p>
                ) : (
                  <div className="space-y-4">
                    {modules.map((module) => {
                      const approval = data.approvals[module];
                      return (
                        <div key={module} className="rounded-lg border p-4">
                          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                            <div className="space-y-1">
                              <div className="font-medium">{module}</div>
                              <div className="text-xs text-muted-foreground">
                                {approval
                                  ? `Last review ${new Date(approval.recorded_at).toLocaleString()} by ${approval.reviewer}`
                                  : "No recorded review"}
                              </div>
                            </div>
                            {decisionBadge(approval?.decision)}
                          </div>
                          <div className="mt-3 flex flex-col gap-3 md:flex-row md:items-center">
                            <Input
                              value={notes[module] ?? ""}
                              onChange={(event) =>
                                setNotes((prev) => ({ ...prev, [module]: event.target.value }))
                              }
                              placeholder="Optional approval note"
                            />
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                onClick={() => handleDecision(module, "approved")}
                                disabled={approvalMutation.isPending}
                              >
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleDecision(module, "needs-review")}
                                disabled={approvalMutation.isPending}
                              >
                                Needs Review
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleDecision(module, "rejected")}
                                disabled={approvalMutation.isPending}
                              >
                                Reject
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Rune Adaptation Drafts</CardTitle>
          <p className="text-sm text-muted-foreground">
            Draft capability bindings generated from discovered components.
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.rune_adaptations.length === 0 ? (
            <p className="text-sm text-muted-foreground">No rune adaptations available.</p>
          ) : (
            data.rune_adaptations.map((adaptation) => (
              <div key={adaptation.module} className="rounded-lg border p-3">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <div className="font-medium">{adaptation.module}</div>
                    <div className="text-xs text-muted-foreground">
                      {adaptation.capability_id} · {adaptation.rune_id}
                    </div>
                  </div>
                  {adaptation.status === "registered" ? (
                    <Badge variant="secondary">Registered</Badge>
                  ) : (
                    <Badge variant="outline">Pending</Badge>
                  )}
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Manifested Components</CardTitle>
          <p className="text-sm text-muted-foreground">
            Current manifests with ownership, domain, and version metadata.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {(Object.keys(kindLabels) as ComponentKind[]).map((kind) => {
            const manifests = data.manifests[kind] ?? [];
            return (
              <div key={kind} className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">{kindLabels[kind]}</h3>
                  <Badge variant="outline">{manifests.length} manifests</Badge>
                </div>
                <div className="space-y-2">
                  {manifests.map((manifest) => (
                    <div key={manifest.owner_module} className="rounded-lg border p-3">
                      <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
                        <div>
                          <div className="font-medium">{manifest.owner_module}</div>
                          <div className="text-xs text-muted-foreground">
                            {manifest.domain} · v{manifest.version}
                          </div>
                        </div>
                        <div className="text-xs text-muted-foreground">{manifest.source_file}</div>
                      </div>
                      <div className="mt-2 text-sm text-muted-foreground">{manifest.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
