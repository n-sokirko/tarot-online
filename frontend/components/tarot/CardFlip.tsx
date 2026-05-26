'use client';

import { useReducedMotion } from 'framer-motion';
import type { ReactNode } from 'react';

interface CardFlipProps {
  isFaceUp: boolean;
  front: ReactNode;
  back: ReactNode;
}

export default function CardFlip({ isFaceUp, front, back }: CardFlipProps) {
  const prefersReducedMotion = useReducedMotion();

  if (prefersReducedMotion) {
    return (
      <div className="relative w-full" style={{ aspectRatio: '2 / 3' }}>
        {isFaceUp ? front : back}
      </div>
    );
  }

  return (
    <div
      className="relative w-full"
      style={{
        aspectRatio: '2 / 3',
        perspective: '1000px',
      }}
    >
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          transformStyle: 'preserve-3d',
          transition: 'transform 700ms ease',
          transform: isFaceUp ? 'rotateY(180deg)' : 'rotateY(0deg)',
        }}
      >
        {/* Back face (default visible) */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backfaceVisibility: 'hidden',
            WebkitBackfaceVisibility: 'hidden',
          }}
        >
          {back}
        </div>

        {/* Front face (shown after flip) */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backfaceVisibility: 'hidden',
            WebkitBackfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
          }}
        >
          {front}
        </div>
      </div>
    </div>
  );
}
