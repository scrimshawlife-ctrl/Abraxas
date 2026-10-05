import { usePhaseAlignments } from '../hooks/useArtifacts';
import type { PhaseAlignment } from '../types';

export function PhaseAlignmentTimeline() {
  const { data: alignments, isLoading, error } = usePhaseAlignments(10);
  
  if (isLoading) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">Loading alignments...</div>;
  if (error) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-red-500">Error: {error}</div>;
  
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" aria-label="Phase Alignments">
      <h2 className="text-xl font-bold mb-4">Phase Alignment Timeline</h2>
      {alignments.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No alignments detected</p>
      ) : (
        <div className="space-y-4">
          {alignments.map((alignment: PhaseAlignment) => (
            <div key={alignment.alignment_id} className="border-l-4 border-blue-500 pl-4 py-2 bg-gray-50 rounded-r-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{alignment.aligned_phase}</p>
                  <p className="text-sm text-gray-500">
                    Domains: {alignment.domains.join(', ')} • Strength: {(alignment.alignment_strength * 100).toFixed(0)}%
                  </p>
                </div>
                <span className="text-sm text-gray-400">
                  {new Date(alignment.timestamp_utc).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}