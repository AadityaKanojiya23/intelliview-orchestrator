"use client";
import { useMemo } from "react";
import useSWR from "swr";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, PieChart, Pie, Cell, Legend } from "recharts";
import Card from "@/components/Card";
import Stat from "@/components/Stat";
import { Skeleton, ErrorState } from "@/components/States";
import { jsx, jsxs } from "react/jsx-runtime";
function AnalyticsPage() {
  const stats = useSWR("/session-statistics", { refreshInterval: 1e4 });
  const faults = useSWR("/fault-statistics", { refreshInterval: 1e4 });
  const dlq = useSWR("/dead-letter-queue?limit=50", { refreshInterval: 1e4 });
  const breakdown = stats.data ? Object.entries(stats.data.status_breakdown).map(([status, count]) => ({ status, count })) : [];
  return /* @__PURE__ */ jsxs("div", { className: "space-y-6 animate-fade-in", children: [
    /* @__PURE__ */ jsxs("div", { children: [
      /* @__PURE__ */ jsx("h1", { className: "text-2xl font-semibold text-zinc-50", children: "Analytics" }),
      /* @__PURE__ */ jsx("p", { className: "text-sm text-muted", children: "Risk distribution, failure modes, and retry behavior." })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4", children: [
      /* @__PURE__ */ jsx(Stat, { label: "Total sessions", value: stats.data?.total_sessions ?? /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-12" }) }),
      /* @__PURE__ */ jsx(Stat, { label: "Avg risk", value: stats.data ? stats.data.risk_score_stats.average_risk_score.toFixed(3) : /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-16" }) }),
      /* @__PURE__ */ jsx(Stat, { label: "High risk", value: stats.data?.risk_score_stats.high_risk_sessions ?? /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-12" }) }),
      /* @__PURE__ */ jsx(Stat, { label: "DLQ size", value: dlq.data?.count ?? /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-12" }) })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "grid grid-cols-1 gap-4 lg:grid-cols-2", children: [
      /* @__PURE__ */ jsx(Card, { title: "Sessions by status", description: "Distribution across the lifecycle states.", children: stats.error ? /* @__PURE__ */ jsx(ErrorState, { error: stats.error, onRetry: () => stats.mutate() }) : !stats.data ? /* @__PURE__ */ jsx(Skeleton, { className: "h-64 w-full" }) : /* @__PURE__ */ jsx(ResponsiveContainer, { width: "100%", height: 280, children: /* @__PURE__ */ jsxs(BarChart, { data: breakdown, children: [
        /* @__PURE__ */ jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "#27272a" }),
        /* @__PURE__ */ jsx(XAxis, { dataKey: "status", stroke: "#71717a", fontSize: 11 }),
        /* @__PURE__ */ jsx(YAxis, { stroke: "#71717a", fontSize: 11 }),
        /* @__PURE__ */ jsx(Tooltip, { contentStyle: { background: "#12121a", border: "1px solid #27272a", borderRadius: 8 } }),
        /* @__PURE__ */ jsx(Bar, { dataKey: "count", fill: "#6366f1", radius: [4, 4, 0, 0] })
      ] }) }) }),
      /* @__PURE__ */ jsx(Card, { title: "Failure breakdown", description: "Counts grouped by failure type.", children: faults.error ? /* @__PURE__ */ jsx(ErrorState, { error: faults.error, onRetry: () => faults.mutate() }) : !faults.data ? /* @__PURE__ */ jsx(Skeleton, { className: "h-64 w-full" }) : Object.keys(faults.data.fault_statistics.failures_by_type).length === 0 ? /* @__PURE__ */ jsx("div", { className: "py-8 text-center text-sm text-muted", children: "No failures recorded." }) : /* @__PURE__ */ jsx(ResponsiveContainer, { width: "100%", height: 280, children: /* @__PURE__ */ jsxs(
        BarChart,
        {
          data: Object.entries(faults.data.fault_statistics.failures_by_type).map(([type, count]) => ({ type, count })),
          children: [
            /* @__PURE__ */ jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "#27272a" }),
            /* @__PURE__ */ jsx(XAxis, { dataKey: "type", stroke: "#71717a", fontSize: 11 }),
            /* @__PURE__ */ jsx(YAxis, { stroke: "#71717a", fontSize: 11 }),
            /* @__PURE__ */ jsx(Tooltip, { contentStyle: { background: "#12121a", border: "1px solid #27272a", borderRadius: 8 } }),
            /* @__PURE__ */ jsx(Bar, { dataKey: "count", fill: "#ef4444", radius: [4, 4, 0, 0] })
          ]
        }
      ) }) })
    ] }),
    /* @__PURE__ */ jsx(RiskDistribution, { stats: stats.data, error: stats.error, onRetry: () => stats.mutate(), loading: !stats.data && !stats.error })
  ] });
}
function RiskDistribution({ stats, error, onRetry, loading }) {
  const completed = useSWR("/completed-sessions?limit=100", { refreshInterval: 1e4 });
  const buckets = useMemo(() => {
    const seed = [
      { name: "Low (<0.3)", color: "#10b981", value: 0 },
      { name: "Medium (0.3-0.6)", color: "#f59e0b", value: 0 },
      { name: "High (0.6-0.8)", color: "#f97316", value: 0 },
      { name: "Critical (\u22650.8)", color: "#ef4444", value: 0 }
    ];
    for (const s of completed.data?.sessions ?? []) {
      const r = s.risk_score;
      if (typeof r !== "number") continue;
      if (r < 0.3) seed[0].value += 1;
      else if (r < 0.6) seed[1].value += 1;
      else if (r < 0.8) seed[2].value += 1;
      else seed[3].value += 1;
    }
    return seed;
  }, [completed.data]);
  return /* @__PURE__ */ jsx(Card, { title: "Risk distribution", description: "Completed sessions bucketed by final risk score.", children: error ? /* @__PURE__ */ jsx(ErrorState, { error, onRetry }) : loading || completed.isLoading ? /* @__PURE__ */ jsx(Skeleton, { className: "h-64 w-full" }) : buckets.every((b) => b.value === 0) ? /* @__PURE__ */ jsx("div", { className: "py-8 text-center text-sm text-muted", children: "No completed sessions with risk scores yet." }) : /* @__PURE__ */ jsx(ResponsiveContainer, { width: "100%", height: 280, children: /* @__PURE__ */ jsxs(PieChart, { children: [
    /* @__PURE__ */ jsx(Pie, { data: buckets, dataKey: "value", nameKey: "name", cx: "50%", cy: "50%", outerRadius: 90, innerRadius: 50, paddingAngle: 2, children: buckets.map((b, i) => /* @__PURE__ */ jsx(Cell, { fill: b.color }, i)) }),
    /* @__PURE__ */ jsx(Tooltip, { contentStyle: { background: "#12121a", border: "1px solid #27272a", borderRadius: 8 } }),
    /* @__PURE__ */ jsx(Legend, { wrapperStyle: { fontSize: 12, color: "#a1a1aa" } })
  ] }) }) });
}
export {
  AnalyticsPage as default
};
