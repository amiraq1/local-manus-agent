import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'IBM Plex Sans'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      colors: {
        primary: {
          DEFAULT: "#00E5A0",
          50: "#E6FFF6",
          100: "#B3FFE6",
          200: "#66FFCC",
          300: "#33FFB8",
          400: "#1AFFB0",
          500: "#00E5A0",
          600: "#00B87E",
          700: "#008A5E",
          800: "#005C3E",
          900: "#002E1F",
        },
        accent: "#FF6B6B",
        dark: {
          50: "#F0F4F8",
          100: "#E1E7EF",
          200: "#C9D1DB",
          300: "#A0AEC0",
          400: "#718096",
          500: "#4A5568",
          600: "#2D3748",
          700: "#1F2A3C",
          800: "#162032",
          900: "#0F1729",
          950: "#080D19",
        },
      },
      keyframes: {
        "slide-in": {
          "0%": { opacity: "0", transform: "translateX(24px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 8px rgba(0,229,160,0.15)" },
          "50%": { boxShadow: "0 0 20px rgba(0,229,160,0.3)" },
        },
      },
      animation: {
        "slide-in": "slide-in 0.3s ease-out",
        "scale-in": "scale-in 0.2s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        shimmer: "shimmer 2s infinite linear",
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
