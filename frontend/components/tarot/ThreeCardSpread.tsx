'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
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
  const [selectedCardIndex, setSelectedCardIndex] = useState<number | null>(null);
  const [clickedIndex, setClickedIndex] = useState<number | null>(null);
  const [flippedCards, setFlippedCards] = useState<[boolean, boolean, boolean]>([false, false, false]);
  const [activeSlide, setActiveSlide] = useState(0);
  const hasTriggeredRef = useRef(false);
  const sliderRef = useRef<HTMLDivElement>(null);

  const hasCards = cards !== null && cards.length > 0;

  // Auto-flip cards on load
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

  // Track active slide via IntersectionObserver
  const slideRefs = useRef<(HTMLDivElement | null)[]>([null, null, null]);
  useEffect(() => {
    const slider = sliderRef.current;
    if (!slider) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
            const idx = slideRefs.current.indexOf(entry.target as HTMLDivElement);
            if (idx >= 0) setActiveSlide(idx);
          }
        });
      },
      { root: slider, threshold: 0.5 }
    );
    slideRefs.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const scrollToSlide = useCallback((index: number) => {
    const slider = sliderRef.current;
    const slide = slideRefs.current[index];
    if (!slider || !slide) return;
    const sliderRect = slider.getBoundingClientRect();
    const slideRect = slide.getBoundingClientRect();
    const offset = slideRect.left - sliderRect.left + slider.scrollLeft - (sliderRect.width - slideRect.width) / 2;
    slider.scrollTo({ left: offset, behavior: 'smooth' });
  }, []);

  const positionLabel = (pos: SpreadPosition) =>
    locale === 'ru' ? pos.label_ru : pos.label_en;
  const positionMeaning = (pos: SpreadPosition) =>
    locale === 'ru' ? pos.meaning_ru : pos.meaning_en;

  const fallbackPositions: SpreadPosition[] = [
    { index: 0, label_ru: t('three_card.past'),    label_en: t('three_card.past'),    meaning_ru: '', meaning_en: '' },
    { index: 1, label_ru: t('three_card.present'), label_en: t('three_card.present'), meaning_ru: '', meaning_en: '' },
    { index: 2, label_ru: t('three_card.future'),  label_en: t('three_card.future'),  meaning_ru: '', meaning_en: '' },
  ];

  const positions = spreadPositions.length > 0 ? spreadPositions : fallbackPositions;

  const selectedDrawnCard =
    selectedCardIndex !== null && cards
      ? (cards.find((c) => c.position_index === selectedCardIndex) ?? null)
      : null;
  const selectedPosition =
    selectedCardIndex !== null ? positions[selectedCardIndex] ?? null : null;

  /** Shared card slot logic used in both mobile and desktop layouts */
  const renderCard = (pos: SpreadPosition, i: number, cardWidth: string) => {
    const drawnCard = cards ? cards.find((c) => c.position_index === i) ?? null : null;
    const isFaceUp = flippedCards[i] ?? false;

    return (
      <>
        {/* Position label */}
        <p
          className="font-serif tracking-widest uppercase text-center"
          style={{ color: '#d4af37', letterSpacing: '0.14em', fontSize: '0.75rem' }}
        >
          {positionLabel(pos)}
        </p>

        {/* Card */}
        <motion.div
          className="cursor-pointer"
          style={{ width: cardWidth }}
          animate={!prefersReducedMotion && clickedIndex === i ? { scale: 1.12 } : { scale: 1 }}
          whileHover={drawnCard !== null ? { scale: 1.05 } : {}}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          onClick={() => {
            if (!drawnCard) return;
            if (!isFaceUp) {
              setFlippedCards((prev) => {
                const next = [...prev] as [boolean, boolean, boolean];
                next[i] = true;
                return next;
              });
            } else if (prefersReducedMotion) {
              setSelectedCardIndex(i);
            } else {
              setClickedIndex(i);
              setTimeout(() => { setSelectedCardIndex(i); setClickedIndex(null); }, 300);
            }
          }}
        >
          {drawnCard !== null ? (
            <CardFlip
              isFaceUp={isFaceUp}
              front={<CardFace card={drawnCard.card} isReversed={drawnCard.is_reversed} locale={locale} />}
              back={<CardBack />}
            />
          ) : (
            <div
              className="w-full rounded-xl"
              style={{ aspectRatio: '2 / 3', border: '1px dashed rgba(212,175,55,0.3)', background: 'rgba(212,175,55,0.03)' }}
            />
          )}
        </motion.div>

        {/* Position meaning (collapsible) — desktop only; mobile shows below slide */}
        {positionMeaning(pos) !== '' && drawnCard !== null && (
          <p
            className="hidden md:block text-xs text-center leading-relaxed max-w-[140px]"
            style={{ color: 'rgba(201,194,224,0.5)' }}
          >
            {positionMeaning(pos)}
          </p>
        )}
      </>
    );
  };

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

      {/* ── MOBILE: horizontal snap scroll slider ────────────────────── */}
      <div className="md:hidden w-full flex flex-col items-center gap-4">
        <div
          ref={sliderRef}
          className="w-full flex gap-5 overflow-x-auto"
          style={{
            scrollSnapType: 'x mandatory',
            WebkitOverflowScrolling: 'touch',
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            paddingLeft: '10vw',
            paddingRight: '10vw',
            paddingBottom: '8px',
          }}
        >
          {positions.map((pos, i) => (
            <div
              key={pos.index}
              ref={(el) => { slideRefs.current[i] = el; }}
              className="flex flex-col items-center gap-3 flex-shrink-0"
              style={{ scrollSnapAlign: 'center', width: '75vw', maxWidth: '280px' }}
            >
              {renderCard(pos, i, '100%')}
            </div>
          ))}
        </div>

        {/* Dots */}
        <div className="flex gap-2 items-center">
          {positions.map((_, i) => (
            <button
              key={i}
              onClick={() => scrollToSlide(i)}
              aria-label={`Карта ${i + 1}`}
              style={{
                borderRadius: '9999px',
                transition: 'all 0.25s',
                background: activeSlide === i ? '#d4af37' : 'rgba(212,175,55,0.25)',
                width: activeSlide === i ? '20px' : '8px',
                height: '8px',
                border: 'none',
                padding: 0,
                cursor: 'pointer',
              }}
            />
          ))}
        </div>

        {/* Position meaning for active slide */}
        <AnimatePresence mode="wait">
          {positionMeaning(positions[activeSlide] ?? positions[0]) !== '' && (
            <motion.p
              key={activeSlide}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.25 }}
              className="text-xs text-center px-6 leading-relaxed"
              style={{ color: 'rgba(201,194,224,0.5)', maxWidth: '280px' }}
            >
              {positionMeaning(positions[activeSlide] ?? positions[0])}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {/* ── DESKTOP: three columns ───────────────────────────────────── */}
      <div className="hidden md:flex gap-6 justify-center items-start">
        {positions.map((pos, i) => (
          <motion.div
            key={pos.index}
            className="flex flex-col items-center gap-3 flex-1"
            style={{ maxWidth: '180px' }}
            initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1, duration: 0.4 }}
          >
            {renderCard(pos, i, '140px')}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
