"use client";
import { useState, useMemo } from "react";
import useSWR from "swr";
import { Cpu, Server, Activity } from "lucide-react";
import Card from "@/components/Card";
import Stat from "@/components/Stat";
import { StatusBadge, Badge } from "@/components/Badge";
import { Skeleton, ErrorState, EmptyState } from "@/components/States";
import { SearchInput } from "@/components/SearchInput";
import { formatPercent, formatRelative } from "@/lib/utils";
import { jsx, jsxs } from "react/jsx-runtime";
function WorkersPage() {
  const workers = useSWR("/workers", { refreshInterval: 4e3 });
  const stats = useSWR("/worker-statistics", { refreshInterval: 5e3 });
  const scheduling = useSWR("/scheduling-status", { refreshInterval: 5e3 });
  const [search, setSearch] = useState("");
  const filtered = useMemo(() => {
    if (!workers.data?.workers) return [];
    if (!search.trim()) return workers.data.workers;
    const q = search.toLowerCase();
    return workers.data.workers.filter((w) => w.worker_id.toLowerCase().includes(q));
  }, [workers.data?.workers, search]);
  return /* @__PURE__ */ jsxs("div", { className: "space-y-6 animate-fade-in", children: [
    /* @__PURE__ */ jsxs("div", { children: [
      /* @__PURE__ */ jsx("h1", { className: "text-2xl font-semibold text-zinc-50", children: "Workers" }),
      /* @__PURE__ */ jsx("p", { className: "text-sm text-muted", children: "Registered worker nodes, capacity, and live utilization." })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4", children: [
      /* @__PURE__ */ jsx(Stat, { label: "Total", value: stats.data?.total_workers ?? /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-12" }), icon: /* @__PURE__ */ jsx(Server, { size: 16 }) }),
      /* @__PURE__ */ jsx(
        Stat,
        {
          label: "Healthy",
          value: stats.data ? `${stats.data.healthy_workers}/${stats.data.total_workers}` : /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-16" }),
          icon: /* @__PURE__ */ jsx(Activity, { size: 16 })
        }
      ),
      /* @__PURE__ */ jsx(
        Stat,
        {
          label: "Utilization",
          value: stats.data ? formatPercent(stats.data.system_utilization_percent) : /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-16" }),
          icon: /* @__PURE__ */ jsx(Cpu, { size: 16 })
        }
      ),
      /* @__PURE__ */ jsx(
        Stat,
        {
          label: "Strategy",
          value: scheduling.data?.current_strategy ?? /* @__PURE__ */ jsx(Skeleton, { className: "h-7 w-24" }),
          hint: scheduling.data?.can_accept_tasks ? "Accepting tasks" : "At capacity"
        }
      )
    ] }),
    /* @__PURE__ */ jsx(Card, { title: "Worker details", description: "Live per-worker stats.", action: /* @__PURE__ */ jsx(SearchInput, { value: search, onChange: setSearch, placeholder: "Filter workers\u2026", className: "w-56" }), children: workers.error ? /* @__PURE__ */ jsx(ErrorState, { error: workers.error, onRetry: () => workers.mutate() }) : !workers.data ? /* @__PURE__ */ jsx(Skeleton, { className: "h-32 w-full" }) : workers.data.workers.length === 0 ? /* @__PURE__ */ jsx(EmptyState, { title: "No workers", description: "Workers register themselves on startup." }) : filtered.length === 0 ? /* @__PURE__ */ jsx(EmptyState, { title: "No matches", description: "Try a different filter." }) : /* @__PURE__ */ jsx("div", { className: "overflow-x-auto", children: /* @__PURE__ */ jsxs("table", { className: "w-full text-sm", children: [
      /* @__PURE__ */ jsx("thead", { className: "text-left text-xs uppercase tracking-wide text-muted", children: /* @__PURE__ */ jsxs("tr", { children: [
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Worker" }),
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Status" }),
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Active" }),
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Capacity" }),
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Utilization" }),
        /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Heartbeat" })
      ] }) }),
      /* @__PURE__ */ jsx("tbody", { children: filtered.map((w) => {
        const util = w.capacity ? w.active_tasks / w.capacity * 100 : 0;
        return /* @__PURE__ */ jsxs("tr", { className: "border-t border-border", children: [
          /* @__PURE__ */ jsx("td", { className: "py-2 pr-4 font-mono text-xs text-zinc-200", children: w.worker_id }),
          /* @__PURE__ */ jsx("td", { className: "py-2 pr-4", children: /* @__PURE__ */ jsx(StatusBadge, { status: w.health_status }) }),
          /* @__PURE__ */ jsx("td", { className: "py-2 pr-4", children: w.active_tasks }),
          /* @__PURE__ */ jsx("td", { className: "py-2 pr-4", children: w.capacity }),
          /* @__PURE__ */ jsx("td", { className: "py-2 pr-4", children: /* @__PURE__ */ jsx(Badge, { variant: util > 90 ? "danger" : util > 70 ? "warn" : "success", children: formatPercent(util) }) }),
          /* @__PURE__ */ jsx("td", { className: "py-2 pr-4 text-muted", children: formatRelative(w.last_heartbeat) })
        ] }, w.worker_id);
      }) })
    ] }) }) })
  ] });
}
export {
  WorkersPage as default
};
