"use client";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { jsx, jsxs } from "react/jsx-runtime";
function SearchInput({ value, onChange, placeholder = "Search\u2026", className }) {
  return /* @__PURE__ */ jsxs("div", { className: cn("relative", className), children: [
    /* @__PURE__ */ jsx(Search, { size: 14, className: "pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" }),
    /* @__PURE__ */ jsx(
      "input",
      {
        type: "search",
        value,
        onChange: (e) => onChange(e.target.value),
        placeholder,
        className: "w-full rounded-md border border-border bg-bg-card py-1.5 pl-8 pr-3 text-sm text-zinc-100 placeholder:text-muted focus:border-accent focus:outline-none"
      }
    )
  ] });
}
export {
  SearchInput
};
