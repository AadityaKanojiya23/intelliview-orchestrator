"use client";
import useSWR from "swr";
import { Activity, AlertTriangle, CheckCircle2, Users } from "lucide-react";
import Card from "@/components/Card";
import Stat from "@/components/Stat";
import { StatusBadge } from "@/components/Badge";
import { Skeleton, ErrorState, EmptyState } from "@/components/States";
import Sparkline from "@/components/Sparkline";
import { formatPercent, formatRelative } from "@/lib/utils";
import { useEffect, useState } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
function OverviewPage() {
  const health = useSWR("/system-health", { refreshInterval: 3e3 });
  const workers = useSWR("/workers", { refreshInterval: 5e3 });
  const stats = useSWR("/session-statistics", { refreshInterval: 5e3 });
  const active = useSWR("/active-sessions", { refreshInterval: 3e3 });
  const [completedHist, setCompletedHist] = useState([]);
  const [failedHist, setFailedHist] = useState([]);
  const [riskHist, setRiskHist] = useState([]);
  useEffect(() => {
    if (!stats.data) return;
    setCompletedHist((h) => [...h, stats.data.completed_sessions].slice(-20));
    setFailedHist((h) => [...h, stats.data.failed_sessions].slice(-20));
    setRiskHist((h) => [...h, stats.data.risk_score_stats.average_risk_score].slice(-20));
  }, [stats.data?.completed_sessions, stats.data?.failed_sessions, stats.data?.risk_score_stats.average_risk_score]);
  const utilization = (workers.data?.workers ?? []).reduce(
    (acc, w) => acc + (w.capacity ? w.active_tasks / w.capacity * 100 : 0),
    0
  ) / Math.max(1, workers.data?.workers.length ?? 1);
  return /* @__PURE__ */ jsxs("div", { className: "space-y-6 animate-fade-in", children: [
    /* @__PURE__ */ jsxs("div", { children: [
      /* @__PURE__ */ jsx("h1", { className: "text-2xl font-semibold text-zinc-50", children: "Overview" }),
      /* @__PURE__ */ jsx("p", { className: "text-sm text-muted", children: "Real-time system health and throughput." })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4", children: [
      /* @__PURE__ */ jsx(
        Stat,
        {
          label: "System",
          value: health.data ? /* @__PURE__ */ jsx(StatusBadge, { status: health.data.overall_status }) : /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-20" }),
          hint: health.data ? `Updated ${formatRelative(health.data.timestamp)}` : "",
          icon: /* @__PURE__ */ jsx(Activity, { size: 16 })
        }
      ),
      /* @__PURE__ */ jsx(
        Stat,
        {
          label: "Workers",
          value: workers.data ? `${workers.data.healthy_workers}/${workers.data.total_workers}` : /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-12" }),
          hint: workers.data ? `${formatPercent(utilization)} utilization` : "",
          icon: /* @__PURE__ */ jsx(Users, { size: 16 })
        }
      ),
      /* @__PURE__ */ jsx(
        Stat,
        {
          label: "Completed",
          value: stats.data ? stats.data.completed_sessions : /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-12" }),
          hint: stats.data ? `${stats.data.active_sessions} active \xB7 ${stats.data.failed_sessions} failed` : "",
          icon: /* @__PURE__ */ jsx(CheckCircle2, { size: 16 })
        }
      ),
      /* @__PURE__ */ jsx(
        Stat,
        {
          label: "Avg risk",
          value: stats.data ? stats.data.risk_score_stats.average_risk_score.toFixed(3) : /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-16" }),
          hint: stats.data ? `${stats.data.risk_score_stats.high_risk_sessions} high risk` : "",
          icon: /* @__PURE__ */ jsx(AlertTriangle, { size: 16 })
        }
      )
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "grid grid-cols-1 gap-4 sm:grid-cols-3", children: [
      /* @__PURE__ */ jsx(Card, { title: "Completed sessions", description: "Last 20 samples", children: /* @__PURE__ */ jsxs("div", { className: "flex items-center justify-between", children: [
        /* @__PURE__ */ jsx("div", { className: "text-2xl font-semibold text-zinc-50", children: stats.data?.completed_sessions ?? "\u2014" }),
        /* @__PURE__ */ jsx(Sparkline, { data: completedHist, color: "#10b981", width: 140, height: 40 })
      ] }) }),
      /* @__PURE__ */ jsx(Card, { title: "Failed sessions", description: "Last 20 samples", children: /* @__PURE__ */ jsxs("div", { className: "flex items-center justify-between", children: [
        /* @__PURE__ */ jsx("div", { className: "text-2xl font-semibold text-zinc-50", children: stats.data?.failed_sessions ?? "\u2014" }),
        /* @__PURE__ */ jsx(Sparkline, { data: failedHist, color: "#ef4444", width: 140, height: 40 })
      ] }) }),
      /* @__PURE__ */ jsx(Card, { title: "Average risk", description: "Last 20 samples", children: /* @__PURE__ */ jsxs("div", { className: "flex items-center justify-between", children: [
        /* @__PURE__ */ jsx("div", { className: "text-2xl font-semibold text-zinc-50", children: stats.data?.risk_score_stats.average_risk_score.toFixed(3) ?? "\u2014" }),
        /* @__PURE__ */ jsx(Sparkline, { data: riskHist, color: "#f59e0b", width: 140, height: 40 })
      ] }) })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "grid grid-cols-1 gap-4 lg:grid-cols-2", children: [
      /* @__PURE__ */ jsx(Card, { title: "Component health", description: "Live status of each dependency.", children: health.error ? /* @__PURE__ */ jsx(ErrorState, { error: health.error, onRetry: () => health.mutate() }) : !health.data ? /* @__PURE__ */ jsx(Skeleton, { className: "h-32 w-full" }) : /* @__PURE__ */ jsx("ul", { className: "space-y-2 text-sm", children: Object.entries(health.data.components).map(([k, v]) => /* @__PURE__ */ jsxs("li", { className: "flex items-center justify-between rounded-md border border-border bg-bg-card px-3 py-2", children: [
        /* @__PURE__ */ jsx("span", { className: "capitalize text-zinc-300", children: k }),
        /* @__PURE__ */ jsx(StatusBadge, { status: v.status })
      ] }, k)) }) }),
      /* @__PURE__ */ jsx(Card, { title: "Active sessions", description: "In-flight interviews across the cluster.", children: active.error ? /* @__PURE__ */ jsx(ErrorState, { error: active.error, onRetry: () => active.mutate() }) : !active.data ? /* @__PURE__ */ jsx(Skeleton, { className: "h-32 w-full" }) : active.data.sessions.length === 0 ? /* @__PURE__ */ jsx(EmptyState, { title: "No active sessions", description: "Start a new interview to see it here." }) : /* @__PURE__ */ jsx("ul", { className: "space-y-2 text-sm", children: active.data.sessions.slice(0, 6).map((s) => /* @__PURE__ */ jsxs("li", { className: "flex items-center justify-between rounded-md border border-border bg-bg-card px-3 py-2", children: [
        /* @__PURE__ */ jsxs("div", { children: [
          /* @__PURE__ */ jsx("div", { className: "font-mono text-xs text-zinc-300", children: s.session_id }),
          /* @__PURE__ */ jsx("div", { className: "text-xs text-muted", children: s.candidate_id })
        ] }),
        /* @__PURE__ */ jsx(StatusBadge, { status: s.status })
      ] }, s.session_id)) }) })
    ] }),
    /* @__PURE__ */ jsx(Card, { title: "Workers", description: "Currently registered worker nodes.", children: workers.error ? /* @__PURE__ */ jsx(ErrorState, { error: workers.error, onRetry: () => workers.mutate() }) : !workers.data ? /* @__PURE__ */ jsx(Skeleton, { className: "h-24 w-full" }) : workers.data.workers.length === 0 ? /* @__PURE__ */ jsx(EmptyState, { title: "No workers registered", description: "Workers self-register via the worker_agent on startup." }) : /* @__PURE__ */ jsx("div", { className: "overflow-x-auto", children: /* @__PURE__ */ jsxs("table", { className: "w-full text-sm", children: [
      /* @__PURE__ */ jsx("thead", { className: "text-left text-xs uppercase tracking-wide text-muted", children: /* @__PURE__ */ jsxs("tr", { children: [
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Worker" }),
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Status" }),
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Load" }),
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Last heartbeat" })
      ] }) }),
      /* @__PURE__ */ jsx("tbody", { children: workers.data.workers.map((w) => /* @__PURE__ */ jsxs("tr", { className: "border-t border-border", children: [
        /* @__PURE__ */ jsx("td", { className: "py-2 pr-4 font-mono text-xs text-zinc-200", children: w.worker_id }),
        /* @__PURE__ */ jsx("td", { className: "py-2 pr-4", children: /* @__PURE__ */ jsx(StatusBadge, { status: w.health_status }) }),
        /* @__PURE__ */ jsxs("td", { className: "py-2 pr-4", children: [
          w.active_tasks,
          "/",
          w.capacity
        ] }),
        /* @__PURE__ */ jsx("td", { className: "py-2 pr-4 text-muted", children: formatRelative(w.last_heartbeat) })
      ] }, w.worker_id)) })
    ] }) }) })
  ] });
}
export {
  OverviewPage as default
};
