import { existsSync } from "fs";
import { mkdir, readFile, readdir, writeFile } from "fs/promises";
import path from "path";
import { parse } from "yaml";

type ComponentKind = "metrics" | "operators" | "artifacts";

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

interface ApprovalRecord {
  decision: "approved" | "needs-review" | "rejected";
  reviewer: string;
  reason: string;
  recorded_at: string;
}

interface ApprovalState {
  approvals: Record<string, ApprovalRecord>;
  history: Array<ApprovalRecord & { module: string }>;
  updated_at: string;
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

const registryRoots: Record<ComponentKind, { prefix: string; dir: string }> = {
  metrics: { prefix: "abraxas.metrics", dir: path.join("abraxas", "metrics") },
  operators: { prefix: "abraxas.operators", dir: path.join("abraxas", "operators") },
  artifacts: { prefix: "abraxas.artifacts", dir: path.join("abraxas", "artifacts") },
};

const approvalsPath = path.resolve(
  process.cwd(),
  "out",
  "governance",
  "component_registry_approvals.json",
);
const runesRegistryPath = path.resolve(
  process.cwd(),
  "abraxas",
  "runes",
  "registry.json",
);

async function walkPythonModules(
  repoRoot: string,
  directory: string,
  modulePrefix: string,
): Promise<string[]> {
  const targetDir = path.resolve(repoRoot, directory);
  if (!existsSync(targetDir)) {
    return [];
  }

  const modules = new Set<string>();
  const stack = [targetDir];

  while (stack.length > 0) {
    const current = stack.pop();
    if (!current) {
      continue;
    }
    const entries = await readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.name === "__pycache__") {
        continue;
      }
      const entryPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(entryPath);
        continue;
      }
      if (!entry.isFile() || !entry.name.endsWith(".py") || entry.name === "__init__.py") {
        continue;
      }
      const relativePath = path.relative(repoRoot, entryPath).replace(/\.py$/, "");
      const modulePath = relativePath.split(path.sep).join(".");
      if (modulePath.startsWith(modulePrefix)) {
        modules.add(modulePath);
      }
    }
  }

  return Array.from(modules).sort();
}

async function loadManifestSummaries(repoRoot: string): Promise<Record<ComponentKind, ManifestSummary[]>> {
  const manifestRoot = path.resolve(repoRoot, "data", "rent_manifests");
  const manifests: Record<ComponentKind, ManifestSummary[]> = {
    metrics: [],
    operators: [],
    artifacts: [],
  };

  const kinds: ComponentKind[] = ["metrics", "operators", "artifacts"];
  for (const kind of kinds) {
    const dir = path.join(manifestRoot, kind);
    if (!existsSync(dir)) {
      continue;
    }
    const entries = await readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isFile() || !entry.name.endsWith(".yaml")) {
        continue;
      }
      const filePath = path.join(dir, entry.name);
      const raw = await readFile(filePath, "utf-8");
      const manifest = parse(raw) as ManifestSummary;
      if (!manifest || !manifest.owner_module) {
        continue;
      }
      manifests[kind].push({
        id: manifest.id,
        kind: manifest.kind,
        domain: manifest.domain,
        description: manifest.description,
        owner_module: manifest.owner_module,
        version: manifest.version,
        created_at: manifest.created_at,
        source_file: path.relative(repoRoot, filePath),
      });
    }
    manifests[kind].sort((a, b) => a.owner_module.localeCompare(b.owner_module));
  }

  return manifests;
}

async function loadApprovalState(): Promise<ApprovalState> {
  if (!existsSync(approvalsPath)) {
    return { approvals: {}, history: [], updated_at: new Date().toISOString() };
  }
  const raw = await readFile(approvalsPath, "utf-8");
  const parsed = JSON.parse(raw) as ApprovalState;
  return {
    approvals: parsed.approvals ?? {},
    history: parsed.history ?? [],
    updated_at: parsed.updated_at ?? new Date().toISOString(),
  };
}

async function loadRuneCapabilities(): Promise<Set<string>> {
  if (!existsSync(runesRegistryPath)) {
    return new Set();
  }
  const raw = await readFile(runesRegistryPath, "utf-8");
  const parsed = JSON.parse(raw) as { capabilities?: Array<{ capability_id: string }> };
  return new Set((parsed.capabilities ?? []).map((cap) => cap.capability_id));
}

function runeDraftForModule(moduleName: string): RuneAdaptation {
  const slug = moduleName.replace(/[^a-zA-Z0-9]+/g, "_").toUpperCase();
  return {
    module: moduleName,
    capability_id: `component.${moduleName}`,
    rune_id: `ϟ_COMPONENT_${slug}`,
    status: "pending",
    draft: true,
  };
}

async function saveApprovalState(state: ApprovalState): Promise<void> {
  const dir = path.dirname(approvalsPath);
  await mkdir(dir, { recursive: true });
  await writeFile(
    approvalsPath,
    JSON.stringify(
      {
        approvals: state.approvals,
        history: state.history,
        updated_at: state.updated_at,
      },
      null,
      2,
    ),
    "utf-8",
  );
}

export async function getComponentRegistry(): Promise<ComponentRegistryResponse> {
  const repoRoot = process.cwd();
  const registry: Record<ComponentKind, string[]> = {
    metrics: [],
    operators: [],
    artifacts: [],
  };

  for (const kind of Object.keys(registryRoots) as ComponentKind[]) {
    const { prefix, dir } = registryRoots[kind];
    registry[kind] = await walkPythonModules(repoRoot, dir, prefix);
  }

  const manifests = await loadManifestSummaries(repoRoot);
  const approvals = await loadApprovalState();
  const runeCapabilities = await loadRuneCapabilities();

  const unmanifested: Record<ComponentKind, string[]> = {
    metrics: [],
    operators: [],
    artifacts: [],
  };

  let registryCount = 0;
  let manifestedCount = 0;

  for (const kind of Object.keys(registry) as ComponentKind[]) {
    const manifestModules = new Set(manifests[kind].map((manifest) => manifest.owner_module));
    unmanifested[kind] = registry[kind].filter((module) => !manifestModules.has(module));
    registryCount += registry[kind].length;
    manifestedCount += manifestModules.size;
  }

  const rune_adaptations = Object.values(registry)
    .flat()
    .map((moduleName) => {
      const draft = runeDraftForModule(moduleName);
      if (runeCapabilities.has(draft.capability_id)) {
        return { ...draft, status: "registered", draft: false };
      }
      return draft;
    })
    .sort((a, b) => a.module.localeCompare(b.module));

  return {
    generated_at: new Date().toISOString(),
    registry,
    manifests,
    unmanifested,
    approvals: approvals.approvals,
    rune_adaptations,
    totals: {
      registry_count: registryCount,
      manifested_count: manifestedCount,
      unmanifested_count: registryCount - manifestedCount,
    },
  };
}

export async function recordComponentApproval(input: {
  module: string;
  decision: ApprovalRecord["decision"];
  reviewer: string;
  reason: string;
}): Promise<ApprovalState> {
  const approvals = await loadApprovalState();
  const record: ApprovalRecord = {
    decision: input.decision,
    reviewer: input.reviewer,
    reason: input.reason,
    recorded_at: new Date().toISOString(),
  };
  approvals.approvals[input.module] = record;
  approvals.history.push({ ...record, module: input.module });
  approvals.updated_at = new Date().toISOString();
  await saveApprovalState(approvals);
  return approvals;
}
