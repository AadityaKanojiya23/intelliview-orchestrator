import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import type { BenchmarkRun } from '../../types';
import { getModelById } from '../../data/models';

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; payload: { model: string } }>;
  label?: string;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
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
      <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
        {payload[0].value.toFixed(1)} / 10
      </div>
    </div>
  );
}

interface QualityBarChartProps {
  run: BenchmarkRun;
}

export function QualityBarChart({ run }: QualityBarChartProps) {
  const data = run.results.map((r) => {
    const model = getModelById(r.modelId);
    return {
      model: `${model?.logo ?? ''} ${r.modelName}`,
      quality: r.metrics.responseQuality,
      color: model?.color ?? '#6366f1',
    };
  });

  return (
    <div className="chart-container">
      <div className="chart-title">Response Quality Score</div>
      <div className="chart-subtitle">Out of 10.0 — higher is better</div>
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
            domain={[0, 10]}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={8} stroke="rgba(99,102,241,0.3)" strokeDasharray="4 4" />
          <Bar dataKey="quality" radius={[6, 6, 0, 0]} maxBarSize={60}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
