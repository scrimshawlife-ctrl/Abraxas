import { MetricCard } from './components/MetricCard';
import { PhaseAlignmentTimeline } from './components/PhaseAlignmentTimeline';
import { MemeticWeatherMap } from './components/MemeticWeatherMap';
import { DomainCompressionDashboard } from './components/DomainCompressionDashboard';
import { ForecastAccuracyChart } from './components/ForecastAccuracyChart';
import { ResonanceNarrativeViewer } from './components/ResonanceNarrativeViewer';
import { RitualStatePanel } from './components/RitualStatePanel';
import { TimechainStatus } from './components/TimechainStatus';
import { Header } from './components/Header';
import { useMetricsSummary } from './hooks/useArtifacts';

export function App() {
  const { data: metrics } = useMetricsSummary();
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Overview Metrics */}
        <section aria-label="System Overview">
          <h2 className="text-2xl font-bold mb-4">System Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <MetricCard 
              title="Total Artifacts" 
              value={metrics?.total_artifacts || 0} 
              icon="📦" 
            />
            <MetricCard 
              title="Oracle Runs (24h)" 
              value={metrics?.oracle_runs_24h || 0} 
              icon="🔮" 
            />
            <MetricCard 
              title="Active Alignments" 
              value={metrics?.phase_alignments_active || 0} 
              icon="🔗" 
            />
            <MetricCard 
              title="Rituals (24h)" 
              value={metrics?.ritual_executions_24h || 0} 
              icon="⚡" 
            />
            <MetricCard 
              title="Timechain Blocks" 
              value={metrics?.timechain_blocks || 0} 
              icon="⛓️" 
            />
          </div>
        </section>

        {/* Phase Alignment Timeline */}
        <PhaseAlignmentTimeline />

        {/* Memetic Weather Map */}
        <MemeticWeatherMap />

        {/* Domain Compression Dashboard */}
        <DomainCompressionDashboard />

        {/* Forecast Accuracy */}
        <ForecastAccuracyChart />

        {/* Resonance Narratives */}
        <ResonanceNarrativeViewer />

        {/* Ritual State */}
        <RitualStatePanel />

        {/* Timechain Status */}
        <TimechainStatus />
      </main>
    </div>
  );
}