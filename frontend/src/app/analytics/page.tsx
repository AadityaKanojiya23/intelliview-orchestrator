"use client";
import { useMemo } from "react";
import useSWR from "swr";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, PieChart, Pie, Cell, Legend } from "recharts";
import { Card } from "@/components/Card";
import { Stat } from "@/components/Stat";
import { Skeleton, ErrorState } from "@/components/States";
import { endpoints } from "@/lib/api";

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16"];

export default function AnalyticsPage() {
  const stats = useSWR("/session-statistics", { refreshInterval: 10000 });
  const faults = useSWR("/fault-statistics", { refreshInterval: 10000 });
  const dlq = useSWR("/dead-letter-queue?limit=50", { refreshInterval: 10000 });

  const breakdown = stats.data ? Object.entries(stats.data.status_breakdown).map(([status, count]) => ({ status, count: count as number })) : [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-50">Analytics</h1>
        <p className="text-sm text-muted">Risk distribution, failure modes, and retry behavior.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Total sessions" value={stats.data?.total_sessions ?? <Skeleton className="h-7 w-12" />} />
        <Stat label="Avg risk" value={stats.data ? stats.data.risk_score_stats.average_risk_score.toFixed(3) : <Skeleton className="h-7 w-16" />} />
        <Stat label="High risk" value={stats.data?.risk_score_stats.high_risk_sessions ?? <Skeleton className="h-7 w-12" />} />
        <Stat label="DLQ size" value={dlq.data?.count ?? <Skeleton className="h-7 w-12" />} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Sessions by status" description="Distribution across the lifecycle states.">
          {stats.error ? (
            <ErrorState error={stats.error} onRetry={() => stats.mutate()} />
          ) : !stats.data ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={breakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="status" stroke="#71717a" fontSize={11} />
                <YAxis stroke="#71717a" fontSize={11} />
                <Tooltip contentStyle={{ background: "#12121a", border: "1px solid #27272a", borderRadius: 8 }} />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card title="Failure breakdown" description="Counts grouped by failure type.">
          {faults.error ? (
            <ErrorState error={faults.error} onRetry={() => faults.mutate()} />
          ) : !faults.data ? (
            <Skeleton className="h-64 w-full" />
          ) : Object.keys(faults.data.fault_statistics.failures_by_type).length === 0 ? (
            <div className="py-8 text-center text-sm text-muted">No failures recorded.</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={Object.entries(faults.data.fault_statistics.failures_by_type).map(([type, count]) => ({ type, count: count as number }))}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="type" stroke="#71717a" fontSize={11} />
                <YAxis stroke="#71717a" fontSize={11} />
                <Tooltip contentStyle={{ background: "#12121a", border: "1px solid #27272a", borderRadius: 8 }} />
                <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <RiskDistribution stats={stats.data} error={stats.error} onRetry={() => stats.mutate()} loading={!stats.data && !stats.error} />
    </div>
  );
}

interface RiskDistributionProps {
  stats:
    | {
        total_sessions: number;
        risk_score_stats: {
          average_risk_score: number;
          high_risk_sessions: number;
        };
      }
    | undefined;
  error: Error | undefined;
  onRetry: () => void;
  loading: boolean;
}

function RiskDistribution({ stats, error, onRetry, loading }: RiskDistributionProps) {
  const completed = useSWR("/completed-sessions?limit=100", { refreshInterval: 10000 });
  const buckets = useMemo(() => {
    const seed = [
      { name: "Low (<0.3)", color: "#10b981", value: 0 },
      { name: "Medium (0.3-0.6)", color: "#f59e0b", value: 0 },
      { name: "High (0.6-0.8)", color: "#f97316", value: 0 },
      { name: "Critical (≥0.8)", color: "#ef4444", value: 0 },
    ];
    for (const s of completed.data?.sessions ?? []) {
      const r = (s as { risk_score?: number | null }).risk_score;
      if (typeof r !== "number") continue;
      if (r < 0.3) seed[0].value += 1;
      else if (r < 0.6) seed[1].value += 1;
      else if (r < 0.8) seed[2].value += 1;
      else seed[3].value += 1;
    }
    return seed;
  }, [completed.data]);

  return (
    <Card title="Risk distribution" description="Completed sessions bucketed by final risk score.">
      {error ? (
        <ErrorState error={error} onRetry={onRetry} />
      ) : loading || completed.isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : buckets.every((b) => b.value === 0) ? (
        <div className="py-8 text-center text-sm text-muted">
          No completed sessions with risk scores yet.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={buckets} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} innerRadius={50} paddingAngle={2}>
              {buckets.map((b, i) => (
                <Cell key={i} fill={b.color} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: "#12121a", border: "1px solid #27272a", borderRadius: 8 }} />
            <Legend wrapperStyle={{ fontSize: 12, color: "#a1a1aa" }} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
