import { useResonanceNarratives } from '../hooks/useArtifacts';

export function ResonanceNarrativeViewer() {
  const { data: narratives, isLoading, error } = useResonanceNarratives(10);
  
  if (isLoading) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">Loading narratives...</div>;
  if (error) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-red-500">Error: {error}</div>;
  
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" aria-label="Resonance Narratives">
      <h2 className="text-xl font-bold mb-4">Resonance Narratives</h2>
      {narratives.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No narratives generated</p>
      ) : (
        <div className="space-y-4">
          {narratives.map((narrative, i) => (
            <div key={narrative.artifact_id || i} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <h3 className="font-medium text-gray-900 mb-2">{narrative.headline}</h3>
              <div className="flex flex-wrap gap-2 mb-3">
                {narrative.motifs?.slice(0, 3).map((m: any, j: number) => (
                  <span key={j} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                    {m.motif} ({(m.strength * 100).toFixed(0)}%)
                  </span>
                ))}
              </div>
              <p className="text-xs text-gray-500">
                ID: {narrative.artifact_id} • Missing: {narrative.constraints_report?.missing_inputs?.length || 0} • Not computable: {narrative.constraints_report?.not_computable?.length || 0}
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}