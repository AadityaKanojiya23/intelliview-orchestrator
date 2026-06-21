"use client";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect, useRef, type ReactNode, type MouseEvent } from "react";
import { cn } from "@/lib/utils";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
}

const FOCUSABLE_SELECTOR =
  'a[href],button:not([disabled]),textarea:not([disabled]),input:not([disabled]),select:not([disabled]),[tabindex]:not([tabindex="-1"])';

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const previousActiveRef = useRef<HTMLElement | null>(null);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (!open) return;

    previousActiveRef.current = (document.activeElement as HTMLElement) ?? null;

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onOpenChange(false);
        return;
      }
      if (e.key !== "Tab" || !containerRef.current) return;
      const focusables = Array.from(
        containerRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
      ).filter((el) => !el.hasAttribute("aria-hidden"));
      if (focusables.length === 0) {
        e.preventDefault();
        return;
      }
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement as HTMLElement | null;
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

    // Move focus into the dialog.
    const focusables = containerRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
    const initial = focusables ? Array.from(focusables).find((el) => !el.hasAttribute("aria-hidden")) : null;
    initial?.focus();

    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
      previousActiveRef.current?.focus?.();
    };
  }, [open, onOpenChange]);

  const motionProps = reduceMotion
    ? { initial: false, animate: undefined, exit: undefined, transition: { duration: 0 } }
    : {};

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          role="dialog"
          aria-modal="true"
          ref={containerRef}
          initial={reduceMotion ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={reduceMotion ? undefined : { opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 pt-[12vh] backdrop-blur-sm"
          onClick={() => onOpenChange(false)}
        >
          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: -20, scale: 0.96 }}
            animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
            exit={reduceMotion ? undefined : { opacity: 0, y: -20, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
            onClick={(e: MouseEvent<HTMLDivElement>) => e.stopPropagation()}
            className="w-full"
            {...motionProps}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

interface DialogContentProps {
  children: ReactNode;
  className?: string;
  onClose?: () => void;
}

export function DialogContent({ children, className, onClose }: DialogContentProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-bg-panel shadow-2xl",
        className
      )}
    >
      {onClose && (
        <button
          onClick={onClose}
          className="absolute right-3 top-3 z-10 rounded p-1 text-muted hover:bg-bg-card hover:text-zinc-200"
          aria-label="Close"
        >
          <X size={16} />
        </button>
      )}
      {children}
    </div>
  );
}

export function DialogTitle({ children, className }: { children: ReactNode; className?: string }) {
  return <h2 className={cn("text-base font-semibold text-zinc-100", className)}>{children}</h2>;
}
