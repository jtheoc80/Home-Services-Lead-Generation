import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f1f6ff",
          100: "#e3eeff",
          200: "#c6daff",
          300: "#9fbfff",
          400: "#6e9aff",
          500: "#3d74ff",   // primary
          600: "#2a57db",
          700: "#1e40b5",
          800: "#183591",
          900: "#152d78"
        },
        texas: {
          50: "#fef7ee",
          100: "#fdedd3",
          200: "#fbd7a5",
          300: "#f8bb6d",
          400: "#f59532",
          500: "#f2760b",
          600: "#e35c05",
          700: "#bc4507",
          800: "#96360e",
          900: "#792e0f"
        },
        success: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b"
        },
        warning: {
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
          800: "#92400e",
          900: "#78350f"
        },
        danger: {
          50: "#fef2f2",
          100: "#fee2e2",
          200: "#fecaca",
          300: "#fca5a5",
          400: "#f87171",
          500: "#ef4444",
          600: "#dc2626",
          700: "#b91c1c",
          800: "#991b1b",
          900: "#7f1d1d"
        }
      },
      boxShadow: {
        soft: "0 2px 10px rgba(10, 20, 50, 0.08)",
        "soft-lg": "0 4px 20px rgba(10, 20, 50, 0.12)",
        "soft-xl": "0 8px 40px rgba(10, 20, 50, 0.16)",
        glow: "0 0 20px rgba(61, 116, 255, 0.3)",
        "texas-glow": "0 0 20px rgba(242, 118, 11, 0.3)"
      },
      borderRadius: {
        xl: "14px",
        "2xl": "18px",
        "3xl": "24px"
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'texas-gradient': 'linear-gradient(135deg, #f59e0b 0%, #f97316 50%, #dc2626 100%)',
        'score-gradient': 'linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%)'
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-soft': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-gentle': 'bounce 2s infinite',
        'scale-in': 'scale-in 0.2s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out'
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' }
        },
        'scale-in': {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' }
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        }
      }
    }
  },
  plugins: []
} satisfies Config;