import { TrendingUp, Zap, Clock } from 'lucide-react';
import { DashboardStats } from '../components/dashboard/DashboardStats';
import { useBenchmark } from '../context/BenchmarkContext';
import { ResultsTable } from '../components/benchmark/ResultsTable';
import { QualityBarChart } from '../components/charts/QualityBarChart';
import { LatencyBarChart } from '../components/charts/LatencyBarChart';
import { getModelById } from '../data/models';

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'Just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

export function Dashboard() {
  const { runs, currentRun } = useBenchmark();
  const latestRun = currentRun ?? runs[0];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Stats */}
      <DashboardStats />

      {/* Latest Run & Charts */}
      {latestRun && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
          {/* Latest results table */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '1rem',
            }}>
              <TrendingUp size={16} color="var(--accent-primary)" />
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Latest Benchmark
              </span>
              <span className="badge badge-primary">
                {timeAgo(latestRun.timestamp)}
              </span>
            </div>
            <div style={{
              fontSize: '0.8125rem',
              color: 'var(--text-secondary)',
              marginBottom: '1rem',
              padding: '0.625rem 0.875rem',
              background: 'var(--bg-hover)',
              borderRadius: 'var(--radius-md)',
              borderLeft: '3px solid var(--accent-primary)',
              fontStyle: 'italic',
            }}>
              "{latestRun.prompt}"
            </div>
            <ResultsTable run={latestRun} />
          </div>

          {/* Charts row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
            <QualityBarChart run={latestRun} />
            <LatencyBarChart run={latestRun} />
          </div>
        </div>
      )}

      {/* Recent activity */}
      {runs.length > 1 && (
        <div className="card" style={{ padding: '1.25rem' }}>
          <h2 style={{
            fontSize: '0.9375rem',
            fontWeight: 600,
            margin: '0 0 0.875rem',
            color: 'var(--text-primary)',
          }}>
            Recent Activity
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {runs.slice(0, 5).map((run, i) => (
              <div
                key={run.id}
                className="animate-fade-in-up"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.875rem',
                  padding: '0.75rem 0.875rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-hover)',
                  animationDelay: `${i * 50}ms`,
                  opacity: 0,
                }}
              >
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(99,102,241,0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <Zap size={14} color="var(--accent-primary)" />
                </div>
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
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                    {run.results.map(r => getModelById(r.modelId)?.name ?? r.modelName).join(' • ')}
                  </div>
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  flexShrink: 0,
                }}>
                  <Clock size={11} />
                  {timeAgo(run.timestamp)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {runs.length === 0 && (
        <div className="card" style={{ padding: '3rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>🚀</div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 0.5rem' }}>
            Welcome to LLM Benchmark!
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9375rem', margin: 0 }}>
            Go to "Run Benchmark" to compare your first LLMs side by side.
          </p>
        </div>
      )}
    </div>
  );
}
