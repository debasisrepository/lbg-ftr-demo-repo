/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1a3672',
          light: '#e1edff',
          dark: '#0d1b36',
        },
        secondary: {
          DEFAULT: '#00a86b',
          light: '#e6f7f1',
        },
        accent: '#ff6b35',
        background: '#ffffff',
        surface: '#f5f7fa',
        border: '#e0e4e8',
        text: {
          primary: '#1f2937',
          secondary: '#6b7280',
          muted: '#9ca3af',
        },
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#3b82f6',
      },
    },
  },
  plugins: [],
}
