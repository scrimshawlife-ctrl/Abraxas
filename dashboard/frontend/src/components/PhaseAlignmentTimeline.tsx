import { usePhaseAlignments } from '../hooks/useArtifacts';
import type { PhaseAlignment } from '../types';
import { TableSkeleton } from './LoadingSkeletons';

export function PhaseAlignmentTimeline() {
  const { data: alignments, isLoading, error } = usePhaseAlignments(10);
  
  if (isLoading) return <TableSkeleton rows={5} />;
  if (error) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-red-500">Error: {error}</div>;
  
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" aria-label="Phase Alignments">
      <h2 className="text-xl font-bold mb-4">Phase Alignment Timeline</h2>
      {alignments.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No alignments detected</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="pb-2 font-medium text-gray-500">Aligned Phase</th>
                <th className="pb-2 font-medium text-gray-500">Domains</th>
                <th className="pb-2 font-medium text-gray-500">Strength</th>
                <th className="pb-2 font-medium text-gray-500">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {alignments.map((alignment: PhaseAlignment) => (
                <tr key={alignment.alignment_id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 font-medium text-gray-900">{alignment.aligned_phase}</td>
                  <td className="py-2 text-gray-600">{alignment.domains.join(', ')}</td>
                  <td className="py-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(alignment.alignment_strength * 100).toFixed(0)}%` }}></div>
                    </div>
                    <span className="text-xs text-gray-500 ml-2">{(alignment.alignment_strength * 100).toFixed(0)}%</span>
                  </td>
                  <td className="py-2 text-gray-400 whitespace-nowrap">{new Date(alignment.timestamp_utc).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}