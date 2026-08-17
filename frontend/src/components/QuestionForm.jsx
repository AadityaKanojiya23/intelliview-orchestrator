"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

const CATEGORIES = ["technical", "behavioral", "situational"];
const DIFFICULTIES = [
  { label: "Easy", value: "easy" },
  { label: "Medium", value: "medium" },
  { label: "Hard", value: "hard" },
];

/**
 * QuestionForm — reusable form for Create and Edit modes.
 *
 * @param {object|null} initial    null = create mode; question object = edit mode
 * @param {function}    onSubmit   called with { text, category, difficulty, tags }
 * @param {function}    onCancel   called when Cancel is clicked
 * @param {boolean}     loading    disables inputs and shows spinner on submit
 */
export default function QuestionForm({ initial = null, onSubmit, onCancel, loading = false }) {
  const [text, setText] = useState("");
  const [category, setCategory] = useState("technical");
  const [difficulty, setDifficulty] = useState("medium");
  const [tags, setTags] = useState("");
  const [errors, setErrors] = useState({});

  // Populate / reset fields when initial changes
  useEffect(() => {
    if (initial) {
      setText(initial.text ?? "");
      setCategory(initial.category ?? "technical");
      setDifficulty(initial.difficulty ?? "medium");
      setTags(Array.isArray(initial.tags) ? initial.tags.join(", ") : "");
    } else {
      setText("");
      setCategory("technical");
      setDifficulty("medium");
      setTags("");
    }
    setErrors({});
  }, [initial]);

  function validate() {
    const e = {};
    if (!text.trim()) e.text = "Question text is required.";
    if (text.trim().length > 1000) e.text = "Must be 1000 characters or fewer.";
    return e;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    const parsedTags = tags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    onSubmit({ text: text.trim(), category, difficulty, tags: parsedTags });
  }

  const selectClass =
    "w-full rounded-md border border-border bg-bg-card px-3 py-1.5 text-sm text-zinc-100 " +
    "focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent transition-colors";

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {/* Question Text */}
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-zinc-300" htmlFor="qf-text">
          Question Text <span className="text-rose-400">*</span>
        </label>
        <textarea
          id="qf-text"
          rows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter the interview question…"
          disabled={loading}
          aria-invalid={!!errors.text}
          aria-describedby={errors.text ? "qf-text-error" : undefined}
          className={
            "w-full rounded-md border bg-bg-card px-3 py-1.5 text-sm text-zinc-100 " +
            "placeholder:text-muted resize-none focus:outline-none focus:ring-2 transition-colors " +
            (errors.text
              ? "border-rose-500/60 focus:ring-rose-500/40"
              : "border-border focus:ring-accent/50 focus:border-accent") +
            " disabled:opacity-50 disabled:cursor-not-allowed"
          }
        />
        {errors.text && (
          <p id="qf-text-error" className="text-xs text-rose-400">
            {errors.text}
          </p>
        )}
      </div>

      {/* Category */}
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-zinc-300" htmlFor="qf-category">
          Category <span className="text-rose-400">*</span>
        </label>
        <select
          id="qf-category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          disabled={loading}
          className={selectClass}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Difficulty */}
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-zinc-300" htmlFor="qf-difficulty">
          Difficulty <span className="text-rose-400">*</span>
        </label>
        <select
          id="qf-difficulty"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
          disabled={loading}
          className={selectClass}
        >
          {DIFFICULTIES.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>
      </div>

      {/* Tags */}
      <Input
        label="Tags (optional)"
        id="qf-tags"
        type="text"
        value={tags}
        onChange={(e) => setTags(e.target.value)}
        placeholder="e.g. Python, Machine Learning, AI"
        disabled={loading}
        hint="Separate multiple tags with commas."
      />

      {/* Actions */}
      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button type="button" variant="secondary" size="md" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" size="md" loading={loading}>
          {initial ? "Save Changes" : "Add Question"}
        </Button>
      </div>
    </form>
  );
}
