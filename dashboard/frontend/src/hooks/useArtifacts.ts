import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useWebSocket } from './useWebSocket';
import type { MetricsSummary, PhaseAlignment, ResonanceNarrative, SynchronicityMap } from '../types';

// WebSocket URL - defaults to same origin with /ws path
const WS_URL = typeof window !== 'undefined' 
  ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
  : 'ws://localhost:8082/ws';

export function useMetricsSummary() {
  const [data, setData] = useState<MetricsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initial fetch
  useEffect(() => {
    let mounted = true;
    api.metrics.summary()
      .then(d => { if (mounted) setData(d); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, []);

  // WebSocket updates
  useWebSocket({
    url: WS_URL,
    onMessage: (msg) => {
      if (msg.type === 'metrics_summary') {
        setData(msg.data);
      }
    },
    reconnect: true,
  });

  return { data, isLoading, error };
}

export function usePhaseAlignments(limit = 20) {
  const [data, setData] = useState<PhaseAlignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.phase.alignments(limit)
      .then(d => { if (mounted) setData(d.alignments); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, [limit]);

  // WebSocket updates
  useWebSocket({
    url: WS_URL,
    onMessage: (msg) => {
      if (msg.type === 'phase_alignments') {
        setData(msg.data);
      }
    },
    reconnect: true,
  });

  return { data, isLoading, error };
}

export function useSynchronicity() {
  const [data, setData] = useState<SynchronicityMap | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.phase.synchronicity()
      .then(d => { if (mounted) setData(d.map); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, []);

  useWebSocket({
    url: WS_URL,
    onMessage: (msg) => {
      if (msg.type === 'synchronicity') {
        setData(msg.data);
      }
    },
    reconnect: true,
  });

  return { data, isLoading, error };
}

export function useResonanceNarratives(limit = 20) {
  const [data, setData] = useState<ResonanceNarrative[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.resonance.narratives(limit)
      .then(d => { if (mounted) setData(d.narratives); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, [limit]);

  useWebSocket({
    url: WS_URL,
    onMessage: (msg) => {
      if (msg.type === 'resonance_narratives') {
        setData(msg.data);
      }
    },
    reconnect: true,
  });

  return { data, isLoading, error };
}

export function useRitualState() {
  const [data, setData] = useState<{ active_modulations: Record<string, Record<string, number>>; recent_executions: any[] }>({
    active_modulations: {},
    recent_executions: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.ritual.state()
      .then(d => { if (mounted) setData(d); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, []);

  useWebSocket({
    url: WS_URL,
    onMessage: (msg) => {
      if (msg.type === 'ritual_state') {
        setData(msg.data);
      }
    },
    reconnect: true,
  });

  return { data, isLoading, error };
}

export function useArtifacts(type?: string, limit = 50) {
  const [data, setData] = useState<Array<{ artifact_id: string; type: string; timestamp: string; size_bytes: number; path: string }>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.artifacts.list({ type, limit })
      .then(d => { if (mounted) setData(d); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, [type, limit]);

  useWebSocket({
    url: WS_URL,
    onMessage: (msg) => {
      if (msg.type === 'artifacts') {
        setData(msg.data);
      }
    },
    reconnect: true,
  });

  return { data, isLoading, error };
}

// Keep original non-WS versions for backward compatibility
export function useMetricsSummaryPolling() {
  const [data, setData] = useState<MetricsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.metrics.summary()
      .then(d => { if (mounted) setData(d); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, []);

  return { data, isLoading, error };
}

export function usePhaseAlignmentsPolling(limit = 20) {
  const [data, setData] = useState<PhaseAlignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.phase.alignments(limit)
      .then(d => { if (mounted) setData(d.alignments); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, [limit]);

  return { data, isLoading, error };
}

export function useSynchronicityPolling() {
  const [data, setData] = useState<SynchronicityMap | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.phase.synchronicity()
      .then(d => { if (mounted) setData(d.map); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, []);

  return { data, isLoading, error };
}

export function useResonanceNarrativesPolling(limit = 20) {
  const [data, setData] = useState<ResonanceNarrative[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.resonance.narratives(limit)
      .then(d => { if (mounted) setData(d.narratives); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, [limit]);

  return { data, isLoading, error };
}

export function useRitualStatePolling() {
  const [data, setData] = useState<{ active_modulations: Record<string, Record<string, number>>; recent_executions: any[] }>({
    active_modulations: {},
    recent_executions: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.ritual.state()
      .then(d => { if (mounted) setData(d); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, []);

  return { data, isLoading, error };
}

export function useArtifactsPolling(type?: string, limit = 50) {
  const [data, setData] = useState<Array<{ artifact_id: string; type: string; timestamp: string; size_bytes: number; path: string }>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.artifacts.list({ type, limit })
      .then(d => { if (mounted) setData(d); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setIsLoading(false); });
    return () => { mounted = false; };
  }, [type, limit]);

  return { data, isLoading, error };
}