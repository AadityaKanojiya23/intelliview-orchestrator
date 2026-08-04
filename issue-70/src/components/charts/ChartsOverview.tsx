import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import type { BenchmarkRun } from '../../types';
import { getModelById } from '../../data/models';

interface ChartsOverviewProps {
  run: BenchmarkRun;
}

export function ChartsOverview({ run }: ChartsOverviewProps) {
  // Radar chart data
  const radarData = [
    { metric: 'Quality', ...Object.fromEntries(run.results.map(r => [r.modelId, r.metrics.responseQuality * 10])) },
    { metric: 'Speed',   ...Object.fromEntries(run.results.map(r => [r.modelId, Math.max(0, 100 - r.metrics.responseTime * 20)])) },
    { metric: 'Cost',    ...Object.fromEntries(run.results.map(r => [r.modelId, Math.max(0, 100 - r.metrics.estimatedCost * 60)])) },
    { metric: 'Complete',...Object.fromEntries(run.results.map(r => [r.modelId, r.metrics.completeness])) },
    { metric: 'Coherence',...Object.fromEntries(run.results.map(r => [r.modelId, r.metrics.coherence])) },
    { metric: 'Accuracy',...Object.fromEntries(run.results.map(r => [r.modelId, r.metrics.accuracy])) },
  ];

  return (
    <div className="chart-container">
      <div className="chart-title">Multi-Metric Radar Comparison</div>
      <div className="chart-subtitle">Normalized 0–100 across all dimensions</div>
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="var(--border-color)" />
          <PolarAngleAxis
            dataKey="metric"
            tick={{ fontSize: 11, fill: 'var(--text-secondary)' }}
          />
          {run.results.map((result) => {
            const model = getModelById(result.modelId);
            return (
              <Radar
                key={result.modelId}
                name={result.modelName}
                dataKey={result.modelId}
                stroke={model?.color ?? '#6366f1'}
                fill={model?.color ?? '#6366f1'}
                fillOpacity={0.12}
                strokeWidth={2}
              />
            );
          })}
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.8125rem',
              color: 'var(--text-primary)',
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
