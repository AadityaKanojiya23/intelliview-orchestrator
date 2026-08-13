"use client";
import { useState } from "react";
import useSWR from "swr";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Table, Thead, Tbody, Tr, Th, Td } from "@/components/ui/Table";
import { Shimmer } from "@/components/ui/Loader";
import { Dialog, DialogContent, DialogTitle } from "@/components/Dialog";
import QuestionForm from "@/components/QuestionForm";
import { endpoints } from "@/lib/api";
import { toast } from "@/lib/toast";

// ── Difficulty badge ──────────────────────────────────────────
const DIFFICULTY_STYLES = {
  easy: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  hard: "bg-rose-500/15 text-rose-300 border-rose-500/30",
};

function DifficultyBadge({ value }) {
  return (
    <span
      className={
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize " +
        (DIFFICULTY_STYLES[value] ?? "bg-zinc-500/15 text-zinc-300 border-zinc-500/30")
      }
    >
      {value}
    </span>
  );
}

// ── Loading skeleton ──────────────────────────────────────────
function TableSkeleton() {
  return (
    <div className="space-y-2 p-4">
      {[...Array(5)].map((_, i) => (
        <Shimmer key={i} className="h-10 w-full rounded-md" />
      ))}
    </div>
  );
}

// ── Delete confirmation dialog ────────────────────────────────
function DeleteDialog({ question, onConfirm, onCancel, loading }) {
  return (
    <Dialog open={Boolean(question)} onOpenChange={(o) => !o && onCancel()}>
      <DialogContent onClose={onCancel} className="max-w-md">
        <div className="border-b border-border px-5 py-4">
          <DialogTitle>Delete Question?</DialogTitle>
        </div>
        <div className="space-y-4 px-5 py-4">
          <p className="text-sm text-zinc-400">
            This action <span className="font-semibold text-zinc-200">cannot be undone</span>.
          </p>
          {question && (
            <p className="line-clamp-3 rounded-md border border-border bg-bg-card px-3 py-2 text-xs text-zinc-300">
              {question.text}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" size="md" onClick={onCancel} disabled={loading}>
              Cancel
            </Button>
            <Button variant="danger" size="md" loading={loading} onClick={onConfirm}>
              Delete
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── Main page ─────────────────────────────────────────────────
export default function QuestionsPage() {
  // SWR — key is the URL path; global swrFetcher in providers.jsx handles the call
  const { data, error, isLoading, mutate } = useSWR("/questions");

  const questions = data?.questions ?? [];

  // Dialog state
  const [createOpen, setCreateOpen] = useState(false);
  const [editQuestion, setEditQuestion] = useState(null);   // null | question object
  const [deleteTarget, setDeleteTarget] = useState(null);   // null | question object

  // Async operation loading flags
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // ── Handlers ────────────────────────────────────────────────

  async function handleCreate(formData) {
    setSubmitting(true);
    try {
      await endpoints.createQuestion(formData);
      await mutate();
      setCreateOpen(false);
      toast.success("Question added successfully.");
    } catch (err) {
      toast.error("Failed to add question.", err?.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEdit(formData) {
    if (!editQuestion) return;
    setSubmitting(true);
    try {
      await endpoints.updateQuestion(editQuestion.question_id, formData);
      await mutate();
      setEditQuestion(null);
      toast.success("Question updated successfully.");
    } catch (err) {
      toast.error("Failed to update question.", err?.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await endpoints.deleteQuestion(deleteTarget.question_id);
      await mutate();
      setDeleteTarget(null);
      toast.success("Question deleted.");
    } catch (err) {
      toast.error("Failed to delete question.", err?.message);
    } finally {
      setDeleting(false);
    }
  }

  // ── Render ──────────────────────────────────────────────────

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-zinc-100">Question Bank</h1>
          <p className="mt-0.5 text-xs text-muted">
            {isLoading ? "Loading…" : `${questions.length} question${questions.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          icon={<Plus size={13} />}
          onClick={() => setCreateOpen(true)}
        >
          Add Question
        </Button>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-md border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          Failed to load questions. Check the backend connection and try refreshing.
        </div>
      )}

      {/* Table */}
      <div className="rounded-xl border border-border bg-bg-panel">
        {isLoading ? (
          <TableSkeleton />
        ) : (
          <Table>
            <Thead>
              <Tr>
                <Th>Question</Th>
                <Th>Category</Th>
                <Th>Difficulty</Th>
                <Th>Tags</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {questions.length === 0 ? (
                <Tr>
                  <Td colSpan={5} className="py-16 text-center text-sm text-muted">
                    No questions yet. Click &ldquo;Add Question&rdquo; to create the first one.
                  </Td>
                </Tr>
              ) : (
                questions.map((q) => (
                  <Tr key={q.question_id}>
                    {/* Question text */}
                    <Td className="max-w-xs">
                      <p className="line-clamp-2 text-sm text-zinc-200" title={q.text}>
                        {q.text}
                      </p>
                    </Td>

                    {/* Category */}
                    <Td>
                      <span className="capitalize text-sm text-zinc-300">{q.category}</span>
                    </Td>

                    {/* Difficulty */}
                    <Td>
                      <DifficultyBadge value={q.difficulty} />
                    </Td>

                    {/* Tags */}
                    <Td>
                      {(q.tags ?? []).length === 0 ? (
                        <span className="text-xs text-muted">—</span>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {q.tags.map((tag) => (
                            <span
                              key={tag}
                              className="rounded border border-border bg-bg-card px-1.5 py-0.5 text-[10px] text-zinc-400"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </Td>

                    {/* Actions */}
                    <Td>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Pencil size={12} />}
                          onClick={() => setEditQuestion(q)}
                          aria-label="Edit question"
                        >
                          Edit
                        </Button>
                        <Button
                          variant="danger"
                          size="sm"
                          icon={<Trash2 size={12} />}
                          onClick={() => setDeleteTarget(q)}
                          aria-label="Delete question"
                        >
                          Delete
                        </Button>
                      </div>
                    </Td>
                  </Tr>
                ))
              )}
            </Tbody>
          </Table>
        )}
      </div>

      {/* Create dialog */}
      <Dialog open={createOpen} onOpenChange={(o) => !o && setCreateOpen(false)}>
        <DialogContent onClose={() => setCreateOpen(false)} className="max-w-lg">
          <div className="border-b border-border px-5 py-4">
            <DialogTitle>Add New Question</DialogTitle>
          </div>
          <div className="px-5 py-4">
            <QuestionForm
              initial={null}
              onSubmit={handleCreate}
              onCancel={() => setCreateOpen(false)}
              loading={submitting}
            />
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit dialog */}
      <Dialog
        open={Boolean(editQuestion)}
        onOpenChange={(o) => !o && setEditQuestion(null)}
      >
        <DialogContent onClose={() => setEditQuestion(null)} className="max-w-lg">
          <div className="border-b border-border px-5 py-4">
            <DialogTitle>Edit Question</DialogTitle>
          </div>
          <div className="px-5 py-4">
            <QuestionForm
              initial={editQuestion}
              onSubmit={handleEdit}
              onCancel={() => setEditQuestion(null)}
              loading={submitting}
            />
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation dialog */}
      <DeleteDialog
        question={deleteTarget}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        loading={deleting}
      />
    </div>
  );
}
