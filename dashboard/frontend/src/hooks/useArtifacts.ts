import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { MetricsSummary, PhaseAlignment, ResonanceNarrative, RitualState, SynchronicityMap } from '../types';

export function useMetricsSummary() {
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

  return { data, isLoading, error };
}

export function useRitualState() {
  const [data, setData] = useState<RitualState>({
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

  return { data, isLoading, error };
}