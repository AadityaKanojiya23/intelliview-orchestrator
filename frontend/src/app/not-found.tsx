import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-lg rounded-lg border border-border bg-bg-panel p-8 text-center" role="alert">
      <h2 className="text-xl font-semibold text-zinc-100">404 — Page not found</h2>
      <p className="mt-2 text-sm text-muted">The page you were looking for doesn&apos;t exist.</p>
      <Link
        href="/"
        className="mt-4 inline-block rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
      >
        Back to dashboard
      </Link>
    </div>
  );
}
