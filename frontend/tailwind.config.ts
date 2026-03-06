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
        // Primary - Deep Navy
        navy: {
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
        },
        // Accent - Electric Teal
        teal: {
          500: '#14b8a6',
          400: '#2dd4bf',
          300: '#5eead4',
        },
        // Secondary - Warm Coral
        coral: {
          500: '#f97316',
          400: '#fb923c',
        },
        // Neutrals
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          600: '#475569',
          700: '#334155',
          900: '#0f172a',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'display-lg': ['64px', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '800' }],
        'display-md': ['48px', { lineHeight: '1.15', letterSpacing: '-0.02em', fontWeight: '800' }],
        'heading-xl': ['40px', { lineHeight: '1.2', letterSpacing: '-0.015em', fontWeight: '700' }],
        'heading-lg': ['32px', { lineHeight: '1.25', letterSpacing: '-0.015em', fontWeight: '700' }],
        'heading-md': ['24px', { lineHeight: '1.3', letterSpacing: '-0.01em', fontWeight: '600' }],
        'heading-sm': ['20px', { lineHeight: '1.35', letterSpacing: '-0.01em', fontWeight: '600' }],
        'body-lg': ['18px', { lineHeight: '1.5' }],
        'body-md': ['16px', { lineHeight: '1.5' }],
        'body-sm': ['14px', { lineHeight: '1.5', letterSpacing: '0.01em' }],
        'caption': ['12px', { lineHeight: '1.5', letterSpacing: '0.02em', fontWeight: '500' }],
      },
      borderRadius: {
        'sm': '6px',
        'md': '10px',
        'lg': '14px',
        'xl': '20px',
        '2xl': '28px',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, rgba(148, 163, 184, 0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(148, 163, 184, 0.08) 1px, transparent 1px)",
      },
      backgroundSize: {
        'grid': '32px 32px',
      },
    },
  },
  plugins: [],
};

export default config;
