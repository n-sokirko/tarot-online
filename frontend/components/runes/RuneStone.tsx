'use client';

import { motion } from 'framer-motion';

interface RuneStoneProps {
  symbol: string;
  name: string;
  positionLabel?: string;
  delay?: number;
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

const SIZES: Record<NonNullable<RuneStoneProps['size']>, { w: number; h: number; symbol: string }> = {
  sm: { w: 64, h: 80, symbol: 'text-2xl' },
  md: { w: 96, h: 120, symbol: 'text-4xl' },
  lg: { w: 128, h: 160, symbol: 'text-5xl' },
};

/**
 * A carved-stone visual for a single rune. No image asset — drawn with CSS
 * to keep the deck weightless and to match the slightly-rough aesthetic.
 */
export default function RuneStone({ symbol, name, positionLabel, delay = 0, size = 'md', onClick }: RuneStoneProps) {
  const dims = SIZES[size];
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, rotateY: 90 }}
      animate={{ opacity: 1, y: 0, rotateY: 0 }}
      transition={{ duration: 0.6, delay, ease: [0.2, 0.7, 0.2, 1] }}
      onClick={onClick}
      className="flex flex-col items-center gap-2"
    >
      {positionLabel && (
        <span
          className="text-[9px] tracking-widest uppercase"
          style={{ color: 'rgba(212,175,55,0.5)', letterSpacing: '0.22em' }}
        >
          {positionLabel}
        </span>
      )}
      <div
        className={`flex items-center justify-center font-serif select-none ${dims.symbol}`}
        style={{
          width: dims.w,
          height: dims.h,
          borderRadius: '12% / 9%',
          background:
            'radial-gradient(ellipse at 30% 25%, #4a4338 0%, #2b2620 55%, #1a1612 100%)',
          boxShadow:
            'inset 0 2px 4px rgba(255,240,200,0.08), inset 0 -3px 6px rgba(0,0,0,0.6), 0 6px 16px rgba(0,0,0,0.5)',
          color: '#d4af37',
          textShadow: '0 0 8px rgba(212,175,55,0.4), 0 1px 2px rgba(0,0,0,0.8)',
          cursor: onClick ? 'pointer' : 'default',
          position: 'relative',
        }}
      >
        {/* Subtle carved texture */}
        <div
          aria-hidden
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 'inherit',
            background:
              'repeating-linear-gradient(125deg, rgba(255,240,200,0.025) 0 2px, transparent 2px 7px)',
            mixBlendMode: 'overlay',
          }}
        />
        <span style={{ position: 'relative', zIndex: 1 }}>{symbol}</span>
      </div>
      <span
        className="font-serif text-xs tracking-wide"
        style={{ color: 'rgba(201,194,224,0.85)' }}
      >
        {name}
      </span>
    </motion.div>
  );
}
