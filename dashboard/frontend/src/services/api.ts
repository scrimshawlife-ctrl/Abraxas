const API_BASE = '/api';

async function fetchJson<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  health: () => fetchJson<{ status: string; service: string; version: string }>('/health'),
  
  artifacts: {
    list: (params?: { type?: string; limit?: number; offset?: number }) => {
      const search = new URLSearchParams();
      if (params?.type) search.set('type', params.type);
      if (params?.limit) search.set('limit', String(params.limit));
      if (params?.offset) search.set('offset', String(params.offset));
      return fetchJson<{ artifact_id: string; type: string; timestamp: string; size_bytes: number; path: string }[]>(`/artifacts?${search}`);
    },
    get: (artifactId: string) => fetchJson<{ manifest: any; files: Record<string, any> }>(`/artifacts/${artifactId}`),
  },
  
  phase: {
    alignments: (limit = 20) => fetchJson<{ alignments: any[] }>(`/phase/alignments?limit=${limit}`),
    synchronicity: () => fetchJson<{ map: any }>('/phase/synchronicity'),
  },
  
  oracle: {
    bundles: (limit = 20) => fetchJson<{ bundles: any[] }>(`/oracle/bundles?limit=${limit}`),
  },
  
  resonance: {
    narratives: (limit = 20) => fetchJson<{ narratives: any[] }>(`/resonance/narratives?limit=${limit}`),
  },
  
  ritual: {
    state: () => fetchJson<{ active_modulations: Record<string, Record<string, number>>; recent_executions: any[] }>('/ritual/state'),
  },
  
  timechain: {
    status: () => fetchJson<{ blocks: number; integrity: string; genesis: string; latest_block_hash: string }>('/timechain/status'),
  },
  
  metrics: {
    summary: () => fetchJson<{
      total_artifacts: number;
      oracle_runs_24h: number;
      phase_alignments_active: number;
      ritual_executions_24h: number;
      timechain_blocks: number;
    }>('/metrics/summary'),
  },
};