"use client";
import { jsx, jsxs } from "react/jsx-runtime";
function GlobalError({ error, reset }) {
  return /* @__PURE__ */ jsxs("div", { className: "mx-auto max-w-lg rounded-lg border border-border bg-bg-panel p-6 text-center", role: "alert", children: [
    /* @__PURE__ */ jsx("h2", { className: "text-lg font-semibold text-zinc-100", children: "Something went wrong" }),
    /* @__PURE__ */ jsx("p", { className: "mt-2 text-sm text-muted", children: error.message || "An unexpected error occurred while loading this page." }),
    error.digest && /* @__PURE__ */ jsxs("p", { className: "mt-1 font-mono text-xs text-muted", children: [
      "digest: ",
      error.digest
    ] }),
    /* @__PURE__ */ jsx(
      "button",
      {
        type: "button",
        onClick: reset,
        className: "mt-4 rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90",
        children: "Try again"
      }
    )
  ] });
}
export {
  GlobalError as default
};
