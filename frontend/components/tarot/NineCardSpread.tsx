'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import CardFlip from './CardFlip';
import CardFace from './CardFace';
import CardBack from './CardBack';
import CardDetailModal from './CardDetailModal';
import type { DrawnCard, SpreadPosition } from '@/lib/types';

interface NineCardSpreadProps {
  cards: DrawnCard[];
  spreadPositions: SpreadPosition[];
  locale: 'ru' | 'en';
}

const FLIP_STAGGER_MS = 180;

export default function NineCardSpread({
  cards,
  spreadPositions,
  locale,
}: NineCardSpreadProps) {
  const prefersReducedMotion = useReducedMotion();
  const [flippedCards, setFlippedCards] = useState<boolean[]>(Array(9).fill(false));
  const [clickedIndex, setClickedIndex] = useState<number | null>(null);
  const [selectedCardIndex, setSelectedCardIndex] = useState<number | null>(null);
  const hasTriggeredRef = useRef(false);

  useEffect(() => {
    if (hasTriggeredRef.current) return;
    hasTriggeredRef.current = true;

    if (prefersReducedMotion) {
      setFlippedCards(Array(9).fill(true));
      return;
    }

    const timers = Array.from({ length: 9 }, (_, i) =>
      setTimeout(() => {
        setFlippedCards((prev) => {
          const next = [...prev];
          next[i] = true;
          return next;
        });
      }, i * FLIP_STAGGER_MS + 300)
    );

    return () => timers.forEach(clearTimeout);
  }, [prefersReducedMotion]);

  const positionLabel = (pos: SpreadPosition) =>
    locale === 'ru' ? pos.label_ru : pos.label_en;
  const positionMeaning = (pos: SpreadPosition) =>
    locale === 'ru' ? pos.meaning_ru : pos.meaning_en;

  const selectedDrawnCard =
    selectedCardIndex !== null
      ? (cards.find((c) => c.position_index === selectedCardIndex) ?? null)
      : null;
  const selectedPosition =
    selectedCardIndex !== null ? (spreadPositions[selectedCardIndex] ?? null) : null;

  return (
    <div className="w-full">
      <AnimatePresence>
        {selectedDrawnCard !== null && selectedPosition !== null && (
          <CardDetailModal
            key={`modal-${selectedCardIndex}`}
            card={selectedDrawnCard.card}
            isReversed={selectedDrawnCard.is_reversed}
            positionLabel={positionLabel(selectedPosition)}
            positionMeaning={positionMeaning(selectedPosition)}
            locale={locale}
            onClose={() => setSelectedCardIndex(null)}
          />
        )}
      </AnimatePresence>

      <div className="grid grid-cols-3 gap-3 md:gap-4 w-full max-w-lg mx-auto">
        {Array.from({ length: 9 }, (_, i) => {
          const drawnCard = cards.find((c) => c.position_index === i) ?? null;
          const pos = spreadPositions[i];
          const isFaceUp = flippedCards[i] ?? false;

          return (
            <motion.div
              key={i}
              className="flex flex-col items-center gap-2"
              initial={prefersReducedMotion ? false : { opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.06, duration: 0.35 }}
            >
              {pos && (
                <p
                  className="font-serif text-center leading-tight"
                  style={{
                    color: 'rgba(212,175,55,0.65)',
                    fontSize: '0.55rem',
                    letterSpacing: '0.08em',
                  }}
                >
                  {positionLabel(pos)}
                </p>
              )}

              <motion.div
                className="w-full cursor-pointer"
                animate={
                  !prefersReducedMotion && clickedIndex === i
                    ? { scale: 1.15 }
                    : { scale: 1 }
                }
                whileHover={drawnCard !== null ? { scale: 1.07 } : {}}
                transition={{ duration: 0.18, ease: 'easeOut' }}
                onClick={() => {
                  if (drawnCard === null) return;
                  if (!isFaceUp) {
                    setFlippedCards((prev) => {
                      const next = [...prev];
                      next[i] = true;
                      return next;
                    });
                  } else {
                    if (prefersReducedMotion) {
                      setSelectedCardIndex(i);
                    } else {
                      setClickedIndex(i);
                      setTimeout(() => {
                        setSelectedCardIndex(i);
                        setClickedIndex(null);
                      }, 250);
                    }
                  }
                }}
              >
                {drawnCard !== null ? (
                  <CardFlip
                    isFaceUp={isFaceUp}
                    front={
                      <CardFace
                        card={drawnCard.card}
                        isReversed={drawnCard.is_reversed}
                        locale={locale}
                      />
                    }
                    back={<CardBack />}
                  />
                ) : (
                  <div
                    className="w-full rounded-lg"
                    style={{
                      aspectRatio: '2 / 3',
                      border: '1px dashed rgba(212,175,55,0.2)',
                      background: 'rgba(212,175,55,0.02)',
                    }}
                  />
                )}
              </motion.div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
