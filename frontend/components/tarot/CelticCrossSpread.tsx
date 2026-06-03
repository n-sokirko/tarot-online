'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import CardFlip from './CardFlip';
import CardFace from './CardFace';
import CardBack from './CardBack';
import CardDetailModal from './CardDetailModal';
import type { DrawnCard, SpreadPosition } from '@/lib/types';

interface CelticCrossSpreadProps {
  cards: DrawnCard[];
  spreadPositions: SpreadPosition[];
  locale: 'ru' | 'en';
}

const FLIP_STAGGER_MS = 200;
const CARD_COUNT = 10;

// Celtic Cross layout:
//  Cross (6 cards):   [5 Crown]
//                     [3 Foundation] ←— in position below cross
//  [4 Past] ─ [1 Present + 2 Challenge(rotated)] ─ [6 Future]
//
//  Staff (4 cards, right column, top to bottom):
//  [10 Outcome] [9 Hopes/Fears] [8 Environment] [7 Self]
//
// We'll render in a grid. Mobile: stack vertically. Desktop: side-by-side.

type Slot = {
  /** position_index from the data (0-9) */
  idx: number;
  /** grid column (1-based) */
  col: number;
  /** grid row (1-based) */
  row: number;
  /** Is this the crossing card (card 2, rendered rotated) */
  crossing?: boolean;
};

// 7-column, 4-row desktop grid
// Columns 1-4: the cross; columns 5-7 hidden spacer; column 6-7: staff
const DESKTOP_SLOTS: Slot[] = [
  { idx: 4, col: 3, row: 1 },              // Crown (5th card)
  { idx: 3, col: 2, row: 2 },              // Past (4th)
  { idx: 0, col: 3, row: 2 },              // Present (1st) — stacked with crossing
  { idx: 1, col: 3, row: 2, crossing: true }, // Challenge/crossing (2nd) rotated
  { idx: 5, col: 4, row: 2 },              // Future (6th)
  { idx: 2, col: 3, row: 3 },              // Foundation (3rd)
  { idx: 6, col: 6, row: 1 },              // Self (7th)
  { idx: 7, col: 6, row: 2 },              // Environment (8th)
  { idx: 8, col: 6, row: 3 },              // Hopes & fears (9th)
  { idx: 9, col: 6, row: 4 },              // Outcome (10th)
];

export default function CelticCrossSpread({
  cards,
  spreadPositions,
  locale,
}: CelticCrossSpreadProps) {
  const prefersReducedMotion = useReducedMotion();
  const [flippedCards, setFlippedCards] = useState<boolean[]>(Array(CARD_COUNT).fill(false));
  const [clickedIndex, setClickedIndex] = useState<number | null>(null);
  const [selectedCardIndex, setSelectedCardIndex] = useState<number | null>(null);
  const hasTriggeredRef = useRef(false);

  useEffect(() => {
    if (hasTriggeredRef.current) return;
    hasTriggeredRef.current = true;

    if (prefersReducedMotion) {
      setFlippedCards(Array(CARD_COUNT).fill(true));
      return;
    }

    const timers = Array.from({ length: CARD_COUNT }, (_, i) =>
      setTimeout(() => {
        setFlippedCards((prev) => {
          const next = [...prev];
          next[i] = true;
          return next;
        });
      }, i * FLIP_STAGGER_MS + 400)
    );
    return () => timers.forEach(clearTimeout);
  }, [prefersReducedMotion]);

  const positionLabel = (pos: SpreadPosition) =>
    locale === 'ru' ? pos.label_ru : pos.label_en;

  const cardByIndex = (posIdx: number) =>
    cards.find((c) => c.position_index === posIdx) ?? null;

  const selectedDrawnCard =
    selectedCardIndex !== null ? cardByIndex(selectedCardIndex) : null;
  const selectedPos =
    selectedCardIndex !== null
      ? (spreadPositions[selectedCardIndex] ?? null)
      : null;

  const handleCardClick = (posIdx: number, isFaceUp: boolean) => {
    if (!isFaceUp) {
      setFlippedCards((prev) => {
        const next = [...prev];
        next[posIdx] = true;
        return next;
      });
    } else {
      if (prefersReducedMotion) {
        setSelectedCardIndex(posIdx);
      } else {
        setClickedIndex(posIdx);
        setTimeout(() => {
          setSelectedCardIndex(posIdx);
          setClickedIndex(null);
        }, 250);
      }
    }
  };

  // Compact card unit — shown in mobile list view
  const renderCardSlot = (slot: Slot) => {
    const drawnCard = cardByIndex(slot.idx);
    const isFaceUp = flippedCards[slot.idx] ?? false;
    const pos = spreadPositions[slot.idx];

    return (
      <div key={slot.idx} className="flex flex-col items-center gap-1">
        {pos && (
          <span
            className="flex items-center justify-center font-serif"
            style={{
              width: 22, height: 22, borderRadius: 999,
              background: 'rgba(212,175,55,0.12)',
              border: '1px solid rgba(212,175,55,0.3)',
              color: '#d4af37', fontSize: '0.7rem',
            }}
          >
            {slot.idx + 1}
          </span>
        )}
        <motion.div
          className={`cursor-pointer ${slot.crossing ? 'rotate-90' : ''}`}
          animate={
            !prefersReducedMotion && clickedIndex === slot.idx
              ? { scale: 1.15 }
              : { scale: 1 }
          }
          whileHover={drawnCard !== null ? { scale: 1.07 } : {}}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          style={{ width: slot.crossing ? '3.5rem' : '4rem' }}
          onClick={() => drawnCard && handleCardClick(slot.idx, isFaceUp)}
        >
          {drawnCard ? (
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
      </div>
    );
  };

  return (
    <>
      {/* ── Mobile: two columns — cross left, staff right ── */}
      <div className="w-full flex md:hidden flex-col items-center gap-4 px-2">
        {/* Cross section */}
        <p
          className="font-serif text-xs tracking-widest uppercase text-center"
          style={{ color: 'rgba(212,175,55,0.45)', letterSpacing: '0.18em' }}
        >
          {locale === 'ru' ? 'Крест ситуации' : 'The Cross'}
        </p>

        {/* Crown */}
        <div className="flex justify-center">{renderCardSlot(DESKTOP_SLOTS[0])}</div>

        {/* Past · Cross(Present+Challenge) · Future */}
        <div className="flex items-center gap-3 justify-center flex-wrap">
          {renderCardSlot(DESKTOP_SLOTS[1])}
          <div className="relative flex items-center justify-center" style={{ width: '5rem', height: '7rem' }}>
            {/* Present card */}
            <div className="absolute" style={{ zIndex: 1 }}>
              {renderCardSlot(DESKTOP_SLOTS[2])}
            </div>
            {/* Challenge card — offset and rotated */}
            <div className="absolute" style={{ transform: 'rotate(90deg) translateX(0.3rem)', zIndex: 2 }}>
              {renderCardSlot(DESKTOP_SLOTS[3])}
            </div>
          </div>
          {renderCardSlot(DESKTOP_SLOTS[4])}
        </div>

        {/* Foundation */}
        <div className="flex justify-center">{renderCardSlot(DESKTOP_SLOTS[5])}</div>

        {/* Staff section */}
        <p
          className="font-serif text-xs tracking-widest uppercase text-center mt-2"
          style={{ color: 'rgba(212,175,55,0.45)', letterSpacing: '0.18em' }}
        >
          {locale === 'ru' ? 'Посох развития' : 'The Staff'}
        </p>
        <div className="grid grid-cols-2 gap-4">
          {DESKTOP_SLOTS.slice(6).map(renderCardSlot)}
        </div>
      </div>

      {/* ── Desktop: CSS grid layout ── */}
      <div
        className="hidden md:grid w-full max-w-2xl"
        style={{
          gridTemplateColumns: 'repeat(6, 1fr)',
          gridTemplateRows: 'repeat(4, auto)',
          gap: '0.75rem',
          alignItems: 'center',
          justifyItems: 'center',
        }}
      >
        {/* Crown — col 3, row 1 */}
        <div style={{ gridColumn: 3, gridRow: 1 }}>{renderCardSlot(DESKTOP_SLOTS[0])}</div>

        {/* Past — col 2, row 2 */}
        <div style={{ gridColumn: 2, gridRow: 2 }}>{renderCardSlot(DESKTOP_SLOTS[1])}</div>

        {/* Present + Challenge stacked — col 3, row 2 */}
        <div
          style={{
            gridColumn: 3,
            gridRow: 2,
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '5rem',
            height: '8rem',
          }}
        >
          <div style={{ position: 'absolute', zIndex: 1 }}>
            {renderCardSlot(DESKTOP_SLOTS[2])}
          </div>
          <div
            style={{
              position: 'absolute',
              transform: 'rotate(90deg)',
              zIndex: 2,
              opacity: 0.9,
            }}
          >
            {renderCardSlot(DESKTOP_SLOTS[3])}
          </div>
        </div>

        {/* Future — col 4, row 2 */}
        <div style={{ gridColumn: 4, gridRow: 2 }}>{renderCardSlot(DESKTOP_SLOTS[4])}</div>

        {/* Foundation — col 3, row 3 */}
        <div style={{ gridColumn: 3, gridRow: 3 }}>{renderCardSlot(DESKTOP_SLOTS[5])}</div>

        {/* Staff separator */}
        <div
          style={{
            gridColumn: 5,
            gridRow: '1 / 5',
            width: '1px',
            height: '100%',
            background: 'rgba(212,175,55,0.15)',
            justifySelf: 'center',
          }}
        />

        {/* Staff cards — col 6, rows 1-4 */}
        {DESKTOP_SLOTS.slice(6).map((slot, i) => (
          <div key={slot.idx} style={{ gridColumn: 6, gridRow: i + 1 }}>
            {renderCardSlot(slot)}
          </div>
        ))}
      </div>

      {/* ── Readable legend: all 10 positions with card name + keywords ── */}
      <div className="w-full max-w-2xl mx-auto mt-10 flex flex-col gap-2 px-2">
        <p
          className="font-serif text-xs tracking-widest uppercase text-center mb-2"
          style={{ color: 'rgba(212,175,55,0.5)', letterSpacing: '0.18em' }}
        >
          {locale === 'ru' ? 'Карты расклада — нажми для разбора' : 'Cards — tap for details'}
        </p>
        {spreadPositions.map((pos, i) => {
          const dc = cardByIndex(i);
          if (!dc) return null;
          const name = locale === 'ru' ? dc.card.name_ru : dc.card.name_en;
          const kws = (locale === 'ru' ? dc.card.keywords_ru : dc.card.keywords_en) ?? [];
          return (
            <button
              key={i}
              onClick={() => setSelectedCardIndex(i)}
              className="w-full text-left flex items-start gap-3 p-3 rounded-xl transition-colors hover:bg-[rgba(212,175,55,0.08)]"
              style={{ background: 'rgba(212,175,55,0.04)', border: '1px solid rgba(212,175,55,0.15)' }}
            >
              <span
                className="flex items-center justify-center font-serif shrink-0"
                style={{
                  width: 26, height: 26, borderRadius: 999,
                  background: 'rgba(212,175,55,0.12)', border: '1px solid rgba(212,175,55,0.3)',
                  color: '#d4af37', fontSize: '0.8rem',
                }}
              >
                {i + 1}
              </span>
              <span className="flex flex-col gap-0.5 min-w-0">
                <span className="font-sans text-[0.62rem] uppercase tracking-wider" style={{ color: 'rgba(201,194,224,0.5)', letterSpacing: '0.1em' }}>
                  {positionLabel(pos)}
                </span>
                <span className="font-serif text-sm" style={{ color: '#d4af37' }}>
                  {name}
                  {dc.is_reversed && (
                    <span style={{ color: 'rgba(201,194,224,0.5)', fontSize: '0.75rem' }}>
                      {' '}· {locale === 'ru' ? 'перевёрнута' : 'reversed'}
                    </span>
                  )}
                </span>
                {kws.length > 0 && (
                  <span className="font-sans text-xs" style={{ color: 'rgba(201,194,224,0.7)' }}>
                    {kws.slice(0, 3).join(' · ')}
                  </span>
                )}
              </span>
            </button>
          );
        })}
      </div>

      {/* Detail modal */}
      {selectedDrawnCard && selectedPos && (
        <CardDetailModal
          card={selectedDrawnCard.card}
          isReversed={selectedDrawnCard.is_reversed}
          positionLabel={locale === 'ru' ? selectedPos.label_ru : selectedPos.label_en}
          positionMeaning={locale === 'ru' ? selectedPos.meaning_ru : selectedPos.meaning_en}
          locale={locale}
          onClose={() => setSelectedCardIndex(null)}
        />
      )}
    </>
  );
}
