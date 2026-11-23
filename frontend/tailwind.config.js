/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#006341',
          50: '#e6f2ed',
          100: '#cce5db',
          200: '#99cbb7',
          300: '#66b193',
          400: '#33976f',
          500: '#006341',
          600: '#005034',
          700: '#003c27',
          800: '#00281a',
          900: '#00140d',
        },
        secondary: {
          DEFAULT: '#d8333e',
          50: '#fce8ea',
          100: '#f9d1d5',
          200: '#f3a3ab',
          300: '#ed7581',
          400: '#e74757',
          500: '#d8333e',
          600: '#ad2932',
          700: '#821f25',
          800: '#561419',
          900: '#2b0a0c',
        },
      },
    },
  },
  plugins: [],
};
