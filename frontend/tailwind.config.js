/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12151a",
        paper: "#f6f5f2",
        brand: {
          50: "#eef5ff",
          100: "#d9e8ff",
          300: "#8fb8ff",
          500: "#3b6fd6",
          600: "#2c57ad",
          700: "#22458a",
        },
        urgent: {
          red: "#c1443c",
          orange: "#c98a2e",
          green: "#2f8a5b",
        },
      },
      fontFamily: {
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(18,21,26,0.06), 0 8px 24px -12px rgba(18,21,26,0.15)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
    },
  },
  plugins: [],
};
