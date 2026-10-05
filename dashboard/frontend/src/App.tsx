import { MetricCard } from './components/MetricCard';
import { PhaseAlignmentTimeline } from './components/PhaseAlignmentTimeline';
import { MemeticWeatherMap } from './components/MemeticWeatherMap';
import { DomainCompressionDashboard } from './components/DomainCompressionDashboard';
import { ForecastAccuracyChart } from './components/ForecastAccuracyChart';
import { ResonanceNarrativeViewer } from './components/ResonanceNarrativeViewer';
import { RitualStatePanel } from './components/RitualStatePanel';
import { TimechainStatus } from './components/TimechainStatus';
import { Header } from './components/Header';
import { OnboardingFlow } from './components/OnboardingFlow';
import { useMetricsSummary } from './hooks/useArtifacts';
import { useState, useEffect } from 'react';

export function App() {
  const { data: metrics } = useMetricsSummary();
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    const hasSeenOnboarding = localStorage.getItem('abraxas-onboarding-complete');
    if (!hasSeenOnboarding) {
      setShowOnboarding(true);
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      <main className="container mx-auto px-4 py-8 space-y-8" id="main-content" role="main">
        {/* Skip link for keyboard users */}
        <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 px-4 py-2 bg-blue-600 text-white rounded">
          Skip to main content
        </a>
        {/* Overview Metrics */}
        <section aria-label="System Overview" aria-live="polite" aria-atomic="true">
          <h2 className="text-2xl font-bold mb-4">System Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4" role="list" aria-label="System metrics">
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
        <section aria-label="Phase Alignments" aria-live="polite">
          <PhaseAlignmentTimeline />
        </section>

        {/* Memetic Weather Map */}
        <section aria-label="Memetic Weather (Synchronicity Map)" aria-live="polite">
          <MemeticWeatherMap />
        </section>

        {/* Domain Compression Dashboard */}
        <section aria-label="Domain Compression">
          <DomainCompressionDashboard />
        </section>

        {/* Forecast Accuracy */}
        <section aria-label="Forecast Accuracy">
          <ForecastAccuracyChart />
        </section>

        {/* Resonance Narratives */}
        <section aria-label="Resonance Narratives" aria-live="polite">
          <ResonanceNarrativeViewer />
        </section>

        {/* Ritual State */}
        <section aria-label="Ritual State" aria-live="polite">
          <RitualStatePanel />
        </section>

        {/* Timechain Status */}
        <section aria-label="Timechain Status">
          <TimechainStatus />
        </section>
      </main>
      <OnboardingFlow 
        isOpen={showOnboarding} 
        onClose={() => { localStorage.setItem('abraxas-onboarding-complete', 'true'); setShowOnboarding(false); }}
        onComplete={() => { localStorage.setItem('abraxas-onboarding-complete', 'true'); setShowOnboarding(false); }}
      />
    </div>
  );
}