import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx,jsx,js}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Tie your system layouts to our changing CSS root variables
        bg: { 
          DEFAULT: "var(--bg-main)", 
          panel: "var(--bg-panel)", 
          card: "var(--bg-card)" 
        },
        accent: { DEFAULT: "#6366f1", light: "#818cf8", dark: "#4f46e5" },
        success: "#10b981",
        warn: "#f59e0b",
        danger: "#ef4444",
        muted: "var(--text-muted)",
        border: "var(--border-color)",
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