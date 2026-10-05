/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#070A12',      // Deep obsidian space
        panel: '#0D1322',           // Polished surface panel
        'panel-subtle': '#121B2F',   // Secondary elevated panel
        border: '#1A243B',          // Subtle pro border
        'border-strong': '#283756',  // Highlight border
        bullish: '#10B981',         // Trading emerald
        'bullish-bg': '#064E3B',    // Trading green subtle
        bearish: '#F43F5E',         // Trading rose crimson
        'bearish-bg': '#881337',    // Trading red subtle
        accent: '#0EA5E9',          // High-precision electric cyan
        'accent-hover': '#38BDF8',  // Cyan hover
        'accent-indigo': '#6366F1', // AI neural indigo
        'accent-violet': '#8B5CF6', // Purple core
      },
      boxShadow: {
        'glow-accent': '0 0 20px -5px rgba(14, 165, 233, 0.3)',
        'glow-emerald': '0 0 20px -5px rgba(16, 185, 129, 0.3)',
        'glow-rose': '0 0 20px -5px rgba(244, 63, 94, 0.3)',
        'card-inner': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.06)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
