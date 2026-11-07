'use client';

import { useState } from 'react';
import { tapImpact } from '@/lib/haptics';

export type LoveSpread = 'feelings' | 'comeback' | 'together' | 'rival' | 'new-love';
export type RailSpread = 'three-card' | 'horseshoe' | 'nine-card' | 'free' | LoveSpread;

interface SpreadRailProps {
  locale: 'ru' | 'en';
  busy: RailSpread | null;
  onPick: (slug: RailSpread) => void;
  /** 'love' — the relationship spreads; 'general' — the classic ones. */
  group?: 'love' | 'general';
}

interface RailItem {
  slug: RailSpread;
  bars: number[]; // preview column heights, px
  ru: { name: string; desc: string; meta: string };
  en: { name: string; desc: string; meta: string };
}

export const LOVE_SPREADS: RailItem[] = [
  {
    slug: 'feelings',
    bars: [26, 32, 38, 32, 26],
    ru: { name: 'Как он ко мне относится', desc: 'Мысли, чувства и то, что он пока не говорит', meta: '5 карт · 3 мин' },
    en: { name: 'How they feel about me', desc: 'Thoughts, feelings and what they are not saying yet', meta: '5 cards · 3 min' },
  },
  {
    slug: 'comeback',
    bars: [36, 28, 20, 28, 36],
    ru: { name: 'Вернётся ли он', desc: 'Почему всё остановилось и есть ли путь назад', meta: '5 карт · 3 мин' },
    en: { name: 'Will they come back', desc: 'Why it stopped and whether there is a way back', meta: '5 cards · 3 min' },
  },
  {
    slug: 'together',
    bars: [30, 30, 38, 22, 34],
    ru: { name: 'Будем ли мы вместе', desc: 'Ты, он и то, что между вами', meta: '5 карт · 3 мин' },
    en: { name: 'Will we be together', desc: 'You, them and what lies between you', meta: '5 cards · 3 min' },
  },
  {
    slug: 'rival',
    bars: [30, 22, 30, 38],
    ru: { name: 'Есть ли у него другая', desc: 'Где его внимание и что происходит на самом деле', meta: '4 карты · 3 мин' },
    en: { name: 'Is there someone else', desc: 'Where their attention is and what is really going on', meta: '4 cards · 3 min' },
  },
  {
    slug: 'new-love',
    bars: [24, 32, 38, 30],
    ru: { name: 'Новое знакомство', desc: 'Кто он, чего хочет и стоит ли продолжать', meta: '4 карты · 3 мин' },
    en: { name: 'A new connection', desc: 'Who they are, what they want, whether to go on', meta: '4 cards · 3 min' },
  },
];

const GENERAL_SPREADS: RailItem[] = [
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

const TITLES = {
  love: { ru: 'Про отношения', en: 'Love & relationships' },
  general: { ru: 'Расклады', en: 'Spreads' },
} as const;

/** Horizontal rail of spreads. Picking one starts it with the question above. */
export default function SpreadRail({ locale, busy, onPick, group = 'general' }: SpreadRailProps) {
  const [hovered, setHovered] = useState<RailSpread | null>(null);
  const items = group === 'love' ? LOVE_SPREADS : GENERAL_SPREADS;
  const love = group === 'love';

  return (
    <section style={{ paddingTop: 30 }}>
      <div className="flex items-baseline justify-between" style={{ padding: '0 18px' }}>
        <h2 className="font-serif" style={{ fontSize: 22 }}>
          {TITLES[group][locale]}
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
          {items.length} {locale === 'ru' ? 'шт' : 'total'}
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
        {items.map((s) => {
          const t = s[locale];
          const active = hovered === s.slug || busy === s.slug;
          return (
            <button
              key={s.slug}
              type="button"
              onClick={() => { tapImpact('light'); onPick(s.slug); }}
              onPointerEnter={() => setHovered(s.slug)}
              onPointerLeave={() => setHovered(null)}
              disabled={busy !== null}
              className="text-left flex flex-col active:scale-[.97]"
              style={{
                flex: '0 0 63%',
                scrollSnapAlign: 'start',
                padding: 16,
                borderRadius: 16,
                background: love
                  ? 'radial-gradient(220px 140px at 100% 0%, rgba(214,120,150,.16), transparent 70%), linear-gradient(180deg,#151019,#0C0A11)'
                  : 'linear-gradient(180deg,#131019,#0C0A11)',
                border: `1px solid ${active ? 'var(--accent)' : love ? 'rgba(214,140,160,.22)' : 'rgba(255,255,255,.10)'}`,
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
                      border: `1px solid ${love ? 'rgba(230,160,175,.5)' : 'rgba(224,178,108,.45)'}`,
                    }}
                  />
                ))}
              </div>
              <span className="font-serif" style={{ fontSize: 19, marginTop: 14, lineHeight: 1.15 }}>{t.name}</span>
              <span style={{ fontSize: 13, color: '#9A94A6', marginTop: 4, lineHeight: 1.4 }}>{t.desc}</span>
              <span className="flex items-center justify-between" style={{ marginTop: 'auto', paddingTop: 16 }}>
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
