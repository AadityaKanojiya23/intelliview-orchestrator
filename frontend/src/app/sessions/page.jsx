"use client";
import { useState, useMemo, lazy, Suspense } from "react";
import useSWR from "swr";
import { Play, RefreshCcw } from "lucide-react";
import Card from "@/components/Card";
import { StatusBadge, Badge } from "@/components/Badge";
import { Skeleton, ErrorState, EmptyState } from "@/components/States";
import { SearchInput } from "@/components/SearchInput";
import Pipeline from "@/components/Pipeline";
import { endpoints } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { cn, formatDate, riskColor } from "@/lib/utils";
import { toast } from "@/lib/toast";

const SessionDetail = lazy(() => import("@/components/SessionDetail"));
const TABS = ["active", "completed", "failed"];
function SessionsPage() {
  const [tab, setTab] = useState("active");
  const [search, setSearch] = useState("");
  const [openId, setOpenId] = useState(null);
  const token = useAppStore((s) => s.token);
  const active = useSWR("/active-sessions", { refreshInterval: 2e3 });
  const completed = useSWR("/completed-sessions?limit=100", { refreshInterval: 1e4 });
  const failed = useSWR("/failed-sessions?limit=100", { refreshInterval: 1e4 });
  const data = tab === "active" ? active : tab === "completed" ? completed : failed;
  const filtered = useMemo(() => {
    if (!data.data?.sessions) return [];
    if (!search.trim()) return data.data.sessions;
    const q = search.toLowerCase();
    return data.data.sessions.filter(
      (s) => s.session_id.toLowerCase().includes(q) || s.candidate_id.toLowerCase().includes(q)
    );
  }, [data.data?.sessions, search]);
  return /* @__PURE__ */ jsxs("div", { className: "space-y-6 animate-fade-in", children: [
    /* @__PURE__ */ jsx("div", { className: "flex items-end justify-between", children: /* @__PURE__ */ jsxs("div", { children: [
      /* @__PURE__ */ jsx("h1", { className: "text-2xl font-semibold text-zinc-50", children: "Sessions" }),
      /* @__PURE__ */ jsx("p", { className: "text-sm text-muted", children: "Start new interviews and review historical results." })
    ] }) }),
    /* @__PURE__ */ jsx(StartInterviewForm, { disabled: !token }),
    /* @__PURE__ */ jsxs(Card, { children: [
      /* @__PURE__ */ jsxs("div", { className: "mb-4 flex flex-wrap items-center gap-2", children: [
        TABS.map((t) => /* @__PURE__ */ jsx(
          "button",
          {
            onClick: () => setTab(t),
            className: cn(
              "rounded-md px-3 py-1.5 text-xs font-medium capitalize",
              tab === t ? "bg-accent/15 text-accent-light" : "text-muted hover:bg-bg-card hover:text-zinc-200"
            ),
            children: t
          },
          t
        )),
        /* @__PURE__ */ jsxs("div", { className: "ml-auto flex items-center gap-2", children: [
          /* @__PURE__ */ jsx(SearchInput, { value: search, onChange: setSearch, placeholder: "Filter by id or candidate\u2026", className: "w-64" }),
          /* @__PURE__ */ jsxs(
            "button",
            {
              onClick: () => data.mutate(),
              className: "flex items-center gap-1 rounded-md border border-border bg-bg-card px-2 py-1 text-xs text-muted hover:text-zinc-200",
              children: [
                /* @__PURE__ */ jsx(RefreshCcw, { size: 12 }),
                " Refresh"
              ]
            }
          )
        ] })
      ] }),
      data.error ? /* @__PURE__ */ jsx(ErrorState, { error: data.error, onRetry: () => data.mutate() }) : !data.data ? /* @__PURE__ */ jsx(Skeleton, { className: "h-32 w-full" }) : filtered.length === 0 ? /* @__PURE__ */ jsx(EmptyState, { title: search ? "No matches" : `No ${tab} sessions`, description: search ? "Try a different search term." : "Sessions matching this state will appear here." }) : /* @__PURE__ */ jsx("div", { className: "overflow-x-auto", children: /* @__PURE__ */ jsxs("table", { className: "w-full text-sm", children: [
        /* @__PURE__ */ jsx("thead", { className: "text-left text-xs uppercase tracking-wide text-muted", children: /* @__PURE__ */ jsxs("tr", { children: [
          /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Session" }),
          /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Pipeline" }),
          /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Status" }),
          /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Risk" }),
          /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Worker" }),
          /* @__PURE__ */ jsx("th", { className: "py-2 pr-4", children: "Updated" })
        ] }) }),
        /* @__PURE__ */ jsx("tbody", { children: filtered.map((s) => /* @__PURE__ */ jsxs(
          "tr",
          {
            onClick: () => setOpenId(s.session_id),
            className: "cursor-pointer border-t border-border transition-colors hover:bg-bg-card/50",
            children: [
              /* @__PURE__ */ jsx("td", { className: "py-2 pr-4 font-mono text-xs text-zinc-300", children: s.session_id }),
              /* @__PURE__ */ jsx("td", { className: "py-2 pr-4", children: /* @__PURE__ */ jsx(Pipeline, { current: s.status }) }),
              /* @__PURE__ */ jsx("td", { className: "py-2 pr-4", children: /* @__PURE__ */ jsx(StatusBadge, { status: s.status }) }),
              /* @__PURE__ */ jsx("td", { className: "py-2 pr-4", children: s.risk_score != null ? /* @__PURE__ */ jsx(Badge, { variant: riskColor(s.risk_score), children: s.risk_score.toFixed(2) }) : /* @__PURE__ */ jsx("span", { className: "text-muted", children: "\u2014" }) }),
              /* @__PURE__ */ jsx("td", { className: "py-2 pr-4 font-mono text-xs text-muted", children: s.assigned_node ?? "\u2014" }),
              /* @__PURE__ */ jsx("td", { className: "py-2 pr-4 text-muted", children: formatDate(s.updated_at ?? s.end_time) })
            ]
          },
          s.session_id
        )) })
      ] }) })
    ] }),
    /* @__PURE__ */ jsx(Suspense, { fallback: null, children: /* @__PURE__ */ jsx(SessionDetail, { sessionId: openId, onClose: () => setOpenId(null) }) })
  ] });
}
function StartInterviewForm({ disabled }) {
  const [candidate, setCandidate] = useState("");
  const [priority, setPriority] = useState("medium");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  async function submit(e) {
    e.preventDefault();
    if (!candidate.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const r = await endpoints.startInterview({ candidate_id: candidate.trim(), priority });
      toast.success("Interview started", `Session ${r.session_id} queued for processing`);
      setCandidate("");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      toast.error("Failed to start interview", msg);
    } finally {
      setSubmitting(false);
    }
  }
  return /* @__PURE__ */ jsxs(Card, { title: "Start interview", description: "Enqueue a new session for processing.", children: [
    /* @__PURE__ */ jsxs("form", { onSubmit: submit, className: "flex flex-wrap items-end gap-3", children: [
      /* @__PURE__ */ jsxs("div", { className: "flex-1 min-w-[200px]", children: [
        /* @__PURE__ */ jsx("label", { className: "block text-xs text-muted", children: "Candidate ID" }),
        /* @__PURE__ */ jsx(
          "input",
          {
            value: candidate,
            onChange: (e) => setCandidate(e.target.value),
            placeholder: "cand-1234",
            className: "mt-1 w-full rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-zinc-100 placeholder:text-muted focus:border-accent focus:outline-none"
          }
        )
      ] }),
      /* @__PURE__ */ jsxs("div", { children: [
        /* @__PURE__ */ jsx("label", { className: "block text-xs text-muted", children: "Priority" }),
        /* @__PURE__ */ jsxs(
          "select",
          {
            value: priority,
            onChange: (e) => setPriority(e.target.value),
            className: "mt-1 rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-zinc-100 focus:border-accent focus:outline-none",
            children: [
              /* @__PURE__ */ jsx("option", { value: "low", children: "low" }),
              /* @__PURE__ */ jsx("option", { value: "medium", children: "medium" }),
              /* @__PURE__ */ jsx("option", { value: "high", children: "high" })
            ]
          }
        )
      ] }),
      /* @__PURE__ */ jsxs(
        "button",
        {
          type: "submit",
          disabled: disabled || submitting || !candidate.trim(),
          className: "flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-dark disabled:opacity-50",
          children: [
            /* @__PURE__ */ jsx(Play, { size: 14 }),
            " ",
            submitting ? "Starting\u2026" : "Start"
          ]
        }
      )
    ] }),
    error && /* @__PURE__ */ jsx("div", { className: "mt-3 text-xs text-rose-400", children: error }),
    disabled && /* @__PURE__ */ jsx("div", { className: "mt-2 text-xs text-amber-400", children: "Set an API token in the top bar to start sessions." })
  ] });
}
export {
  SessionsPage as default
};
