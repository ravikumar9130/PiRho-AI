import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cyberpunk Neon Cyan - Primary brand color
        neon: {
          50: "#ecfeff",
          100: "#cffafe",
          200: "#a5f3fc",
          300: "#67e8f9",
          400: "#22d3ee",
          500: "#00FFFF", // Pure cyan
          600: "#0891b2",
          700: "#0e7490",
          800: "#155e75",
          900: "#164e63",
          950: "#083344",
        },
        // Electric Magenta - Secondary accent
        magenta: {
          50: "#fdf4ff",
          100: "#fae8ff",
          200: "#f5d0fe",
          300: "#f0abfc",
          400: "#e879f9",
          500: "#FF00FF", // Pure magenta
          600: "#c026d3",
          700: "#a21caf",
          800: "#86198f",
          900: "#701a75",
          950: "#4a044e",
        },
        // Electric Blue
        electric: {
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
        },
        // Neon Purple
        purple: {
          400: "#c084fc",
          500: "#a855f7",
          600: "#9333ea",
        },
        // Hot Pink
        hotpink: {
          400: "#fb7185",
          500: "#f43f5e",
          600: "#e11d48",
        },
        // Deep black surfaces for cyberpunk feel
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#1e293b",
          800: "#0f172a",
          850: "#0c1222",
          900: "#080d19",
          925: "#060a14",
          950: "#030712",
          black: "#010204",
        },
        // Keep brand for backwards compatibility but map to neon
        brand: {
          50: "#ecfeff",
          100: "#cffafe",
          200: "#a5f3fc",
          300: "#67e8f9",
          400: "#22d3ee",
          500: "#00d4ff",
          600: "#0891b2",
          700: "#0e7490",
          800: "#155e75",
          900: "#164e63",
          950: "#083344",
        },
        accent: {
          gold: "#fbbf24",
          amber: "#f59e0b",
          cyan: "#00FFFF",
          magenta: "#FF00FF",
          purple: "#a855f7",
          pink: "#f43f5e",
        },
      },
      fontFamily: {
        sans: ["var(--font-space-grotesk)", "system-ui", "sans-serif"],
        display: ["var(--font-orbitron)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "fade-up": "fadeUp 0.5s ease-out forwards",
        "slide-up": "slideUp 0.3s ease-out forwards",
        "slide-in-left": "slideInLeft 0.3s ease-out forwards",
        "slide-in-right": "slideInRight 0.3s ease-out forwards",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "pulse-neon": "pulseNeon 2s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
        "spin-slow": "spin 3s linear infinite",
        float: "float 6s ease-in-out infinite",
        "scale-in": "scaleIn 0.2s ease-out forwards",
        "bounce-subtle": "bounceSubtle 2s ease-in-out infinite",
        "glow-pulse": "glowPulse 2s ease-in-out infinite",
        "border-glow": "borderGlow 3s ease-in-out infinite",
        "glitch": "glitch 1s linear infinite",
        "glitch-1": "glitch1 0.3s linear infinite",
        "glitch-2": "glitch2 0.3s linear infinite",
        "scanline": "scanline 8s linear infinite",
        "grid-flow": "gridFlow 20s linear infinite",
        "flicker": "flicker 0.15s infinite",
        "text-glow": "textGlow 2s ease-in-out infinite alternate",
        "float-slow": "floatSlow 8s ease-in-out infinite",
        "rotate-slow": "rotateSlow 20s linear infinite",
        "cyber-pulse": "cyberPulse 1.5s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        slideInLeft: {
          "0%": { transform: "translateX(-100%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        slideInRight: {
          "0%": { transform: "translateX(100%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(0, 255, 255, 0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(0, 255, 255, 0.6)" },
        },
        pulseNeon: {
          "0%, 100%": { 
            boxShadow: "0 0 5px #00FFFF, 0 0 10px #00FFFF, 0 0 20px #00FFFF",
            borderColor: "rgba(0, 255, 255, 0.8)",
          },
          "50%": { 
            boxShadow: "0 0 10px #00FFFF, 0 0 20px #00FFFF, 0 0 40px #00FFFF, 0 0 80px #00FFFF",
            borderColor: "rgba(0, 255, 255, 1)",
          },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        floatSlow: {
          "0%, 100%": { transform: "translateY(0) rotate(0deg)" },
          "50%": { transform: "translateY(-20px) rotate(2deg)" },
        },
        scaleIn: {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        bounceSubtle: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-5px)" },
        },
        glowPulse: {
          "0%, 100%": { 
            filter: "drop-shadow(0 0 2px #00FFFF) drop-shadow(0 0 5px #00FFFF)",
          },
          "50%": { 
            filter: "drop-shadow(0 0 5px #00FFFF) drop-shadow(0 0 15px #00FFFF) drop-shadow(0 0 30px #00FFFF)",
          },
        },
        borderGlow: {
          "0%, 100%": { 
            borderColor: "rgba(0, 255, 255, 0.5)",
            boxShadow: "0 0 10px rgba(0, 255, 255, 0.3), inset 0 0 10px rgba(0, 255, 255, 0.1)",
          },
          "50%": { 
            borderColor: "rgba(255, 0, 255, 0.5)",
            boxShadow: "0 0 20px rgba(255, 0, 255, 0.4), inset 0 0 15px rgba(255, 0, 255, 0.1)",
          },
        },
        glitch: {
          "0%": { transform: "translate(0)" },
          "20%": { transform: "translate(-2px, 2px)" },
          "40%": { transform: "translate(-2px, -2px)" },
          "60%": { transform: "translate(2px, 2px)" },
          "80%": { transform: "translate(2px, -2px)" },
          "100%": { transform: "translate(0)" },
        },
        glitch1: {
          "0%": { clipPath: "inset(40% 0 61% 0)" },
          "20%": { clipPath: "inset(92% 0 1% 0)" },
          "40%": { clipPath: "inset(43% 0 1% 0)" },
          "60%": { clipPath: "inset(25% 0 58% 0)" },
          "80%": { clipPath: "inset(54% 0 7% 0)" },
          "100%": { clipPath: "inset(58% 0 43% 0)" },
        },
        glitch2: {
          "0%": { clipPath: "inset(65% 0 14% 0)" },
          "20%": { clipPath: "inset(79% 0 15% 0)" },
          "40%": { clipPath: "inset(41% 0 34% 0)" },
          "60%": { clipPath: "inset(14% 0 72% 0)" },
          "80%": { clipPath: "inset(2% 0 90% 0)" },
          "100%": { clipPath: "inset(31% 0 43% 0)" },
        },
        scanline: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        gridFlow: {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "0 100px" },
        },
        flicker: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.8" },
        },
        textGlow: {
          "0%": { 
            textShadow: "0 0 5px #00FFFF, 0 0 10px #00FFFF, 0 0 20px #00FFFF",
          },
          "100%": { 
            textShadow: "0 0 10px #FF00FF, 0 0 20px #FF00FF, 0 0 40px #FF00FF",
          },
        },
        rotateSlow: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        cyberPulse: {
          "0%, 100%": { 
            transform: "scale(1)",
            opacity: "1",
          },
          "50%": { 
            transform: "scale(1.05)",
            opacity: "0.8",
          },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
      boxShadow: {
        glow: "0 0 20px rgba(0, 255, 255, 0.3)",
        "glow-lg": "0 0 40px rgba(0, 255, 255, 0.4)",
        "glow-xl": "0 0 60px rgba(0, 255, 255, 0.5)",
        "inner-glow": "inset 0 0 20px rgba(0, 255, 255, 0.1)",
        "neon-cyan": "0 0 5px #00FFFF, 0 0 10px #00FFFF, 0 0 20px #00FFFF, 0 0 40px #00FFFF",
        "neon-magenta": "0 0 5px #FF00FF, 0 0 10px #FF00FF, 0 0 20px #FF00FF, 0 0 40px #FF00FF",
        "neon-dual": "0 0 10px #00FFFF, 0 0 20px #FF00FF, 0 0 40px #00FFFF",
        "cyber-card": "0 0 0 1px rgba(0, 255, 255, 0.1), 0 4px 30px rgba(0, 0, 0, 0.5), inset 0 0 30px rgba(0, 255, 255, 0.05)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "cyber-gradient": "linear-gradient(135deg, #00FFFF 0%, #FF00FF 50%, #00FFFF 100%)",
        "neon-gradient": "linear-gradient(90deg, #00FFFF 0%, #a855f7 50%, #FF00FF 100%)",
        "dark-gradient": "linear-gradient(180deg, #080d19 0%, #030712 100%)",
        "grid-cyber": `
          linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0, 255, 255, 0.03) 1px, transparent 1px)
        `,
      },
    },
  },
  plugins: [],
};

export default config;
