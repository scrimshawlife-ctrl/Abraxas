import { useMetricsSummary } from '../hooks/useArtifacts';

export function Header() {
  const { data: metrics, isLoading } = useMetricsSummary();
  
  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🏛️</span>
            <h1 className="text-2xl font-bold text-gray-900">Abraxas Dashboard</h1>
            <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
              PRODUCTION CANON v2.0.0
            </span>
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>Artifacts: {isLoading ? '—' : metrics?.total_artifacts || 0}</span>
            <span>Oracle: {isLoading ? '—' : metrics?.oracle_runs_24h || 0}/24h</span>
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span>LIVE</span>
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}