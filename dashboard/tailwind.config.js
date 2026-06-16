/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        /* dashboard (dark) */
        surface: "#111827",
        panel: "#1F2937",
        border: "#374151",
        muted: "#6B7280",
        accent: "#6366F1",
        danger: "#EF4444",
        warning: "#F59E0B",
        success: "#10B981",
        /* landing page (warm) */
        cream: "#FAFAF6",
        sand: "#F2F0E8",
        charcoal: "#1A1A1A",
        warm: {
          50: "#FFF9EB",
          100: "#FFF0C6",
          200: "#FFE08A",
          300: "#FFCB47",
          400: "#F5B520",
          500: "#E8A000",
          600: "#CC7A00",
          700: "#A35500",
          800: "#864300",
          900: "#6E3600",
        },
        slate: {
          150: "#EAECF0",
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        display: ['"Inter"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
