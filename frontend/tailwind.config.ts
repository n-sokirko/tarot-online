import type { Config } from 'tailwindcss';

// Design system "Обсидиан" — see design_handoff_tarot_redesign/README.md.
// The legacy names (midnight, royal, gold, mist) are kept and re-pointed at the
// new palette so every existing page picks it up without being rewritten; the
// new names are what fresh code should reach for.
const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Legacy names, new values.
        midnight: '#0B0A0F',
        royal: '#131019',
        gold: '#E0B26C',
        ember: '#a02c2c',
        mist: '#F2EDE4',

        // Obsidian tokens.
        accent: '#E0B26C',
        ink: {
          DEFAULT: '#F2EDE4', // primary text
          2: '#A49DAF',       // paragraphs
          3: '#9A94A6',       // captions
          4: '#8E879B',       // mono labels
          5: '#7E7890',       // inactive tabs
          6: '#6F6A7C',       // faintest service text
        },
        surface: {
          DEFAULT: '#131019',
          deep: '#0C0A11',
          card: '#1E1830',
          sheet: '#120F19',
        },
        streak: '#8FD3C4',
        violet: '#B6A7F0',
      },
      fontFamily: {
        serif: ['var(--font-prata)', 'Prata', 'Georgia', 'serif'],
        sans: ['var(--font-manrope)', 'Manrope', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', '"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      transitionTimingFunction: {
        // Main curve, card flip, shuffle.
        obsidian: 'cubic-bezier(.2,.8,.2,1)',
        flip: 'cubic-bezier(.3,.9,.2,1)',
        shuffle: 'cubic-bezier(.4,.1,.3,1)',
      },
      boxShadow: {
        card: '0 26px 40px -24px #000',
        'card-lift': '0 50px 60px -24px #000',
        fan: '0 30px 50px -26px #000',
        sheet: '0 -30px 60px -30px #000',
        gold: '0 14px 30px -14px rgba(224,178,108,.9)',
      },
    },
  },
  plugins: [],
};

export default config;
