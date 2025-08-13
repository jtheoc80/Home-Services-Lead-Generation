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
        }
      },
      boxShadow: {
        soft: "0 2px 10px rgba(10, 20, 50, 0.08)"
      },
      borderRadius: {
        xl: "14px"
      }
    }
  },
  plugins: []
} satisfies Config;