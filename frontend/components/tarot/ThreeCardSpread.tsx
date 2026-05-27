'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import CardFlip from './CardFlip';
import CardFace from './CardFace';
import CardBack from './CardBack';
import CardDetailModal from './CardDetailModal';
import type { DrawnCard, SpreadPosition } from '@/lib/types';

interface ThreeCardSpreadProps {
  cards: DrawnCard[] | null;
  spreadPositions: SpreadPosition[];
  locale: 'ru' | 'en';
}

const FLIP_STAGGER_MS = 300;

export default function ThreeCardSpread({
  cards,
  spreadPositions,
  locale,
}: ThreeCardSpreadProps) {
  const t = useTranslations('positions');
  const prefersReducedMotion = useReducedMotion();
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [selectedCardIndex, setSelectedCardIndex] = useState<number | null>(null);
  const [clickedIndex, setClickedIndex] = useState<number | null>(null);
  const [flippedCards, setFlippedCards] = useState<[boolean, boolean, boolean]>([
    false,
    false,
    false,
  ]);
  const hasTriggeredRef = useRef(false);

  const hasCards = cards !== null && cards.length > 0;

  useEffect(() => {
    if (!hasCards || hasTriggeredRef.current) return;
    hasTriggeredRef.current = true;

    if (prefersReducedMotion) {
      setFlippedCards([true, true, true]);
      return;
    }

    const timers = ([0, 1, 2] as const).map((i) =>
      setTimeout(() => {
        setFlippedCards((prev) => {
          const next: [boolean, boolean, boolean] = [...prev] as [boolean, boolean, boolean];
          next[i] = true;
          return next;
        });
      }, i * FLIP_STAGGER_MS + 400)
    );

    return () => timers.forEach(clearTimeout);
  }, [hasCards, prefersReducedMotion]);

  const positionLabel = (pos: SpreadPosition) =>
    locale === 'ru' ? pos.label_ru : pos.label_en;
  const positionMeaning = (pos: SpreadPosition) =>
    locale === 'ru' ? pos.meaning_ru : pos.meaning_en;

  const fallbackPositions: SpreadPosition[] = [
    {
      index: 0,
      label_ru: t('three_card.past'),
      label_en: t('three_card.past'),
      meaning_ru: '',
      meaning_en: '',
    },
    {
      index: 1,
      label_ru: t('three_card.present'),
      label_en: t('three_card.present'),
      meaning_ru: '',
      meaning_en: '',
    },
    {
      index: 2,
      label_ru: t('three_card.future'),
      label_en: t('three_card.future'),
      meaning_ru: '',
      meaning_en: '',
    },
  ];

  const positions = spreadPositions.length > 0 ? spreadPositions : fallbackPositions;

  const selectedDrawnCard =
    selectedCardIndex !== null && cards
      ? (cards.find((c) => c.position_index === selectedCardIndex) ?? null)
      : null;
  const selectedPosition =
    selectedCardIndex !== null ? positions[selectedCardIndex] ?? null : null;

  return (
    <div className="w-full">
      {/* Card detail modal */}
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

      <div className="flex flex-col md:flex-row gap-6 md:gap-4 justify-center items-start">
        {positions.map((pos, i) => {
          const drawnCard = cards
            ? cards.find((c) => c.position_index === i) ?? null
            : null;
          const isExpanded = expandedIndex === i;

          return (
            <motion.div
              key={pos.index}
              className="flex flex-col items-center gap-3 flex-1 max-w-[180px] mx-auto md:mx-0"
              initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.4 }}
            >
              {/* Position label */}
              <p
                className="font-serif text-sm tracking-widest uppercase text-center"
                style={{ color: '#d4af37', letterSpacing: '0.12em' }}
              >
                {positionLabel(pos)}
              </p>

              {/* Card slot */}
              <motion.div
                className="w-full cursor-pointer"
                style={{ maxWidth: '140px' }}
                animate={
                  !prefersReducedMotion && clickedIndex === i
                    ? { scale: 1.18 }
                    : { scale: 1 }
                }
                whileHover={drawnCard !== null ? { scale: 1.08 } : {}}
                transition={{ duration: 0.2, ease: 'easeOut' }}
                onClick={() => {
                  if (drawnCard === null) return;
                  const isFaceUp = flippedCards[i] ?? false;
                  if (!isFaceUp) {
                    // Flip the card manually
                    setFlippedCards((prev) => {
                      const next: [boolean, boolean, boolean] = [...prev] as [boolean, boolean, boolean];
                      next[i] = true;
                      return next;
                    });
                  } else {
                    // Open detail modal
                    if (prefersReducedMotion) {
                      setSelectedCardIndex(i);
                    } else {
                      setClickedIndex(i);
                      setTimeout(() => {
                        setSelectedCardIndex(i);
                        setClickedIndex(null);
                      }, 300);
                    }
                  }
                }}
              >
                {drawnCard !== null ? (
                  <div>
                    <CardFlip
                      isFaceUp={flippedCards[i] ?? false}
                      front={
                        <CardFace
                          card={drawnCard.card}
                          isReversed={drawnCard.is_reversed}
                          locale={locale}
                        />
                      }
                      back={<CardBack />}
                    />
                  </div>
                ) : (
                  <div
                    className="w-full rounded-xl"
                    style={{
                      aspectRatio: '2 / 3',
                      border: '1px dashed rgba(212,175,55,0.3)',
                      background: 'rgba(212,175,55,0.03)',
                    }}
                  />
                )}
              </motion.div>

              {/* Collapsible position meaning */}
              {drawnCard !== null && positionMeaning(pos) !== '' && (
                <div className="w-full text-center">
                  <button
                    className="text-xs font-serif tracking-wide transition-colors"
                    style={{ color: 'rgba(201,194,224,0.5)' }}
                    onClick={() => setExpandedIndex(isExpanded ? null : i)}
                    aria-expanded={isExpanded}
                  >
                    {isExpanded ? '▲' : '▼'}
                  </button>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.p
                        key={`meaning-${i}`}
                        className="mt-1 text-xs leading-relaxed text-center"
                        style={{ color: 'rgba(201,194,224,0.65)' }}
                        initial={
                          prefersReducedMotion ? false : { opacity: 0, height: 0 }
                        }
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={
                          prefersReducedMotion ? {} : { opacity: 0, height: 0 }
                        }
                      >
                        {positionMeaning(pos)}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
