"use client";
import { memo } from "react";
import { Dialog, DialogContent, DialogTitle } from "@/components/Dialog";
import Pipeline from "@/components/Pipeline";
import { StatusBadge, Badge } from "@/components/Badge";
import { Shimmer } from "@/components/Shimmer";
import { useAppStore } from "@/lib/store";
import { formatDate, riskColor, formatRelative } from "@/lib/utils";
import { Activity, Calendar, Cpu, Hash, RefreshCw, User } from "lucide-react";
import useSWR from "swr";

function SessionDetailImpl({ sessionId, onClose }) {
  const token = useAppStore((s) => s.token);
  const open = sessionId !== null;
  const { data, error, isLoading, mutate } = useSWR(
    open && token ? `/session-status/${sessionId}` : null,
    { refreshInterval: 2000 },
  );
  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent onClose={onClose} className="max-w-2xl">
        <div className="border-b border-border px-5 py-4">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle>Session detail</DialogTitle>
              <p className="mt-0.5 font-mono text-xs text-muted">{sessionId}</p>
            </div>
            <div className="flex items-center gap-2">
              {data && <StatusBadge status={data.status} />}
              <button
                onClick={() => mutate()}
                className="rounded-md border border-border bg-bg-card p-1.5 text-muted hover:text-zinc-200"
                aria-label="Refresh"
              >
                <RefreshCw size={12} />
              </button>
            </div>
          </div>
        </div>
        <div className="p-5">
          {error && (
            <div className="rounded-md border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300">
              Failed to load session
            </div>
          )}
          {isLoading && !data && (
            <div className="space-y-3">
              <Shimmer className="h-12 w-full" />
              <Shimmer className="h-12 w-full" />
              <Shimmer className="h-20 w-full" />
            </div>
          )}
          {data && (
            <div className="space-y-5">
              <div>
                <h3 className="text-xs font-medium uppercase tracking-wide text-muted">Pipeline</h3>
                <div className="mt-2 rounded-md border border-border bg-bg-card p-3">
                  <Pipeline current={data.status} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Candidate" value={data.candidate_id} icon={User} />
                <Field label="Assigned worker" value={data.assigned_node ?? "—"} icon={Cpu} />
                <Field label="Created" value={formatDate(data.created_at ?? data.updated_at)} icon={Calendar} />
                <Field label="Started" value={formatRelative(data.start_time)} icon={Activity} />
                <Field label="Ended" value={formatRelative(data.end_time)} icon={Activity} />
                <Field
                  label="Risk score"
                  value={
                    data.risk_score != null ? (
                      <Badge variant={riskColor(data.risk_score)}>{data.risk_score.toFixed(3)}</Badge>
                    ) : (
                      "—"
                    )
                  }
                  icon={Hash}
                />
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, value, icon: Icon }) {
  return (
    <div className="rounded-md border border-border bg-bg-card px-3 py-2.5">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-muted">
        <Icon size={10} />
        <span>{label}</span>
      </div>
      <div className="mt-1 text-sm text-zinc-200">{value}</div>
    </div>
  );
}

const SessionDetail = memo(SessionDetailImpl);
export default SessionDetail;
