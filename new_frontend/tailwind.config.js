/** @type {import('tailwindcss').Config} */
export default {
  content: [
  './index.html',
  './**/*.{js,jsx}',        // all JSX in root and subfolders
  '!./node_modules/**',     // exclude node_modules
],
  theme: {
    extend: {
      fontFamily: {
        display: ['"DM Sans"', 'sans-serif'],
        body:    ['"DM Sans"', 'sans-serif'],
        mono:    ['"DM Mono"', 'monospace'],
      },
      colors: {
        ink: {
          DEFAULT: '#0F172A',
          300:     '#94A3B8',
          400:     '#64748B',
          700:     '#1E293B',
        },
        slate: {
          DEFAULT:  '#F8FAFC',
          soft:     '#F1F5F9',
          border:   '#E2E8F0',
        },
        blue: {
          DEFAULT: '#2563EB',
          light:   '#EFF6FF',
          border:  '#BFDBFE',
          dark:    '#1D4ED8',
        },
        amber: {
          DEFAULT: '#D97706',
          light:   '#FFFBEB',
        },
        rust: {
          DEFAULT: '#DC2626',
          light:   '#FEF2F2',
        },
      },
      borderRadius: {
        DEFAULT: '6px',
        lg:      '10px',
        xl:      '14px',
      },
      boxShadow: {
        card:   '0 1px 3px 0 rgb(0 0 0 / 0.07), 0 1px 2px -1px rgb(0 0 0 / 0.07)',
        modal:  '0 20px 60px -10px rgb(0 0 0 / 0.18)',
      },
    },
  },
  plugins: [],
}
