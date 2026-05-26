'use client';

import { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import CardBack from './CardBack';

interface DeckPileProps {
  onShuffleComplete: () => void;
}

// Stable rotations for each card in the pile
const PILE_ROTATIONS = [-3, 2, -1, 3, -2, 1, -0.5];

export default function DeckPile({ onShuffleComplete }: DeckPileProps) {
  const t = useTranslations('reading');
  const prefersReducedMotion = useReducedMotion();
  const [isShuffling, setIsShuffling] = useState(false);
  const [shuffled, setShuffled] = useState(false);

  const handleShuffle = () => {
    if (isShuffling || shuffled) return;

    if (prefersReducedMotion) {
      setShuffled(true);
      onShuffleComplete();
      return;
    }

    setIsShuffling(true);

    // After fan-out animation plays, mark complete
    setTimeout(() => {
      setIsShuffling(false);
      setShuffled(true);
      onShuffleComplete();
    }, 1200);
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Deck pile */}
      <div
        className="relative cursor-pointer select-none"
        style={{ width: '120px', height: '180px' }}
        onClick={handleShuffle}
        role="button"
        tabIndex={0}
        aria-label={t('shuffle')}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') handleShuffle();
        }}
      >
        {PILE_ROTATIONS.map((rot, i) => {
          // During shuffle: fan cards out then they restack
          const fanAngle = isShuffling
            ? rot * 8 + (i - 3) * 20
            : rot;
          const fanX = isShuffling ? (i - 3) * 18 : 0;
          const fanY = isShuffling ? Math.abs(i - 3) * -5 : 0;

          return (
            <motion.div
              key={i}
              className="absolute inset-0"
              animate={
                prefersReducedMotion
                  ? {}
                  : {
                      rotate: fanAngle,
                      x: fanX,
                      y: fanY,
                    }
              }
              transition={{
                type: 'spring',
                stiffness: 120,
                damping: 14,
                delay: isShuffling ? i * 0.04 : (PILE_ROTATIONS.length - i) * 0.04,
              }}
            >
              <CardBack rotation={0} />
            </motion.div>
          );
        })}
      </div>

      {/* Shuffle button */}
      {!shuffled && (
        <motion.button
          className="px-8 py-3 rounded-full font-serif text-sm tracking-widest uppercase transition-all"
          style={{
            background: 'transparent',
            border: '1px solid #d4af37',
            color: '#d4af37',
            letterSpacing: '0.15em',
          }}
          whileHover={prefersReducedMotion ? {} : { scale: 1.05, backgroundColor: 'rgba(212,175,55,0.1)' }}
          whileTap={prefersReducedMotion ? {} : { scale: 0.97 }}
          onClick={handleShuffle}
          disabled={isShuffling}
        >
          {isShuffling ? '···' : t('shuffle')}
        </motion.button>
      )}

      {shuffled && (
        <p
          className="text-sm font-serif tracking-wide"
          style={{ color: 'rgba(201,194,224,0.6)' }}
        >
          ✦
        </p>
      )}
    </div>
  );
}
