import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx,jsx,js}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: "#0a0a0f", panel: "#12121a", card: "#1a1a24" },
        accent: { DEFAULT: "#6366f1", light: "#818cf8", dark: "#4f46e5" },
        success: "#10b981",
        warn: "#f59e0b",
        danger: "#ef4444",
        muted: "#71717a",
        border: "#27272a",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
