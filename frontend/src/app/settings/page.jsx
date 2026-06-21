"use client";
import { useState } from "react";
import useSWR from "swr";
import Card from "@/components/Card";
import { Skeleton, ErrorState } from "@/components/States";
import { endpoints } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { useThemeStore } from "@/lib/theme";
import { toast } from "@/lib/toast";
import { Moon, Sun, Monitor } from "lucide-react";
import { jsx, jsxs } from "react/jsx-runtime";
function SettingsPage() {
  const { token, setToken } = useAppStore();
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);
  const [draft, setDraft] = useState("");
  const [switching, setSwitching] = useState(null);
  const [detecting, setDetecting] = useState(false);
  const scheduling = useSWR("/scheduling-status", { refreshInterval: 5e3 });
  return /* @__PURE__ */ jsxs("div", { className: "space-y-6 animate-fade-in", children: [
    /* @__PURE__ */ jsxs("div", { children: [
      /* @__PURE__ */ jsx("h1", { className: "text-2xl font-semibold text-zinc-50", children: "Settings" }),
      /* @__PURE__ */ jsx("p", { className: "text-sm text-muted", children: "API credentials, theme, and runtime controls." })
    ] }),
    /* @__PURE__ */ jsx(Card, { title: "API token", description: "Required for worker management and protected endpoints.", children: /* @__PURE__ */ jsxs(
      "form",
      {
        onSubmit: (e) => {
          e.preventDefault();
          setToken(draft.trim() || null);
          toast.success("API token updated");
        },
        className: "flex items-center gap-2",
        children: [
          /* @__PURE__ */ jsx(
            "input",
            {
              type: "password",
              value: draft || token || "",
              onChange: (e) => setDraft(e.target.value),
              placeholder: "paste API_TOKEN",
              className: "flex-1 rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-zinc-100 placeholder:text-muted focus:border-accent focus:outline-none"
            }
          ),
          /* @__PURE__ */ jsx("button", { type: "submit", className: "rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-dark", children: "Save" }),
          token && /* @__PURE__ */ jsx(
            "button",
            {
              type: "button",
              onClick: () => {
                setToken(null);
                setDraft("");
                toast.info("Signed out");
              },
              className: "rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-zinc-300 hover:bg-bg-panel",
              children: "Clear"
            }
          )
        ]
      }
    ) }),
    /* @__PURE__ */ jsx(Card, { title: "Appearance", description: "Choose how the dashboard looks.", children: /* @__PURE__ */ jsx("div", { className: "flex flex-wrap items-center gap-2", children: [
      { v: "dark", label: "Dark", icon: Moon },
      { v: "light", label: "Light", icon: Sun },
      { v: "system", label: "System", icon: Monitor }
    ].map((opt) => /* @__PURE__ */ jsxs(
      "button",
      {
        onClick: () => {
          setTheme(opt.v);
          toast.info(`Theme: ${opt.label}`);
        },
        className: "flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium " + (theme === opt.v ? "border-accent bg-accent/15 text-accent-light" : "border-border bg-bg-card text-zinc-300 hover:border-accent/40"),
        children: [
          /* @__PURE__ */ jsx(opt.icon, { size: 14 }),
          " ",
          opt.label
        ]
      },
      opt.v
    )) }) }),
    /* @__PURE__ */ jsx(Card, { title: "Load balancing", description: "Switch the active strategy at runtime.", children: scheduling.error ? /* @__PURE__ */ jsx(ErrorState, { error: scheduling.error, onRetry: () => scheduling.mutate() }) : !scheduling.data ? /* @__PURE__ */ jsx(Skeleton, { className: "h-20 w-full" }) : /* @__PURE__ */ jsx("div", { className: "flex flex-wrap items-center gap-2", children: ["ROUND_ROBIN", "LEAST_LOADED", "QUEUE_BASED"].map((s) => /* @__PURE__ */ jsxs(
      "button",
      {
        disabled: switching !== null,
        onClick: async () => {
          setSwitching(s);
          try {
            await endpoints.switchStrategy(s);
            await scheduling.mutate();
            toast.success("Strategy switched", s);
          } catch (e) {
            toast.error("Failed to switch", e instanceof Error ? e.message : String(e));
          } finally {
            setSwitching(null);
          }
        },
        className: "rounded-md border px-3 py-1.5 text-xs font-medium " + (scheduling.data.current_strategy === s ? "border-accent bg-accent/15 text-accent-light" : "border-border bg-bg-card text-zinc-300 hover:border-accent/40"),
        children: [
          s,
          " ",
          switching === s ? "\u2026" : ""
        ]
      },
      s
    )) }) }),
    /* @__PURE__ */ jsx(Card, { title: "Failure detection", description: "Manually trigger detection + recovery for stuck sessions and failed workers.", children: /* @__PURE__ */ jsx(
      "button",
      {
        disabled: detecting,
        onClick: async () => {
          setDetecting(true);
          try {
            const r = await endpoints.detectFailures();
            toast.success(
              "Detection complete",
              `${r.failed_sessions_detected} failed \xB7 ${r.unhealthy_workers_detected} unhealthy \xB7 ${r.stuck_sessions_detected} stuck`
            );
          } catch (e) {
            toast.error("Detection failed", e instanceof Error ? e.message : String(e));
          } finally {
            setDetecting(false);
          }
        },
        className: "rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-dark disabled:opacity-50",
        children: detecting ? "Scanning\u2026" : "Run detection"
      }
    ) })
  ] });
}
export {
  SettingsPage as default
};
