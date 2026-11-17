/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#1B2A2F',
        muted: '#4A5A60',
        paper: '#F6F2EA',
        surface: '#FFFFFF',
        line: '#D5CFC0',
        primary: {
          DEFAULT: '#0B5D5B',
          ink: '#FFFFFF',
          soft: '#E0EFEE',
        },
        info: {
          bg: '#E2EEF1',
          ink: '#0E4A5C',
        },
        warn: {
          bg: '#FFF0C7',
          ink: '#5B3A00',
        },
        ok: {
          bg: '#DDF1E4',
          ink: '#0C5A30',
        },
      },
      spacing: {
        s1: '4px',
        s2: '8px',
        s3: '12px',
        s4: '16px',
        s5: '24px',
        s6: '32px',
      },
      fontFamily: {
        body: ['"Public Sans"', '"Segoe UI"', 'system-ui', 'sans-serif'],
        head: ['"Source Serif 4"', 'Georgia', '"Times New Roman"', 'serif'],
      },
      borderRadius: {
        'badge': '12px',
        'card': '12px',
        'button': '24px',
        'chip': '16px',
        'field': '8px',
        'tag': '10px',
      },
    },
  },
  plugins: [],
};
