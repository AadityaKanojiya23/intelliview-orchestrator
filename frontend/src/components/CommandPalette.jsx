"use client";
import { Command } from "cmdk";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Activity,
  Users,
  BarChart3,
  Settings,
  Search,
  Play,
  RefreshCcw,
  Trash2,
  Zap
} from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "@/components/Dialog";
import { jsx, jsxs } from "react/jsx-runtime";
const NAV_ITEMS = [
  { id: "nav:overview", label: "Overview", icon: LayoutDashboard, action: "/", group: "Navigate" },
  { id: "nav:sessions", label: "Sessions", icon: Activity, action: "/sessions", group: "Navigate" },
  { id: "nav:workers", label: "Workers", icon: Users, action: "/workers", group: "Navigate" },
  { id: "nav:analytics", label: "Analytics", icon: BarChart3, action: "/analytics", group: "Navigate" },
  { id: "nav:settings", label: "Settings", icon: Settings, action: "/settings", group: "Navigate" }
];
const ACTIONS = [
  { id: "act:start", label: "Start new interview", icon: Play, action: "start", group: "Actions" },
  { id: "act:refresh", label: "Refresh all data", icon: RefreshCcw, action: "refresh", group: "Actions" },
  { id: "act:detect", label: "Run failure detection", icon: Zap, action: "detect", group: "Actions" },
  { id: "act:clear-cache", label: "Clear session cache", icon: Trash2, action: "clear-cache", group: "Actions" }
];
function CommandPalette({ open, onOpenChange, onAction }) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  useEffect(() => {
    if (!open) setSearch("");
  }, [open]);
  const handleSelect = (id) => {
    const nav = NAV_ITEMS.find((n) => n.id === id);
    if (nav) {
      router.push(nav.action);
      onOpenChange(false);
      return;
    }
    const act = ACTIONS.find((a) => a.id === id);
    if (act) {
      onAction?.(act.action);
      onOpenChange(false);
      return;
    }
  };
  return /* @__PURE__ */ jsx(Dialog, { open, onOpenChange, children: /* @__PURE__ */ jsxs(DialogContent, { className: "max-w-xl p-0 overflow-hidden", children: [
    /* @__PURE__ */ jsx(DialogTitle, { className: "sr-only", children: "Command palette" }),
    /* @__PURE__ */ jsxs(Command, { label: "Command palette", className: "bg-bg-panel", children: [
      /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-2 border-b border-border px-4 py-3", children: [
        /* @__PURE__ */ jsx(Search, { size: 16, className: "text-muted" }),
        /* @__PURE__ */ jsx(
          Command.Input,
          {
            value: search,
            onValueChange: setSearch,
            placeholder: "Type a command or search\u2026",
            className: "flex-1 bg-transparent text-sm text-zinc-100 placeholder:text-muted focus:outline-none"
          }
        ),
        /* @__PURE__ */ jsx("kbd", { className: "rounded border border-border bg-bg-card px-1.5 py-0.5 text-[10px] text-muted", children: "ESC" })
      ] }),
      /* @__PURE__ */ jsxs(Command.List, { className: "max-h-80 overflow-y-auto p-2", children: [
        /* @__PURE__ */ jsx(Command.Empty, { className: "px-3 py-6 text-center text-sm text-muted", children: "No results found." }),
        /* @__PURE__ */ jsx(Command.Group, { heading: "Navigate", className: "text-xs uppercase tracking-wide text-muted", children: NAV_ITEMS.map((item) => /* @__PURE__ */ jsxs(
          Command.Item,
          {
            value: item.label,
            onSelect: () => handleSelect(item.id),
            className: "flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm text-zinc-200 aria-selected:bg-accent/15 aria-selected:text-accent-light",
            children: [
              /* @__PURE__ */ jsx(item.icon, { size: 16 }),
              /* @__PURE__ */ jsx("span", { children: item.label })
            ]
          },
          item.id
        )) }),
        /* @__PURE__ */ jsx(Command.Separator, { className: "my-2 h-px bg-border" }),
        /* @__PURE__ */ jsx(Command.Group, { heading: "Actions", className: "text-xs uppercase tracking-wide text-muted", children: ACTIONS.map((item) => /* @__PURE__ */ jsxs(
          Command.Item,
          {
            value: item.label,
            onSelect: () => handleSelect(item.id),
            className: "flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm text-zinc-200 aria-selected:bg-accent/15 aria-selected:text-accent-light",
            children: [
              /* @__PURE__ */ jsx(item.icon, { size: 16 }),
              /* @__PURE__ */ jsx("span", { children: item.label })
            ]
          },
          item.id
        )) })
      ] }),
      /* @__PURE__ */ jsxs("div", { className: "flex items-center justify-between border-t border-border bg-bg-card/50 px-4 py-2 text-[10px] text-muted", children: [
        /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-3", children: [
          /* @__PURE__ */ jsxs("span", { children: [
            /* @__PURE__ */ jsx("kbd", { className: "rounded border border-border bg-bg-card px-1", children: "\u2191\u2193" }),
            " navigate"
          ] }),
          /* @__PURE__ */ jsxs("span", { children: [
            /* @__PURE__ */ jsx("kbd", { className: "rounded border border-border bg-bg-card px-1", children: "\u21B5" }),
            " select"
          ] })
        ] }),
        /* @__PURE__ */ jsx("span", { children: "Powered by cmdk" })
      ] })
    ] })
  ] }) });
}
export {
  CommandPalette
};
