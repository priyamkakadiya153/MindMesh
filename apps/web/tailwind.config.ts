import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      screens: {
        'mobile-xs': '375px',
        'mobile-sm': '390px',
        'mobile-md': '412px',
        'mobile-lg': '430px',
        'tiny': '360px',
        'xs': '390px',
        'phone': '430px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        'laptop': '1366px',
        'desktop': '1440px',
        '2xl': '1536px',
        '3xl': '1920px',
      },
      colors: {
        // Semantic Token System
        brand: {
          50: 'var(--brand-50)',
          100: 'var(--brand-100)',
          500: 'var(--brand-500)',
          600: 'var(--brand-600)',
          700: 'var(--brand-700)',
        },
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          light: 'var(--color-primary-light)',
          foreground: 'var(--color-primary-fg)',
        },
        secondary: {
          DEFAULT: 'var(--color-secondary)',
          hover: 'var(--color-secondary-hover)',
          foreground: 'var(--color-secondary-fg)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
          subtle: 'var(--color-accent-subtle)',
          text: 'var(--color-accent-text)',
        },
        surface: {
          DEFAULT: 'var(--color-surface)',
          hover: 'var(--color-surface-hover)',
          card: 'var(--color-surface-card)',
          glass: 'var(--color-surface-glass)',
        },
        bg: {
          base: 'var(--color-bg)',
          subtle: 'var(--color-bg-subtle)',
          elevated: 'var(--color-bg-elevated)',
        },
        border: {
          base: 'var(--color-border)',
          subtle: 'var(--color-border-subtle)',
          hover: 'var(--color-border-hover)',
          focus: 'var(--color-border-focus)',
        },
        txt: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          inverse: 'var(--color-text-inverse)',
        },
        status: {
          success: 'var(--color-success)',
          warning: 'var(--color-warning)',
          error: 'var(--color-error)',
          info: 'var(--color-info)',
        },

        // Legacy compatibility
        bgPrimary: "var(--bg-primary)",
        bgSecondary: "var(--bg-secondary)",
        bgTertiary: "var(--bg-tertiary)",
        bgCard: "var(--bg-card)",
        bgCardHover: "var(--bg-card-hover)",
        bgSidebar: "var(--bg-sidebar)",
        bgHeader: "var(--bg-header)",
        bgDialog: "var(--bg-dialog)",
        bgInput: "var(--bg-input)",
        bgHover: "var(--bg-hover)",
        bgActive: "var(--bg-active)",
        bgOverlay: "var(--bg-overlay)",

        textPrimary: "var(--text-primary)",
        textSecondary: "var(--text-secondary)",
        textMuted: "var(--text-muted)",
        textInverse: "var(--text-inverse)",

        borderColor: "var(--border-color)",
        borderMuted: "var(--border-muted)",
        borderHover: "var(--border-hover)",
        borderFocus: "var(--border-focus)",

        accentHover: "var(--accent-hover)",
        accentSubtle: "var(--accent-subtle)",
        accentText: "var(--accent-text)",

        successBg: "var(--success-bg)",
        successBorder: "var(--success-border)",
        successText: "var(--success-text)",

        warningBg: "var(--warning-bg)",
        warningBorder: "var(--warning-border)",
        warningText: "var(--warning-text)",

        dangerBg: "var(--danger-bg)",
        dangerBorder: "var(--danger-border)",
        dangerText: "var(--danger-text)",

        infoBg: "var(--info-bg)",
        infoBorder: "var(--info-border)",
        infoText: "var(--info-text)",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        display: ["Outfit", "Inter", "sans-serif"],
      },
      borderRadius: {
        'ds-sm': 'var(--radius-sm)',
        'ds-md': 'var(--radius-md)',
        'ds-lg': 'var(--radius-lg)',
        'ds-xl': 'var(--radius-xl)',
        'ds-pill': 'var(--radius-pill)',
      },
      boxShadow: {
        'ds-soft': 'var(--shadow-soft)',
        'ds-medium': 'var(--shadow-medium)',
        'ds-floating': 'var(--shadow-floating)',
        'ds-modal': 'var(--shadow-modal)',
        'ds-hero': 'var(--shadow-hero)',
        'ds-glow': '0 0 25px -5px rgba(99, 102, 241, 0.4)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float-slow': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s infinite linear',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        glowPulse: {
          '0%': { opacity: '0.4', filter: 'blur(20px)' },
          '100%': { opacity: '0.8', filter: 'blur(35px)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;


