'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import type { DailyCardResponse } from '@/lib/api';
import { notify, tapImpact } from '@/lib/haptics';
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
  ru: { title: 'Карта дня', pick: 'выбери карту', shuffling: 'тасую…', again: 'нажми, чтобы спрятать', card: 'карта' },
  en: { title: 'Card of the day', pick: 'pick a card', shuffling: 'shuffling…', again: 'tap to hide', card: 'card' },
} as const;

const MONO: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '10.5px',
  letterSpacing: '.16em',
  textTransform: 'uppercase',
};

// Fan geometry, as fractions of the stage width (the stage is 4:3).
const N = 7;
const SPREAD_DEG = 7.5;       // angle between neighbours
const CARD_W = 0.24;          // fan card width
const CARD_H = CARD_W * 1.5;
const ORIGIN = 2.6;           // pivot below the card, in card heights
const TOP = 0.12;             // fan card top
const BIG = 1.85;             // picked card scale
const STAGE_H = 0.75;

const angle = (i: number) => (i - (N - 1) / 2) * SPREAD_DEG;

const BACK: React.CSSProperties = {
  borderRadius: 12,
  border: '1px solid rgba(224,178,108,.55)',
  background:
    'radial-gradient(circle at 50% 50%, rgba(224,178,108,.22), transparent 46%),' +
    'repeating-linear-gradient(45deg, rgba(224,178,108,.08) 0 2px, transparent 2px 8px),' +
    'linear-gradient(180deg,#1E1830,#0E0C14)',
  boxShadow: '0 18px 36px -18px #000, inset 0 0 0 4px rgba(14,12,20,.9), inset 0 0 0 5px rgba(224,178,108,.35)',
};

function BackFace() {
  return (
    <div className="absolute inset-0 flex items-center justify-center" style={{ ...BACK, backfaceVisibility: 'hidden' }}>
      <span aria-hidden style={{ color: 'var(--accent)', fontSize: 22, textShadow: '0 0 14px rgba(224,178,108,.8)' }}>✦</span>
    </div>
  );
}

/**
 * Card of the day as a fan the person draws from: tap a card — it rises,
 * flies to the middle and turns over with a gold glow. The card itself is
 * real — the same deterministic one /api/v1/cards/daily/ serves — so whichever
 * back is tapped, the ritual shows today's card. Haptics tick inside Telegram.
 */
export default function DailyFan({ locale, daily, flipped, onFlip, shuffleSignal, onOpened }: DailyFanProps) {
  const t = L[locale];
  const reduce = useReducedMotion();
  const stage = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(360);
  const [picked, setPicked] = useState<number | null>(null);
  const [shuffling, setShuffling] = useState(false);

  useEffect(() => {
    const el = stage.current;
    if (!el) return;
    setWidth(el.clientWidth || 360);
    const ro = new ResizeObserver(() => setWidth(el.clientWidth || 360));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // One shuffle per signal: the card goes back into the fan.
  useEffect(() => {
    if (shuffleSignal === 0) return;
    onFlip(false);
    setPicked(null);
    setShuffling(true);
    const timer = setTimeout(() => setShuffling(false), 1050);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shuffleSignal]);

  // Turned face down ("hide" or a shuffle) → back to the fan.
  useEffect(() => { if (!flipped) setPicked(null); }, [flipped]);

  const choose = (i: number) => {
    if (shuffling || picked !== null || flipped) return;
    tapImpact('medium');
    setPicked(i);
    setTimeout(() => {
      onFlip(true);
      onOpened();
      notify('success');
    }, reduce ? 0 : 620);
  };

  const hide = () => {
    if (!flipped) return;
    tapImpact('light');
    onFlip(false);
  };

  const card = daily?.card;
  const name = card ? (locale === 'ru' ? card.name_ru : card.name_en) : '';
  const keywords = card ? (locale === 'ru' ? card.keywords_ru : card.keywords_en) : [];
  const showBig = picked !== null || flipped;
  const hint = shuffling ? t.shuffling : flipped ? t.again : t.pick;

  // Where fan card i sits, relative to the spot of the big card (stage centre).
  const W = width, h = CARD_H * W, pivot = (ORIGIN - 0.5) * h;
  const from = (i: number) => {
    const a = (angle(i) * Math.PI) / 180;
    const fanCy = TOP * W + h / 2 + pivot - Math.cos(a) * pivot;
    return { x: Math.sin(a) * pivot, y: fanCy - (STAGE_H * W) / 2, rotate: angle(i) };
  };
  const start = picked !== null ? from(picked) : { x: 0, y: 0, rotate: 0 };
  const dur = reduce ? 0 : 1;

  return (
    <section style={{ padding: '26px 18px 0' }}>
      <div className="flex items-baseline justify-between" style={{ marginBottom: 12 }}>
        <span style={{ ...MONO, color: '#8E879B' }}>{t.title}</span>
        <span style={{ fontSize: '12.5px', color: 'var(--accent)' }}>{hint}</span>
      </div>

      <div
        ref={stage}
        className="relative block w-full"
        style={{ aspectRatio: '4 / 3', perspective: 1100 }}
      >
        <div className="absolute inset-0" style={{ animation: shuffling ? 'shuf 1.05s var(--ease-shuffle)' : undefined }}>
          {/* The fan */}
          {Array.from({ length: N }, (_, i) => {
            const isPicked = picked === i;
            return (
              <motion.button
                key={i}
                type="button"
                aria-label={`${t.pick}: ${t.card} ${i + 1}`}
                onClick={() => choose(i)}
                disabled={showBig}
                initial={false}
                animate={{
                  rotate: angle(i),
                  y: showBig ? (isPicked ? 0 : 46) : 0,
                  opacity: showBig ? 0 : 1,
                }}
                transition={{
                  duration: .38 * dur,
                  delay: showBig && !isPicked ? Math.abs(i - (picked ?? 3)) * .035 * dur : 0,
                }}
                whileTap={{ y: -16 }}
                className="absolute"
                style={{
                  left: `${(0.5 - CARD_W / 2) * 100}%`, top: `${(TOP / STAGE_H) * 100}%`, width: `${CARD_W * 100}%`,
                  aspectRatio: '2 / 3', transformOrigin: `50% ${ORIGIN * 100}%`, background: 'none', border: 0, padding: 0,
                  cursor: 'pointer', pointerEvents: showBig ? 'none' : 'auto',
                }}
              >
                <span
                  className="absolute inset-0"
                  style={{ animation: showBig || reduce ? undefined : `fanBreathe 3.4s ease-in-out ${i * .2}s infinite` }}
                >
                  <BackFace />
                </span>
              </motion.button>
            );
          })}

          {/* The picked card: flies out of the fan and turns over. */}
          {showBig && (
            <motion.button
              type="button"
              key={`big-${picked ?? 'open'}`}
              onClick={hide}
              aria-pressed={flipped}
              aria-label={flipped ? `${t.title}: ${name}` : t.title}
              className="absolute"
              initial={picked !== null && !flipped ? { ...start, scale: 1 } : false}
              animate={{ x: 0, y: 0, rotate: 0, scale: BIG }}
              transition={reduce ? { duration: 0 } : { type: 'spring', stiffness: 170, damping: 21 }}
              style={{
                left: `${(0.5 - CARD_W / 2) * 100}%`, top: `${(0.5 - CARD_H / STAGE_H / 2) * 100}%`, width: `${CARD_W * 100}%`,
                aspectRatio: '2 / 3', transformStyle: 'preserve-3d', zIndex: 2, background: 'none', border: 0, padding: 0,
                cursor: flipped ? 'pointer' : 'default',
              }}
            >
              {/* gold burst behind the reveal */}
              <motion.div
                aria-hidden
                className="absolute"
                initial={{ opacity: 0, scale: .6 }}
                animate={flipped ? { opacity: [0, 1, .4], scale: [.6, 1.35, 1.15] } : { opacity: 0, scale: .6 }}
                transition={{ duration: .9 * dur, times: [0, .35, 1] }}
                style={{
                  inset: '-32%', borderRadius: '50%', zIndex: -1, pointerEvents: 'none',
                  background: 'radial-gradient(circle, rgba(224,178,108,.5), rgba(224,178,108,0) 65%)',
                }}
              />
              <motion.div
                className="absolute inset-0"
                initial={false}
                animate={{ rotateY: flipped ? 180 : 0 }}
                transition={{ duration: .7 * dur, ease: [.3, .9, .2, 1] }}
                style={{ transformStyle: 'preserve-3d' }}
              >
                <BackFace />
                <div
                  className="absolute inset-0 flex flex-col text-left"
                  style={{
                    backfaceVisibility: 'hidden', transform: 'rotateY(180deg)', borderRadius: 9,
                    border: '1px solid var(--accent)', background: 'linear-gradient(180deg,#1E1830,#0E0C14)',
                    padding: 5, gap: 3, boxShadow: '0 0 26px -6px rgba(224,178,108,.7)',
                  }}
                >
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 6.5, color: 'var(--accent)' }}>{roman(card?.number)}</span>
                  <div
                    className="relative flex-1 overflow-hidden"
                    style={{
                      borderRadius: 5,
                      transform: daily?.is_reversed ? 'rotate(180deg)' : undefined,
                      background: 'repeating-linear-gradient(135deg, rgba(255,255,255,.06) 0 6px, rgba(255,255,255,.08) 6px 12px)',
                    }}
                  >
                    {card?.image_url && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={card.image_url} alt={name} className="absolute inset-0 w-full h-full object-cover" />
                    )}
                  </div>
                  <span className="font-serif" style={{ fontSize: 10.5, lineHeight: 1.1, color: 'var(--ink)' }}>{name}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 5.6, color: '#8E879B' }}>{keywords.slice(0, 2).join(' · ')}</span>
                </div>
              </motion.div>
            </motion.button>
          )}
        </div>
      </div>
    </section>
  );
}
