import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  // Safelist dynamic classes that are constructed at runtime
  // These classes are used in TiptapEditor.tsx and globals.css
  safelist: [
    // Document styles (doc-style-modern, doc-style-classic, doc-style-compact)
    { pattern: /^doc-style-(modern|classic|compact)$/ },
    // Document formats (doc-format-a4, doc-format-letter, doc-format-wide)
    { pattern: /^doc-format-(a4|letter|wide)$/ },
    // Document fonts (doc-font-sans, doc-font-serif, doc-font-mono)
    { pattern: /^doc-font-(sans|serif|mono)$/ },
    // Document sizes (doc-size-sm, doc-size-md, doc-size-lg)
    { pattern: /^doc-size-(sm|md|lg)$/ },
    // Document line heights (doc-leading-tight, doc-leading-normal, doc-leading-relaxed)
    { pattern: /^doc-leading-(tight|normal|relaxed)$/ },
    // Document margins (doc-margin-narrow, doc-margin-normal, doc-margin-wide)
    { pattern: /^doc-margin-(narrow|normal|wide)$/ },
    // Theme classes
    'doc-theme-ep',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // illanes v3 color palette
      colors: {
        bg: 'var(--bg)',
        paper: 'var(--paper)',
        ink: 'var(--ink)',
        muted: 'var(--muted)',
        line: 'var(--line)',
        'line-strong': 'var(--line-strong)',
        // Semantic colors
        'c-green': 'var(--c-green)',
        'c-blue': 'var(--c-blue)',
        'c-amber': 'var(--c-amber)',
        'c-red': 'var(--c-red)',
      },
      // illanes v3 spacing (4px base)
      spacing: {
        '1': '0.25rem',   // 4px
        '2': '0.5rem',    // 8px
        '3': '0.75rem',   // 12px
        '4': '1rem',      // 16px
        '5': '1.25rem',   // 20px
        '6': '1.5rem',    // 24px
        '8': '2rem',      // 32px
        '10': '2.5rem',   // 40px
        '12': '3rem',     // 48px
        '16': '4rem',     // 64px
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'xs': ['0.8125rem', { lineHeight: '1.4' }],    // 13px
        'sm': ['0.875rem', { lineHeight: '1.5' }],     // 14px
        'base': ['1rem', { lineHeight: '1.62' }],      // 16px
        'lg': ['1.125rem', { lineHeight: '1.5' }],     // 18px
        'xl': ['1.25rem', { lineHeight: '1.4' }],      // 20px - H3
        '2xl': ['1.5rem', { lineHeight: '1.3' }],      // 24px - H2
        '3xl': ['1.75rem', { lineHeight: '1.2' }],     // 28px - H1
        '4xl': ['2.25rem', { lineHeight: '1.1' }],     // 36px - Hero
      },
      fontWeight: {
        normal: '400',
        medium: '600',
        semibold: '700',
        bold: '800',
        black: '900',
      },
      borderRadius: {
        none: '0',
      },
      boxShadow: {
        none: 'none',
      },
      maxWidth: {
        'narrow': '760px',
        'container': '1160px',
        'wide': '1400px',
      },
    },
  },
  plugins: [],
}

export default config
