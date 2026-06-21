"use client";
import { cn } from "@/lib/utils";
import { jsx } from "react/jsx-runtime";
function Shimmer({ className }) {
  return /* @__PURE__ */ jsx(
    "div",
    {
      className: cn(
        "relative overflow-hidden rounded-md bg-bg-card",
        "before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.6s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/[0.04] before:to-transparent",
        className
      )
    }
  );
}
if (typeof document !== "undefined" && !document.getElementById("shimmer-keyframes")) {
  const style = document.createElement("style");
  style.id = "shimmer-keyframes";
  style.textContent = "@keyframes shimmer { 100% { transform: translateX(100%); } }";
  document.head.appendChild(style);
}
export {
  Shimmer
};
