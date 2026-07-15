import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { BenchmarkRun } from '../../types';
import { getModelById } from '../../data/models';

interface LatencyTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; payload: { model: string } }>;
}

function LatencyTooltip({ active, payload }: LatencyTooltipProps) {
  if (!active || !payload?.length) return null;
  const val = payload[0].value;
  const color = val <= 2 ? 'var(--accent-success)' : val <= 3.5 ? 'var(--accent-warning)' : 'var(--accent-danger)';
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-md)',
      padding: '0.625rem 0.875rem',
      boxShadow: 'var(--shadow-lg)',
    }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
        {payload[0].payload.model}
      </div>
      <div style={{ fontSize: '1rem', fontWeight: 700, color }}>
        {val.toFixed(2)}s
      </div>
    </div>
  );
}

interface LatencyBarChartProps {
  run: BenchmarkRun;
}

export function LatencyBarChart({ run }: LatencyBarChartProps) {
  const data = run.results.map((r) => {
    const model = getModelById(r.modelId);
    const t = r.metrics.responseTime;
    const color = t <= 2 ? '#10b981' : t <= 3.5 ? '#f59e0b' : '#ef4444';
    return {
      model: `${model?.logo ?? ''} ${r.modelName}`,
      latency: t,
      color,
    };
  });

  return (
    <div className="chart-container">
      <div className="chart-title">Response Latency</div>
      <div className="chart-subtitle">In seconds — lower is better</div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
          <XAxis
            dataKey="model"
            tick={{ fontSize: 11, fill: 'var(--text-secondary)' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={false}
            tickLine={false}
            unit="s"
          />
          <Tooltip content={<LatencyTooltip />} />
          <Bar dataKey="latency" radius={[6, 6, 0, 0]} maxBarSize={60}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
