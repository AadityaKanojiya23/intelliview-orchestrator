import { CheckCircle, Sparkles } from 'lucide-react';
import { BenchmarkRunner } from '../components/benchmark/BenchmarkRunner';
import { ResultsTable } from '../components/benchmark/ResultsTable';
import { QualityBarChart } from '../components/charts/QualityBarChart';
import { LatencyBarChart } from '../components/charts/LatencyBarChart';
import { TokenPieChart } from '../components/charts/TokenPieChart';
import { ChartsOverview } from '../components/charts/ChartsOverview';
import { useBenchmark } from '../context/BenchmarkContext';

export function Benchmark() {
  const { currentRun, isRunning } = useBenchmark();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Configuration card */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '1.25rem' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'rgba(99,102,241,0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Sparkles size={16} color="var(--accent-primary)" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Benchmark Configuration
            </h2>
            <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Select models, enter a prompt, and run the simulation
            </p>
          </div>
        </div>
        <BenchmarkRunner />
      </div>

      {/* Results */}
      {currentRun && !isRunning && (
        <div
          className="animate-fade-in"
          style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}
        >
          {/* Success banner */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
            padding: '0.875rem 1.125rem',
            borderRadius: 'var(--radius-lg)',
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
          }}>
            <CheckCircle size={16} color="var(--accent-success)" />
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent-success)' }}>
              Benchmark complete!
            </span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              {currentRun.results.length} models compared in {currentRun.runDuration.toFixed(2)}s
            </span>
          </div>

          {/* Results table */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <ResultsTable run={currentRun} />
          </div>

          {/* Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
            <QualityBarChart run={currentRun} />
            <LatencyBarChart run={currentRun} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
            <TokenPieChart run={currentRun} />
            <ChartsOverview run={currentRun} />
          </div>
        </div>
      )}
    </div>
  );
}
