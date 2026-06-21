"use client";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="mx-auto max-w-lg rounded-lg border border-border bg-bg-panel p-6 text-center" role="alert">
      <h2 className="text-lg font-semibold text-zinc-100">Something went wrong</h2>
      <p className="mt-2 text-sm text-muted">
        {error.message || "An unexpected error occurred while loading this page."}
      </p>
      {error.digest && <p className="mt-1 font-mono text-xs text-muted">digest: {error.digest}</p>}
      <button
        type="button"
        onClick={reset}
        className="mt-4 rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
      >
        Try again
      </button>
    </div>
  );
}
