"use client";
import { Shimmer } from "@/components/Shimmer";
import { IllustrationEmpty, IllustrationError } from "@/components/Illustrations";
import { cn } from "@/lib/utils";
import { jsx, jsxs } from "react/jsx-runtime";
function Skeleton({ className }) {
  return /* @__PURE__ */ jsx(Shimmer, { className });
}
function ErrorState({ error, onRetry }) {
  return /* @__PURE__ */ jsx("div", { className: "rounded-md border border-rose-500/30 bg-rose-500/5 p-4 text-sm text-rose-300", children: /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-3", children: [
    /* @__PURE__ */ jsx(IllustrationError, { className: "h-12 w-16 shrink-0" }),
    /* @__PURE__ */ jsxs("div", { className: "min-w-0 flex-1", children: [
      /* @__PURE__ */ jsx("div", { className: "font-medium", children: "Something went wrong" }),
      /* @__PURE__ */ jsx("div", { className: "mt-1 text-xs text-rose-400", children: error.message }),
      onRetry && /* @__PURE__ */ jsx(
        "button",
        {
          onClick: onRetry,
          className: "mt-2 rounded-md border border-rose-500/30 px-2 py-1 text-xs text-rose-200 hover:bg-rose-500/10",
          children: "Retry"
        }
      )
    ] })
  ] }) });
}
function EmptyState({ title, description, className }) {
  return /* @__PURE__ */ jsxs("div", { className: cn("flex flex-col items-center justify-center rounded-md border border-dashed border-border py-10 text-center", className), children: [
    /* @__PURE__ */ jsx(IllustrationEmpty, { className: "mb-3 h-20 w-32" }),
    /* @__PURE__ */ jsx("div", { className: "text-sm font-medium text-zinc-300", children: title }),
    description && /* @__PURE__ */ jsx("div", { className: "mt-1 text-xs text-muted", children: description })
  ] });
}
export {
  EmptyState,
  ErrorState,
  Skeleton
};
