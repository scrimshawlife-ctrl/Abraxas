import { useSynchronicity } from '../hooks/useArtifacts';
import { TableSkeleton } from './LoadingSkeletons';

export function MemeticWeatherMap() {
  const { data: syncMap, isLoading, error } = useSynchronicity();
  
  if (isLoading) return <TableSkeleton rows={5} />;
  if (error) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-red-500">Error: {error}</div>;
  
  const patterns = syncMap?.patterns || [];
  
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" aria-label="Memetic Weather">
      <h2 className="text-xl font-bold mb-4">Memetic Weather (Synchronicity Map)</h2>
      {patterns.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No synchronicity patterns detected</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm min-w-[600px]">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="pb-2 font-medium text-gray-500 whitespace-nowrap">Source → Target</th>
                      <th className="pb-2 font-medium text-gray-500 whitespace-nowrap">Phase</th>
                      <th className="pb-2 font-medium text-gray-500 whitespace-nowrap">Lag (hrs)</th>
                      <th className="pb-2 font-medium text-gray-500 whitespace-nowrap">Confidence</th>
                      <th className="pb-2 font-medium text-gray-500 whitespace-nowrap">Observations</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patterns.slice(0, 10).map((pattern, i) => (
                      <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-2 font-mono whitespace-nowrap">{pattern.source_domain} → {pattern.target_domain}</td>
                        <td className="py-2 whitespace-nowrap">{pattern.phase}</td>
                        <td className="py-2 whitespace-nowrap">{pattern.lag_hours.toFixed(1)}</td>
                        <td className="py-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${pattern.confidence * 100}%` }}></div>
                          </div>
                          <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">{(pattern.confidence * 100).toFixed(0)}%</span>
                        </td>
                        <td className="py-2 whitespace-nowrap">{pattern.observation_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
      <p className="text-xs text-gray-400 mt-2">
        Generated: {syncMap ? new Date(syncMap.generated_utc).toLocaleString() : '—'}
      </p>
    </section>
  );
}