/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        sonar: {
          abyss: "#04111c",
          deep: "#0a1f33",
          mid: "#0f2f4f",
          highlight: "#3b82f6",
          cyan: "#22d3ee",
          warn: "#f59e0b",
          danger: "#ef4444",
          ok: "#22c55e",
          review: "#a855f7",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        sonar: "0 4px 30px -10px rgba(34, 211, 238, 0.18)",
      },
      animation: {
        "sonar-sweep": "sonar-sweep 4s ease-in-out infinite",
        "pulse-slow": "pulse 6s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        "sonar-sweep": {
          "0%": { transform: "translateX(-100%)", opacity: "0.2" },
          "50%": { transform: "translateX(0%)", opacity: "0.5" },
          "100%": { transform: "translateX(100%)", opacity: "0.2" },
        },
      },
    },
  },
  plugins: [],
};