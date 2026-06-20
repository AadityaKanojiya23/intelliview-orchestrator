"use client";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect, type ReactNode, type MouseEvent } from "react";
import { cn } from "@/lib/utils";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onOpenChange]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 pt-[12vh] backdrop-blur-sm"
          onClick={() => onOpenChange(false)}
        >
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
            onClick={(e: MouseEvent<HTMLDivElement>) => e.stopPropagation()}
            className="w-full"
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
