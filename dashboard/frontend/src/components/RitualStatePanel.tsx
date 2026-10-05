import { useRitualState } from '../hooks/useArtifacts';
import { CardSkeleton } from './LoadingSkeletons';

export function RitualStatePanel() {
  const { data: ritualState, isLoading, error } = useRitualState();
  
  if (isLoading) return <CardSkeleton />;
  if (error) return <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-red-500">Error: {error}</div>;
  
  const activeModulations = ritualState?.active_modulations || {};
  const recentExecutions = ritualState?.recent_executions || [];
  
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" aria-label="Ritual State">
      <h2 className="text-xl font-bold mb-4">Ritual State</h2>
      
      <div className="mb-6">
        <h3 className="font-medium text-gray-900 mb-3">Active Modulations</h3>
        {Object.keys(activeModulations).length === 0 ? (
          <p className="text-gray-500 text-center py-4">No active modulations</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(activeModulations).map(([target, params]) => (
              <div key={target} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <p className="font-mono text-sm text-gray-700 mb-1 truncate">{target}</p>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(params).map(([param, value]) => (
                    <span key={param} className="px-2 py-0.5 text-xs bg-gray-200 text-gray-700 rounded">
                      {param}: {typeof value === 'number' ? value.toFixed(2) : value}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div>
        <h3 className="font-medium text-gray-900 mb-3">Recent Executions</h3>
        {recentExecutions.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No recent executions</p>
        ) : (
          <div className="space-y-2">
            {recentExecutions.slice(0, 5).map((exec: any, i: number) => (
              <div key={i} className="bg-gray-50 rounded-lg p-3 border border-gray-200 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{exec.protocol_id}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(exec.timestamp_utc).toLocaleString()} • Effect: {(exec.effect_magnitude * 100).toFixed(0)}%
                  </p>
                </div>
                <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                  SUCCESS
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}