"use client";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { jsx, jsxs } from "react/jsx-runtime";
const FOCUSABLE_SELECTOR = 'a[href],button:not([disabled]),textarea:not([disabled]),input:not([disabled]),select:not([disabled]),[tabindex]:not([tabindex="-1"])';
function Dialog({ open, onOpenChange, children }) {
  const containerRef = useRef(null);
  const previousActiveRef = useRef(null);
  const reduceMotion = useReducedMotion();
  useEffect(() => {
    if (!open) return;
    previousActiveRef.current = document.activeElement ?? null;
    const onKey = (e) => {
      if (e.key === "Escape") {
        onOpenChange(false);
        return;
      }
      if (e.key !== "Tab" || !containerRef.current) return;
      const focusables2 = Array.from(
        containerRef.current.querySelectorAll(FOCUSABLE_SELECTOR)
      ).filter((el) => !el.hasAttribute("aria-hidden"));
      if (focusables2.length === 0) {
        e.preventDefault();
        return;
      }
      const first = focusables2[0];
      const last = focusables2[focusables2.length - 1];
      const active = document.activeElement;
      if (e.shiftKey && (active === first || !containerRef.current.contains(active))) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    const focusables = containerRef.current?.querySelectorAll(FOCUSABLE_SELECTOR);
    const initial = focusables ? Array.from(focusables).find((el) => !el.hasAttribute("aria-hidden")) : null;
    initial?.focus();
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
      previousActiveRef.current?.focus?.();
    };
  }, [open, onOpenChange]);
  const motionProps = reduceMotion ? { initial: false, animate: void 0, exit: void 0, transition: { duration: 0 } } : {};
  return /* @__PURE__ */ jsx(AnimatePresence, { children: open && /* @__PURE__ */ jsx(
    motion.div,
    {
      role: "dialog",
      "aria-modal": "true",
      ref: containerRef,
      initial: reduceMotion ? false : { opacity: 0 },
      animate: { opacity: 1 },
      exit: reduceMotion ? void 0 : { opacity: 0 },
      transition: { duration: 0.15 },
      className: "fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 pt-[12vh] backdrop-blur-sm",
      onClick: () => onOpenChange(false),
      children: /* @__PURE__ */ jsx(
        motion.div,
        {
          initial: reduceMotion ? false : { opacity: 0, y: -20, scale: 0.96 },
          animate: reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 },
          exit: reduceMotion ? void 0 : { opacity: 0, y: -20, scale: 0.96 },
          transition: { type: "spring", stiffness: 400, damping: 30 },
          onClick: (e) => e.stopPropagation(),
          className: "w-full",
          ...motionProps,
          children
        }
      )
    }
  ) });
}
function DialogContent({ children, className, onClose }) {
  return /* @__PURE__ */ jsxs(
    "div",
    {
      className: cn(
        "rounded-xl border border-border bg-bg-panel shadow-2xl",
        className
      ),
      children: [
        onClose && /* @__PURE__ */ jsx(
          "button",
          {
            onClick: onClose,
            className: "absolute right-3 top-3 z-10 rounded p-1 text-muted hover:bg-bg-card hover:text-zinc-200",
            "aria-label": "Close",
            children: /* @__PURE__ */ jsx(X, { size: 16 })
          }
        ),
        children
      ]
    }
  );
}
function DialogTitle({ children, className }) {
  return /* @__PURE__ */ jsx("h2", { className: cn("text-base font-semibold text-zinc-100", className), children });
}
export {
  Dialog,
  DialogContent,
  DialogTitle
};
