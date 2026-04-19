import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: "#15191f",
        mist: "#f5f7fb",
        pine: "#0f766e",
        coral: "#e85d3f",
        gold: "#f5b642",
      },
      boxShadow: {
        soft: "0 12px 34px rgba(21, 25, 31, 0.10)",
      },
    },
  },
  plugins: [],
};

export default config;
