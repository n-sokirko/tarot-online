import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        midnight: '#0b0b1f',
        royal: '#1c1840',
        gold: '#d4af37',
        ember: '#a02c2c',
        mist: '#c9c2e0',
      },
      fontFamily: {
        serif: ['var(--font-cormorant)', '"Cormorant Garamond"', 'Georgia', 'serif'],
        sans: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
