import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Courier New"', 'monospace'],
      },
      colors: {
        accent: {
          DEFAULT: '#e07810',
          bright: '#f59332',
          dim: 'rgba(224,120,16,0.3)',
          bg: 'rgba(224,120,16,0.07)',
        },
        surface: {
          base: '#0d0d0d',
          panel: '#111111',
          DEFAULT: '#181818',
          elevated: '#1e1e1e',
          hover: '#242424',
        },
        border: {
          faint: '#181818',
          subtle: '#222222',
          DEFAULT: '#2c2c2c',
          strong: '#3a3a3a',
        },
      },
    },
  },
  plugins: [],
};

export default config;
