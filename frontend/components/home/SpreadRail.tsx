'use client';

import { useState } from 'react';

export type RailSpread = 'three-card' | 'horseshoe' | 'nine-card' | 'free';

interface SpreadRailProps {
  locale: 'ru' | 'en';
  busy: RailSpread | null;
  onPick: (slug: RailSpread) => void;
}

const SPREADS: {
  slug: RailSpread;
  bars: number[]; // preview column heights, px
  ru: { name: string; desc: string; meta: string };
  en: { name: string; desc: string; meta: string };
}[] = [
  {
    slug: 'three-card',
    bars: [30, 30, 30],
    ru: { name: 'Три карты', desc: 'Прошлое · Настоящее · Будущее', meta: '3 карты · 2 мин' },
    en: { name: 'Three cards', desc: 'Past · Present · Future', meta: '3 cards · 2 min' },
  },
  {
    slug: 'horseshoe',
    bars: [18, 28, 36, 28, 18],
    ru: { name: 'Подкова', desc: 'Скрытое, препятствие и исход', meta: '5 карт · 4 мин' },
    en: { name: 'Horseshoe', desc: 'The hidden, the obstacle, the outcome', meta: '5 cards · 4 min' },
  },
  {
    slug: 'nine-card',
    bars: [30, 30, 30, 30, 30, 30],
    ru: { name: 'Девять карт', desc: 'Полный разбор ситуации', meta: '9 карт · 8 мин' },
    en: { name: 'Nine cards', desc: 'The whole situation, in full', meta: '9 cards · 8 min' },
  },
  {
    slug: 'free',
    bars: [22, 34, 16, 28],
    ru: { name: 'Свой расклад', desc: 'Раскладываешь как хочешь, позиции подписываешь сам', meta: 'до 10 карт' },
    en: { name: 'Your own spread', desc: 'Lay it out your way, name the positions yourself', meta: 'up to 10 cards' },
  },
];

/** Horizontal rail of spreads. Picking one starts it with the question above. */
export default function SpreadRail({ locale, busy, onPick }: SpreadRailProps) {
  const [hovered, setHovered] = useState<RailSpread | null>(null);

  return (
    <section style={{ paddingTop: 30 }}>
      <div className="flex items-baseline justify-between" style={{ padding: '0 18px' }}>
        <h2 className="font-serif" style={{ fontSize: 22 }}>
          {locale === 'ru' ? 'Расклады' : 'Spreads'}
        </h2>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '10.5px',
            letterSpacing: '.16em',
            textTransform: 'uppercase',
            color: '#8E879B',
          }}
        >
          {SPREADS.length} {locale === 'ru' ? 'шт' : 'total'}
        </span>
      </div>

      <div
        className="flex overflow-x-auto"
        style={{
          gap: 12,
          padding: '6px 18px 18px',
          scrollSnapType: 'x mandatory',
          perspective: 900,
          scrollbarWidth: 'none',
        }}
      >
        {SPREADS.map((s) => {
          const t = s[locale];
          const active = hovered === s.slug || busy === s.slug;
          return (
            <button
              key={s.slug}
              type="button"
              onClick={() => onPick(s.slug)}
              onPointerEnter={() => setHovered(s.slug)}
              onPointerLeave={() => setHovered(null)}
              disabled={busy !== null}
              className="text-left flex flex-col"
              style={{
                flex: '0 0 63%',
                scrollSnapAlign: 'start',
                padding: 16,
                borderRadius: 16,
                background: 'linear-gradient(180deg,#131019,#0C0A11)',
                border: `1px solid ${active ? 'var(--accent)' : 'rgba(255,255,255,.10)'}`,
                transition: 'transform var(--dur) var(--ease), border-color 300ms',
                transform: active
                  ? 'rotateY(-9deg) rotateX(5deg) translateZ(calc(26px * var(--depth)))'
                  : 'none',
                minHeight: 48,
              }}
            >
              <div className="flex items-end" style={{ gap: 5, height: 40 }} aria-hidden>
                {s.bars.map((h, i) => (
                  <span
                    key={i}
                    style={{
                      width: 20,
                      height: h,
                      borderRadius: 4,
                      border: '1px solid rgba(224,178,108,.45)',
                    }}
                  />
                ))}
              </div>
              <span className="font-serif" style={{ fontSize: 19, marginTop: 14 }}>{t.name}</span>
              <span style={{ fontSize: 13, color: '#9A94A6', marginTop: 4, lineHeight: 1.4 }}>{t.desc}</span>
              <span className="flex items-center justify-between" style={{ marginTop: 16 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10.5px', color: '#8E879B' }}>
                  {busy === s.slug ? (locale === 'ru' ? 'готовлю…' : 'preparing…') : t.meta}
                </span>
                <span style={{ color: 'var(--accent)' }}>→</span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
