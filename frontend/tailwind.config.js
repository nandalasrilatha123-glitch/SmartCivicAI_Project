/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F3F4EF",
        "paper-raised": "#FBFBF8",
        ink: {
          DEFAULT: "#1B2A4A",
          soft: "#3E4C6B",
          faint: "#7C86A0",
        },
        marigold: {
          DEFAULT: "#E8A33D",
          dark: "#C4832A",
        },
        stamp: {
          red: "#B23A2E",
          teal: "#2F6F62",
        },
        module: {
          schools: "#2F5FA8",
          agriculture: "#3F7D3B",
          healthcare: "#B23A2E",
          traffic: "#C97A1E",
        },
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: [
          "Noto Sans",
          "Noto Sans Telugu",
          "Noto Sans Devanagari",
          "system-ui",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        none: "0px",
        sm: "2px",
        DEFAULT: "3px",
        md: "4px",
      },
    },
  },
  plugins: [],
};
