import { Zap, Trophy, DollarSign, Activity, BarChart2, Hash } from 'lucide-react';
import { StatCard } from './StatCard';
import { useBenchmark } from '../../context/BenchmarkContext';
import { getDashboardStats } from '../../utils/csvExport';

export function DashboardStats() {
  const { runs } = useBenchmark();
  const stats = getDashboardStats(runs);

  const cards = [
    {
      label: 'Total Benchmarks Run',
      value: stats.totalBenchmarks,
      icon: <Activity size={20} color="#6366f1" />,
      iconBg: 'rgba(99, 102, 241, 0.12)',
      gradientStart: '#6366f1',
      gradientEnd: '#7c3aed',
      subtext: stats.totalBenchmarks === 0 ? 'Run your first benchmark!' : undefined,
    },
    {
      label: 'Fastest Model',
      value: stats.fastestModel,
      icon: <Zap size={20} color="#f59e0b" />,
      iconBg: 'rgba(245, 158, 11, 0.12)',
      gradientStart: '#f59e0b',
      gradientEnd: '#d97706',
      subtext: stats.averageLatency > 0 ? `Avg latency: ${stats.averageLatency}s` : undefined,
    },
    {
      label: 'Highest Quality',
      value: stats.highestQualityModel,
      icon: <Trophy size={20} color="#10b981" />,
      iconBg: 'rgba(16, 185, 129, 0.12)',
      gradientStart: '#10b981',
      gradientEnd: '#059669',
      subtext: 'Best response quality score',
    },
    {
      label: 'Lowest Cost',
      value: stats.lowestCostModel,
      icon: <DollarSign size={20} color="#3b82f6" />,
      iconBg: 'rgba(59, 130, 246, 0.12)',
      gradientStart: '#3b82f6',
      gradientEnd: '#2563eb',
      subtext: 'Most cost-efficient model',
    },
    {
      label: 'Total Tokens Used',
      value: stats.totalTokensUsed.toLocaleString(),
      icon: <Hash size={20} color="#ec4899" />,
      iconBg: 'rgba(236, 72, 153, 0.12)',
      gradientStart: '#ec4899',
      gradientEnd: '#db2777',
      subtext: 'Across all benchmark runs',
    },
    {
      label: 'Avg Response Time',
      value: stats.averageLatency > 0 ? `${stats.averageLatency}s` : 'N/A',
      icon: <BarChart2 size={20} color="#8b5cf6" />,
      iconBg: 'rgba(139, 92, 246, 0.12)',
      gradientStart: '#8b5cf6',
      gradientEnd: '#7c3aed',
      subtext: 'Average latency per model',
    },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1rem',
      marginBottom: '1.5rem',
    }}>
      {cards.map((card, i) => (
        <StatCard key={card.label} {...card} delay={i * 60} />
      ))}
    </div>
  );
}
