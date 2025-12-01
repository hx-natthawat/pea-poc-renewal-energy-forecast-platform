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
        // PEA Brand Colors
        pea: {
          primary: "#1e40af", // Blue
          secondary: "#059669", // Green (renewable energy)
          accent: "#f59e0b", // Amber (solar)
          dark: "#1e293b",
          light: "#f8fafc",
        },
      },
    },
  },
  plugins: [],
};

export default config;
