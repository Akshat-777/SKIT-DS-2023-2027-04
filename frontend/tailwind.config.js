/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    screens: {
      'xs': '375px',      // Mobile wireframe base (375px)
      'sm': '640px',
      'md': '768px',      // Tablet wireframe base (768px)
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1440px',    // Desktop wireframe base (1440px)
      '3xl': '1920px',
    },
    extend: {
      colors: {
        // Brand & Accent Colors
        brand: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1', // Primary Brand Base
          600: '#4F46E5', // Primary Hover
          700: '#4338CA',
          800: '#3730A3',
          900: '#312E81',
          950: '#1E1B4B',
        },
        // CareerLens ATS Score Threshold Ranges
        // Red: 0-49 (Critical gaps) | Amber: 50-74 (Moderate fit) | Green: 75-100 (Recruiter ready)
        ats: {
          red: {
            light: '#FEE2E2', // bg-red-100
            DEFAULT: '#EF4444', // Red (0-49)
            dark: '#991B1B', // text-red-800
            border: '#F87171',
            glow: 'rgba(239, 68, 68, 0.35)',
          },
          amber: {
            light: '#FEF3C7', // bg-amber-100
            DEFAULT: '#F59E0B', // Amber (50-74)
            dark: '#92400E', // text-amber-800
            border: '#FBBF24',
            glow: 'rgba(245, 158, 11, 0.35)',
          },
          green: {
            light: '#D1FAE5', // bg-emerald-100
            DEFAULT: '#10B981', // Green (75-100)
            dark: '#065F46', // text-emerald-800
            border: '#34D399',
            glow: 'rgba(16, 185, 129, 0.35)',
          }
        },
        // Neutral Slate Palette (Optimized for Dark & Light modes)
        slate: {
          850: '#151F32',
          925: '#0B1120',
          950: '#030712',
        },
        // Persona Critique Agent Colors
        agent: {
          recruiter: '#8B5CF6',     // Violet (Senior Tech Recruiter)
          hr: '#EC4899',            // Pink (People Operations / HR Director)
          manager: '#3B82F6',       // Blue (Engineering Hiring Manager)
        },
        // Market Analytics Visuals
        market: {
          lpa: '#0D9488',          // Teal (Salary LPA metrics)
          trending: '#F97316',     // Orange (Trending market skills)
          gap: '#E11D48',          // Rose (Critical skill gaps)
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }],   // 11px
        'xs': ['0.75rem', { lineHeight: '1rem' }],       // 12px
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],   // 14px
        'base': ['1rem', { lineHeight: '1.5rem' }],       // 16px
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],   // 18px
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],    // 20px
        '2xl': ['1.5rem', { lineHeight: '2rem' }],       // 24px
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],  // 30px
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],    // 36px
        '5xl': ['3rem', { lineHeight: '1.16' }],         // 48px
      },
      borderRadius: {
        'sm': '4px',
        'DEFAULT': '6px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '20px',
        '3xl': '24px',
        'full': '9999px',
      },
      boxShadow: {
        'subtle': '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)',
        'card-hover': '0 12px 20px -3px rgba(0, 0, 0, 0.12), 0 4px 6px -4px rgba(0, 0, 0, 0.08)',
        'modal': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        'glow-brand': '0 0 20px -3px rgba(99, 102, 241, 0.35)',
        'glow-green': '0 0 20px -3px rgba(16, 185, 129, 0.35)',
        'glow-amber': '0 0 20px -3px rgba(245, 158, 11, 0.35)',
        'glow-red': '0 0 20px -3px rgba(239, 68, 68, 0.35)',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      animation: {
        'pulse-subtle': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
      }
    },
  },
  plugins: [],
}
