import { jsx, jsxs } from "react/jsx-runtime";
function Loading() {
  return /* @__PURE__ */ jsxs("div", { className: "flex h-64 items-center justify-center", role: "status", "aria-live": "polite", children: [
    /* @__PURE__ */ jsx("div", { className: "h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-accent" }),
    /* @__PURE__ */ jsx("span", { className: "sr-only", children: "Loading\u2026" })
  ] });
}
export {
  Loading as default
};
