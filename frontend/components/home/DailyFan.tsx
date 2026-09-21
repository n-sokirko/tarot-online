'use client';

import { useEffect, useState } from 'react';
import type { DailyCardResponse } from '@/lib/api';
import { roman } from './roman';

interface DailyFanProps {
  locale: 'ru' | 'en';
  /** Fetched by the page: the share card below uses the same card. */
  daily: DailyCardResponse | null;
  flipped: boolean;
  onFlip: (next: boolean) => void;
  /** Bumped by "Перетасовать" in the question block — each bump plays one shuffle. */
  shuffleSignal: number;
  /** Called the first time the card is turned face up today. */
  onOpened: () => void;
}

const L = {
  ru: { title: 'Карта дня', open: 'открыть', hide: 'скрыть', shuffling: 'тасую…', back: 'рубашка' },
  en: { title: 'Card of the day', open: 'open', hide: 'hide', shuffling: 'shuffling…', back: 'card back' },
} as const;

const MONO: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '10.5px',
  letterSpacing: '.16em',
  textTransform: 'uppercase',
};

/**
 * Card of the day as a 3D fan: two card backs either side and the day's card
 * in the middle, which turns over on tap. The card itself is real — the same
 * deterministic one /api/v1/cards/daily/ serves — so the ritual means something.
 */
export default function DailyFan({ locale, daily, flipped, onFlip, shuffleSignal, onOpened }: DailyFanProps) {
  const t = L[locale];
  const [shuffling, setShuffling] = useState(false);

  // One shuffle per signal. Face down first, so the shuffle has something to
  // hide; the animation length is the design's 1.05s.
  useEffect(() => {
    if (shuffleSignal === 0) return;
    onFlip(false);
    setShuffling(true);
    const timer = setTimeout(() => setShuffling(false), 1050);
    return () => clearTimeout(timer);
  }, [shuffleSignal]);

  const toggle = () => {
    if (shuffling) return;
    const next = !flipped;
    onFlip(next);
    if (next) onOpened();
  };

  const card = daily?.card;
  const name = card ? (locale === 'ru' ? card.name_ru : card.name_en) : '';
  const keywords = card ? (locale === 'ru' ? card.keywords_ru : card.keywords_en) : [];
  const hint = shuffling ? t.shuffling : flipped ? t.hide : t.open;

  return (
    <section style={{ padding: '26px 18px 0' }}>
      <div className="flex items-baseline justify-between" style={{ marginBottom: 12 }}>
        <span style={{ ...MONO, color: '#8E879B' }}>{t.title}</span>
        <span style={{ fontSize: '12.5px', color: 'var(--accent)' }}>{hint}</span>
      </div>

      <button
        type="button"
        onClick={toggle}
        aria-pressed={flipped}
        aria-label={flipped ? `${t.title}: ${name}` : t.title}
        className="relative block w-full"
        style={{ aspectRatio: '4 / 3', perspective: 1100, background: 'none', border: 0, cursor: 'pointer' }}
      >
        <div
          className="relative w-full h-full"
          style={{
            transformStyle: 'preserve-3d',
            animation: shuffling ? 'shuf 1.05s var(--ease-shuffle)' : undefined,
          }}
        >
          {/* Side backs: violet hatching on the left, gold on the right. */}
          {[-1, 1].map((side) => (
            <div
              key={side}
              aria-hidden
              className="absolute"
              style={{
                width: '40%',
                aspectRatio: '2 / 3',
                top: '50%',
                left: '50%',
                borderRadius: 13,
                border: '1px solid rgba(255,255,255,.10)',
                boxShadow: '0 30px 50px -26px #000',
                background: `repeating-linear-gradient(${side < 0 ? 46 : -46}deg, ${
                  side < 0 ? 'rgba(182,167,240,.13)' : 'rgba(224,178,108,.13)'
                } 0 2px, transparent 2px 9px), linear-gradient(180deg,#131019,#0C0A11)`,
                transform: `translate(-50%,-50%) translateX(${side * 58}%) rotate(${side * 13}deg) translateZ(calc(14px * var(--depth)))`,
              }}
            />
          ))}

          {/* The day's card: two faces, turned with rotateY. */}
          <div
            className="absolute"
            style={{
              width: '44%',
              aspectRatio: '2 / 3',
              top: '50%',
              left: '50%',
              transformStyle: 'preserve-3d',
              transition: 'transform var(--dur) var(--ease-flip)',
              transform: `translate(-50%,-50%) translateZ(calc(70px * var(--depth))) rotateY(${flipped ? 180 : 0}deg)`,
            }}
          >
            {/* Back */}
            <div
              className="absolute inset-0 flex items-center justify-center"
              style={{
                backfaceVisibility: 'hidden',
                borderRadius: 13,
                border: '1px solid rgba(224,178,108,.34)',
                background: 'linear-gradient(180deg,#1E1830,#0E0C14)',
                boxShadow: '0 30px 50px -26px #000',
              }}
            >
              <span
                aria-hidden
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: '50%',
                  border: '1px solid rgba(224,178,108,.5)',
                  animation: 'breathe 4.5s ease-in-out infinite',
                }}
              />
            </div>

            {/* Face */}
            <div
              className="absolute inset-0 flex flex-col"
              style={{
                backfaceVisibility: 'hidden',
                transform: 'rotateY(180deg)',
                borderRadius: 13,
                border: '1px solid var(--accent)',
                background: 'linear-gradient(180deg,#1E1830,#0E0C14)',
                padding: 9,
                gap: 6,
                boxShadow: '0 30px 50px -26px #000',
              }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10.5px', color: 'var(--accent)' }}>
                {roman(card?.number)}
              </span>
              <div
                className="relative flex-1 overflow-hidden"
                style={{
                  borderRadius: 8,
                  transform: daily?.is_reversed ? 'rotate(180deg)' : undefined,
                  background: 'repeating-linear-gradient(135deg, rgba(255,255,255,.06) 0 6px, rgba(255,255,255,.08) 6px 12px)',
                }}
              >
                {card?.image_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={card.image_url} alt={name} className="absolute inset-0 w-full h-full object-cover" />
                )}
              </div>
              <span className="font-serif" style={{ fontSize: 17, lineHeight: 1.1, color: 'var(--ink)' }}>
                {name}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#8E879B' }}>
                {keywords.slice(0, 2).join(' · ')}
              </span>
            </div>
          </div>
        </div>
      </button>
    </section>
  );
}
