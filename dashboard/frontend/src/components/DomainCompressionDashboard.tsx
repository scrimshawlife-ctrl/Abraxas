import { useArtifacts } from '../hooks/useArtifacts';
import { CardSkeleton } from './LoadingSkeletons';

export function DomainCompressionDashboard() {
  const { data: artifacts, isLoading, error } = useArtifacts('domain_compression', 20);
  
  if (isLoading) return <CardSkeleton />;
  if (error) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-red-500">Error: {error}</div>;
  
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" aria-label="Domain Compression">
      <h2 className="text-xl font-bold mb-4">Domain Compression Dashboard</h2>
      {artifacts.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No compression artifacts</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {artifacts.slice(0, 6).map((artifact) => (
            <div key={artifact.artifact_id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <p className="font-medium text-gray-900 truncate">{artifact.artifact_id}</p>
              <p className="text-sm text-gray-500 mt-1">{new Date(artifact.timestamp).toLocaleString()}</p>
              <p className="text-xs text-gray-400 mt-1">{(artifact.size_bytes / 1024).toFixed(1)} KB</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}