import { BarChart3, TrendingUp } from 'lucide-react';
import { useBenchmark } from '../context/BenchmarkContext';
import { QualityBarChart } from '../components/charts/QualityBarChart';
import { LatencyBarChart } from '../components/charts/LatencyBarChart';
import { TokenPieChart } from '../components/charts/TokenPieChart';
import { ChartsOverview } from '../components/charts/ChartsOverview';

export function Charts() {
  const { runs, currentRun } = useBenchmark();
  const displayRun = currentRun ?? runs[0];

  if (!displayRun) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon"><BarChart3 size={48} /></div>
        <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          No data to visualize yet
        </div>
        <div style={{ fontSize: '0.875rem', marginTop: '0.375rem' }}>
          Run a benchmark first to see analytics charts
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '1rem 1.25rem',
        borderRadius: 'var(--radius-lg)',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        boxShadow: 'var(--shadow-sm)',
      }}>
        <TrendingUp size={16} color="var(--accent-primary)" />
        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          Visualizing:
        </span>
        <span style={{
          fontSize: '0.8125rem',
          color: 'var(--text-secondary)',
          fontStyle: 'italic',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          "{displayRun.prompt}"
        </span>
        <span className="badge badge-primary" style={{ marginLeft: 'auto', flexShrink: 0 }}>
          {displayRun.results.length} models
        </span>
      </div>

      {/* Charts grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1rem' }}>
        <QualityBarChart run={displayRun} />
        <LatencyBarChart run={displayRun} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1rem' }}>
        <TokenPieChart run={displayRun} />
        <ChartsOverview run={displayRun} />
      </div>

      {/* All runs model performance summary */}
      {runs.length > 1 && (
        <div className="card" style={{ padding: '1.25rem' }}>
          <h2 style={{ fontSize: '0.9375rem', fontWeight: 700, margin: '0 0 0.5rem', color: 'var(--text-primary)' }}>
            All Benchmarks Overview
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: '0 0 1rem' }}>
            {runs.length} benchmark runs · Showing latest run above
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {runs.map((run) => (
              <div key={run.id} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.875rem',
                padding: '0.625rem 0.875rem',
                borderRadius: 'var(--radius-md)',
                background: run.id === displayRun.id ? 'rgba(99,102,241,0.06)' : 'var(--bg-hover)',
                border: run.id === displayRun.id ? '1px solid rgba(99,102,241,0.2)' : '1px solid transparent',
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: '0.8125rem',
                    fontWeight: 500,
                    color: 'var(--text-primary)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {run.prompt}
                  </div>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', flexShrink: 0 }}>
                  {run.results.length} models
                </div>
                {run.id === displayRun.id && (
                  <span className="badge badge-primary" style={{ fontSize: '0.7rem' }}>
                    Viewing
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
