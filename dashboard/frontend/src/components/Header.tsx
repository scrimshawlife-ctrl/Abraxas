import { useMetricsSummary } from '../hooks/useArtifacts';
import { useTheme } from '../hooks/useTheme';

export function Header() {
  const { data: metrics } = useMetricsSummary();
  const { theme, setTheme } = useTheme();
  
  return (
    <header className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🏛️</span>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Abraxas Dashboard</h1>
            <span className="px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full">
              PRODUCTION CANON v2.0.0
            </span>
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
            <span>Artifacts: {metrics?.total_artifacts || 0}</span>
            <span>Oracle: {metrics?.oracle_runs_24h || 0}/24h</span>
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span>LIVE</span>
            </span>
            <div className="flex items-center space-x-2 ml-4">
              <span className="text-xs text-gray-500 dark:text-gray-400">Theme:</span>
              <select 
                value={theme} 
                onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
                className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Theme selection"
              >
                <option value="light">☀️ Light</option>
                <option value="dark">🌙 Dark</option>
                <option value="system">💻 System</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}