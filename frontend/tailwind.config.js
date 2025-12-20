/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // ================================================================
      // COLOR PALETTE (Professional SOC Dashboard Theme)
      // ================================================================
      colors: {
        // Primary colors (Dark mode optimized)
        slate: {
          '950': '#030712',
          '900': '#0f172a',
          '800': '#1e293b',
          '700': '#334155',
          '600': '#475569',
          '500': '#64748b',
          '400': '#94a3b8',
          '300': '#cbd5e1',
          '200': '#e2e8f0',
          '100': '#f1f5f9',
        },
        // Accent colors
        cyan: {
          '600': '#0891b2',
          '500': '#06b6d4',
          '400': '#22d3ee',
          '300': '#67e8f9',
          '200': '#a5f3fc',
        },
        emerald: {
          '600': '#059669',
          '500': '#10b981',
          '400': '#34d399',
          '300': '#6ee7b7',
        },
        rose: {
          '600': '#e11d48',
          '500': '#f43f5e',
          '400': '#fb7185',
          '300': '#fda4af',
        },
        amber: {
          '600': '#d97706',
          '500': '#f59e0b',
          '400': '#fbbf24',
          '300': '#fcd34d',
        },
        purple: {
          '600': '#9333ea',
          '500': '#a855f7',
          '400': '#c084fc',
          '300': '#d8b4fe',
        },
      },

      // ================================================================
      // ANIMATIONS
      // ================================================================
      animation: {
        'fade-in': 'fadeInSlideUp 0.3s ease-out',
        'fade-out': 'fadeOutSlideDown 0.3s ease-out',
        'slide-in-left': 'slideInFromLeft 0.3s ease-out',
        'slide-out-left': 'slideOutToLeft 0.3s ease-out',
        'pulse-custom': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'siren': 'siren 2s infinite',
        'scale-in': 'scaleIn 0.3s ease-out',
      },

      keyframes: {
        'fadeInSlideUp': {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'fadeOutSlideDown': {
          from: { opacity: '1', transform: 'translateY(0)' },
          to: { opacity: '0', transform: 'translateY(12px)' },
        },
        'slideInFromLeft': {
          from: { opacity: '0', transform: 'translateX(-16px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'slideOutToLeft': {
          from: { opacity: '1', transform: 'translateX(0)' },
          to: { opacity: '0', transform: 'translateX(-16px)' },
        },
        'glow': {
          '0%, 100%': { boxShadow: '0 0 8px rgba(6, 182, 212, 0.3)' },
          '50%': { boxShadow: '0 0 16px rgba(6, 182, 212, 0.5)' },
        },
        'siren': {
          '0%': { boxShadow: '0 0 0 0 rgba(244, 63, 94, 0.7)' },
          '70%': { boxShadow: '0 0 0 10px rgba(244, 63, 94, 0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(244, 63, 94, 0)' },
        },
        'scaleIn': {
          from: { transform: 'scale(0.95)', opacity: '0' },
          to: { transform: 'scale(1)', opacity: '1' },
        },
      },

      // ================================================================
      // BOX SHADOWS
      // ================================================================
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(6, 182, 212, 0.5)',
        'glow-emerald': '0 0 20px rgba(16, 185, 129, 0.5)',
        'glow-rose': '0 0 20px rgba(244, 63, 94, 0.5)',
      },

      // ================================================================
      // SCREEN SIZES
      // ================================================================
      screens: {
        'xs': '320px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
        '3xl': '1920px',
        '4k': '2560px',
      },

      // ================================================================
      // MIN/MAX HEIGHT
      // ================================================================
      minHeight: {
        'screen': '100vh',
        'screen-minus-header': 'calc(100vh - 4rem)',
      },

      height: {
        'screen-minus-header': 'calc(100vh - 4rem)',
      },

      // ================================================================
      // GRID TEMPLATES
      // ================================================================
      gridTemplateColumns: {
        'auto-fit-sm': 'repeat(auto-fit, minmax(320px, 1fr))',
        'auto-fit-md': 'repeat(auto-fit, minmax(400px, 1fr))',
        'auto-fit-lg': 'repeat(auto-fit, minmax(500px, 1fr))',
      },
    },
  },

  plugins: [
    function ({ addUtilities }) {
      const customUtilities = {
        '.glow-cyan': { boxShadow: '0 0 20px rgba(6, 182, 212, 0.5)' },
        '.glow-emerald': { boxShadow: '0 0 20px rgba(16, 185, 129, 0.5)' },
        '.glow-rose': { boxShadow: '0 0 20px rgba(244, 63, 94, 0.5)' },
      };
      addUtilities(customUtilities);
    },
  ],
}

