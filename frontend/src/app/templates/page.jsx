"use client";
import { useState, useMemo } from "react";
import useSWR from "swr";
import { useRouter } from "next/navigation";
import {
  Clock,
  ListChecks,
  Plus,
  Play,
  CheckCircle2,
} from "lucide-react";
import Card from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Skeleton, ErrorState, EmptyState } from "@/components/States";
import { SearchInput, Button, Input } from "@/components/ui";
import { Dialog, DialogContent, DialogTitle } from "@/components/Dialog";
import { endpoints } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { toast } from "@/lib/toast";
import { cn } from "@/lib/utils";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const INTERVIEW_TYPES = ["technical", "behavioral", "mixed"];

const DIST_COLORS = [
  "bg-indigo-500",
  "bg-emerald-500",
  "bg-amber-500",
  "bg-rose-500",
  "bg-sky-500",
  "bg-violet-500",
  "bg-pink-500",
  "bg-teal-500",
];

function CategoryDistribution({ distribution }) {
  const entries = Object.entries(distribution || {});
  if (entries.length === 0) {
    return <div className="text-xs text-muted">No category breakdown set.</div>;
  }
  return (
    <div>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-bg-card">
        {entries.map(([key, value], i) => (
          <div
            key={key}
            className={DIST_COLORS[i % DIST_COLORS.length]}
            style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }}
            title={`${key}: ${(value * 100).toFixed(0)}%`}
          />
        ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
        {entries.map(([key, value], i) => (
          <div key={key} className="flex items-center gap-1.5 text-xs text-muted">
            <span className={cn("h-2 w-2 rounded-full", DIST_COLORS[i % DIST_COLORS.length])} />
            <span className="capitalize">{key}</span>
            <span className="text-zinc-400">{(value * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TemplateCard({ template, selected, onSelect }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(template)}
      className={cn(
        "flex w-full flex-col rounded-xl border bg-bg-panel p-5 text-left shadow-sm transition-all hover:border-accent/50",
        selected ? "border-accent ring-2 ring-accent/30" : "border-border"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold text-zinc-100">{template.name}</h3>
          {template.description && (
            <p className="mt-0.5 line-clamp-2 text-xs text-muted">{template.description}</p>
          )}
        </div>
        {selected ? (
          <CheckCircle2 size={18} className="shrink-0 text-accent" />
        ) : (
          <Badge variant="accent" className="capitalize shrink-0">
            {template.interview_type}
          </Badge>
        )}
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs text-muted">
        <span className="flex items-center gap-1.5">
          <Clock size={13} />
          {template.duration_minutes} min
        </span>
        <span className="flex items-center gap-1.5">
          <ListChecks size={13} />
          {template.question_count} questions
        </span>
        {template.usage_count > 0 && (
          <span className="ml-auto text-[11px] text-muted">
            Used {template.usage_count}x
          </span>
        )}
      </div>

      <div className="mt-4">
        <div className="mb-1.5 text-[11px] uppercase tracking-wide text-muted">
          Category distribution
        </div>
        <CategoryDistribution distribution={template.category_distribution} />
      </div>
    </button>
  );
}

function CreateTemplateDialog({ open, onOpenChange, onCreated }) {
  const [name, setName] = useState("");
  const [interviewType, setInterviewType] = useState("technical");
  const [description, setDescription] = useState("");
  const [duration, setDuration] = useState(60);
  const [questionCount, setQuestionCount] = useState(10);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const template = await endpoints.createTemplate({
        name: name.trim(),
        interview_type: interviewType,
        description: description.trim() || null,
        duration_minutes: Number(duration) || 60,
        question_count: Number(questionCount) || 10,
      });
      toast.success("Template created", template.name);
      setName("");
      setDescription("");
      onCreated?.();
      onOpenChange(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      toast.error("Failed to create template", msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="mx-auto max-w-md" onClose={() => onOpenChange(false)}>
        <div className="border-b border-border px-5 py-4">
          <DialogTitle>New template</DialogTitle>
        </div>
        <form onSubmit={submit} className="space-y-4 px-5 py-4">
          <Input
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Senior Backend Engineer"
            autoFocus
          />
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-300">Interview type</label>
            <select
              value={interviewType}
              onChange={(e) => setInterviewType(e.target.value)}
              className="w-full rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-zinc-100 focus:border-accent focus:outline-none"
            >
              {INTERVIEW_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <Input
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional summary of what this template covers"
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Duration (minutes)"
              type="number"
              min={1}
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
            <Input
              label="Question count"
              type="number"
              min={1}
              value={questionCount}
              onChange={(e) => setQuestionCount(e.target.value)}
            />
          </div>
          {error && <div className="text-xs text-rose-400">{error}</div>}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={submitting} disabled={!name.trim()}>
              Create template
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function StartInterviewPanel({ template, onDeselect }) {
  const token = useAppStore((s) => s.token);
  const router = useRouter();
  const [candidateId, setCandidateId] = useState("");
  const [candidateName, setCandidateName] = useState("");
  const [priority, setPriority] = useState("medium");
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);

  async function startInterview(e) {
    e.preventDefault();
    if (!candidateId.trim() || !template) return;
    setStarting(true);
    setError(null);
    try {
      const r = await endpoints.startInterview({
        candidate_id: candidateId.trim(),
        candidate_name: candidateName.trim() || undefined,
        priority,
        template_id: template.template_id,
      });
      toast.success(
        "Interview started",
        `Session ${r.session_id} queued using "${template.name}"`
      );
      setCandidateId("");
      setCandidateName("");
      router.push("/sessions");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      toast.error("Failed to start interview", msg);
    } finally {
      setStarting(false);
    }
  }

  if (!template) {
    return (
      <Card title="Start interview">
        <EmptyState
          title="No template selected"
          description="Pick a template from the list to configure and start an interview."
        />
      </Card>
    );
  }

  return (
    <Card
      title="Start interview"
      description={`Using template "${template.name}"`}
      action={
        <Button variant="ghost" size="sm" onClick={onDeselect}>
          Change
        </Button>
      }
    >
      <div className="mb-4 rounded-md border border-border bg-bg-card px-3 py-2.5 text-xs text-muted">
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          <span>
            Type: <span className="capitalize text-zinc-300">{template.interview_type}</span>
          </span>
          <span>
            Duration: <span className="text-zinc-300">{template.duration_minutes} min</span>
          </span>
          <span>
            Questions: <span className="text-zinc-300">{template.question_count}</span>
          </span>
        </div>
      </div>

      <form onSubmit={startInterview} className="space-y-3">
        <Input
          label="Candidate ID"
          value={candidateId}
          onChange={(e) => setCandidateId(e.target.value)}
          placeholder="cand-1234"
        />
        <Input
          label="Candidate name (optional)"
          value={candidateName}
          onChange={(e) => setCandidateName(e.target.value)}
          placeholder="Jane Doe"
        />
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-300">Priority</label>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="w-full rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-zinc-100 focus:border-accent focus:outline-none"
          >
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </div>
        {error && <div className="text-xs text-rose-400">{error}</div>}
        {!token && (
          <div className="text-xs text-amber-400">
            Set an API token in the top bar to start sessions.
          </div>
        )}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full"
          loading={starting}
          disabled={!token || !candidateId.trim()}
          icon={<Play size={14} />}
        >
          {starting ? "Starting…" : "Start Interview"}
        </Button>
      </form>
    </Card>
  );
}

export default function TemplatesPage() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [selected, setSelected] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const token = useAppStore((s) => s.token);

  const { data, error, mutate, isLoading } = useSWR("/templates", { refreshInterval: 15000 });

  const templates = data?.templates ?? [];

  const filtered = useMemo(() => {
    let list = templates;
    if (typeFilter !== "all") {
      list = list.filter((t) => t.interview_type === typeFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (t) =>
          t.name.toLowerCase().includes(q) ||
          (t.description || "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [templates, typeFilter, search]);

  return (
    <ErrorBoundary>
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-zinc-50">Interview Templates</h1>
            <p className="text-sm text-muted">
              Browse templates, then select one to start an interview.
            </p>
          </div>
          <Button
            variant="primary"
            size="lg"
            icon={<Plus size={14} />}
            onClick={() => setCreateOpen(true)}
            disabled={!token}
          >
            New template
          </Button>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="space-y-4 lg:col-span-2">
            <Card>
              <div className="flex flex-wrap items-center gap-2">
                <SearchInput
                  value={search}
                  onChange={setSearch}
                  placeholder="Search templates…"
                  className="min-w-[220px] flex-1"
                />
                <div className="flex items-center gap-1 rounded-md border border-border bg-bg-card p-1">
                  {["all", ...INTERVIEW_TYPES].map((t) => (
                    <button
                      key={t}
                      onClick={() => setTypeFilter(t)}
                      className={cn(
                        "rounded px-2.5 py-1 text-xs font-medium capitalize transition-colors",
                        typeFilter === t
                          ? "bg-accent/15 text-accent-light"
                          : "text-muted hover:text-zinc-200"
                      )}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </Card>

            {error ? (
              <ErrorState error={error} onRetry={() => mutate()} />
            ) : isLoading || !data ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-44 w-full" />
                ))}
              </div>
            ) : filtered.length === 0 ? (
              <EmptyState
                title={
                  search || typeFilter !== "all" ? "No matching templates" : "No templates yet"
                }
                description={
                  search || typeFilter !== "all"
                    ? "Try a different search term or filter."
                    : "Create your first interview template to get started."
                }
              />
            ) : (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {filtered.map((t) => (
                  <TemplateCard
                    key={t.template_id}
                    template={t}
                    selected={selected?.template_id === t.template_id}
                    onSelect={(tpl) =>
                      setSelected((prev) =>
                        prev?.template_id === tpl.template_id ? null : tpl
                      )
                    }
                  />
                ))}
              </div>
            )}
          </div>

          <div className="lg:col-span-1">
            <div className="lg:sticky lg:top-6">
              <StartInterviewPanel template={selected} onDeselect={() => setSelected(null)} />
            </div>
          </div>
        </div>
      </div>

      <CreateTemplateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={() => mutate()}
      />
    </ErrorBoundary>
  );
}
