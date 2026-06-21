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

export default function SessionsPage() {
  const [tab, setTab] = useState("active");
  const [search, setSearch] = useState("");
  const [openId, setOpenId] = useState(null);
  const token = useAppStore((s) => s.token);

  const active = useSWR("/active-sessions", { refreshInterval: 2000 });
  const completed = useSWR("/completed-sessions?limit=100", { refreshInterval: 10000 });
  const failed = useSWR("/failed-sessions?limit=100", { refreshInterval: 10000 });

  const data = tab === "active" ? active : tab === "completed" ? completed : failed;

  const filtered = useMemo(() => {
    if (!data.data?.sessions) return [];
    if (!search.trim()) return data.data.sessions;
    const q = search.toLowerCase();
    return data.data.sessions.filter(
      (s) => s.session_id.toLowerCase().includes(q) || (s.candidate_id || "").toLowerCase().includes(q),
    );
  }, [data.data?.sessions, search]);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-50">Sessions</h1>
          <p className="text-sm text-muted">Start new interviews and review historical results.</p>
        </div>
      </div>

      <StartInterviewForm disabled={!token} />

      <Card>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-medium capitalize",
                tab === t ? "bg-accent/15 text-accent-light" : "text-muted hover:bg-bg-card hover:text-zinc-200",
              )}
            >
              {t}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-2">
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Filter by id or candidate…"
              className="w-64"
            />
            <button
              onClick={() => data.mutate()}
              className="flex items-center gap-1 rounded-md border border-border bg-bg-card px-2 py-1 text-xs text-muted hover:text-zinc-200"
            >
              <RefreshCcw size={12} /> Refresh
            </button>
          </div>
        </div>

        {data.error ? (
          <ErrorState error={data.error} onRetry={() => data.mutate()} />
        ) : !data.data ? (
          <Skeleton className="h-32 w-full" />
        ) : filtered.length === 0 ? (
          <EmptyState
            title={search ? "No matches" : `No ${tab} sessions`}
            description={search ? "Try a different search term." : "Sessions matching this state will appear here."}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="py-2 pr-4">Session</th>
                  <th className="py-2 pr-4">Pipeline</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Risk</th>
                  <th className="py-2 pr-4">Worker</th>
                  <th className="py-2 pr-4">Updated</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <tr
                    key={s.session_id}
                    onClick={() => setOpenId(s.session_id)}
                    className="cursor-pointer border-t border-border transition-colors hover:bg-bg-card/50"
                  >
                    <td className="py-2 pr-4 font-mono text-xs text-zinc-300">{s.session_id}</td>
                    <td className="py-2 pr-4">
                      <Pipeline current={s.status} />
                    </td>
                    <td className="py-2 pr-4">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="py-2 pr-4">
                      {s.risk_score != null ? (
                        <Badge variant={riskColor(s.risk_score)}>{s.risk_score.toFixed(2)}</Badge>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td className="py-2 pr-4 font-mono text-xs text-muted">{s.assigned_node ?? "—"}</td>
                    <td className="py-2 pr-4 text-muted">{formatDate(s.updated_at ?? s.end_time)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Suspense fallback={null}>
        <SessionDetail sessionId={openId} onClose={() => setOpenId(null)} />
      </Suspense>
    </div>
  );
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

  return (
    <Card title="Start interview" description="Enqueue a new session for processing.">
      <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
        <div className="min-w-[200px] flex-1">
          <label className="block text-xs text-muted">Candidate ID</label>
          <input
            value={candidate}
            onChange={(e) => setCandidate(e.target.value)}
            placeholder="cand-1234"
            className="mt-1 w-full rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-zinc-100 placeholder:text-muted focus:border-accent focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-muted">Priority</label>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="mt-1 rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-zinc-100 focus:border-accent focus:outline-none"
          >
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={disabled || submitting || !candidate.trim()}
          className="flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-dark disabled:opacity-50"
        >
          <Play size={14} /> {submitting ? "Starting…" : "Start"}
        </button>
      </form>
      {error && <div className="mt-3 text-xs text-rose-400">{error}</div>}
      {disabled && (
        <div className="mt-2 text-xs text-amber-400">Set an API token in the top bar to start sessions.</div>
      )}
    </Card>
  );
}
