'use client';

import { useEffect, useState } from 'react';
import { dateLine } from '@/lib/moon';
import { selectionTick, tapImpact } from '@/lib/haptics';
import type { RailSpread } from './SpreadRail';

interface QuestionBlockProps {
  locale: 'ru' | 'en';
  question: string;
  onQuestion: (q: string) => void;
  onShuffle: () => void;
  /** True while the reading is being created. */
  busy?: boolean;
  /** The topic chip that is selected, if any. */
  topic: TopicKey | null;
  onTopic: (topic: TopicKey | null) => void;
}

export const QUESTION_LIMIT = 180;

export type TopicKey = 'thinks' | 'back' | 'together' | 'rival' | 'new' | 'work' | 'money';

/** Ready-made questions: a tap fills the question and picks the matching spread. */
export const TOPICS: {
  key: TopicKey;
  spread: RailSpread;
  ru: { chip: string; q: string; spread: string };
  en: { chip: string; q: string; spread: string };
}[] = [
  { key: 'thinks', spread: 'feelings',
    ru: { chip: '💭 Что он думает обо мне', q: 'Что он думает обо мне и как ко мне относится?', spread: 'Как он ко мне относится · 5 карт' },
    en: { chip: '💭 What do they think of me', q: 'What do they think of me and how do they feel?', spread: 'How they feel about me · 5 cards' } },
  { key: 'back', spread: 'comeback',
    ru: { chip: '🔁 Вернётся ли он', q: 'Вернётся ли он ко мне?', spread: 'Вернётся ли он · 5 карт' },
    en: { chip: '🔁 Will they come back', q: 'Will they come back to me?', spread: 'Will they come back · 5 cards' } },
  { key: 'together', spread: 'together',
    ru: { chip: '💞 Будем ли вместе', q: 'Есть ли у нас с ним будущее?', spread: 'Будем ли мы вместе · 5 карт' },
    en: { chip: '💞 Will we be together', q: 'Do we have a future together?', spread: 'Will we be together · 5 cards' } },
  { key: 'rival', spread: 'rival',
    ru: { chip: '🥀 Есть ли другая', q: 'Есть ли у него кто-то другой?', spread: 'Есть ли у него другая · 4 карты' },
    en: { chip: '🥀 Someone else?', q: 'Is there someone else in their life?', spread: 'Is there someone else · 4 cards' } },
  { key: 'new', spread: 'new-love',
    ru: { chip: '✨ Новое знакомство', q: 'Что ждёт меня с новым человеком?', spread: 'Новое знакомство · 4 карты' },
    en: { chip: '✨ Someone new', q: 'What awaits me with this new person?', spread: 'A new connection · 4 cards' } },
  { key: 'work', spread: 'three-card',
    ru: { chip: '💼 Работа', q: 'Что меня ждёт в работе в ближайший месяц?', spread: 'Три карты · 3 карты' },
    en: { chip: '💼 Work', q: 'What awaits me at work this month?', spread: 'Three cards · 3 cards' } },
  { key: 'money', spread: 'three-card',
    ru: { chip: '💰 Деньги', q: 'Как мне улучшить своё финансовое положение?', spread: 'Три карты · 3 карты' },
    en: { chip: '💰 Money', q: 'How can I improve my finances?', spread: 'Three cards · 3 cards' } },
];

const L = {
  ru: {
    title: 'Что сейчас требует внимания?',
    lead: 'Опиши ситуацию своими словами — или выбери тему ниже.',
    placeholder: 'например: почему я тяну с решением о работе',
    shuffle: 'Перетасовать',
    lay: 'Разложить',
    busy: 'Тасую…',
    spread: 'Расклад',
    topics: 'Частые вопросы',
  },
  en: {
    title: 'What needs your attention right now?',
    lead: 'Describe it in your own words — or pick a topic below.',
    placeholder: "e.g. why I keep putting off the decision about work",
    shuffle: 'Shuffle',
    lay: 'Lay out',
    busy: 'Shuffling…',
    spread: 'Spread',
    topics: 'Popular questions',
  },
} as const;

// Cards the floating hero card turns over to, one after another.
const HERO = ['the-star', 'the-moon', 'the-sun', 'the-lovers', 'wheel-of-fortune', 'the-high-priestess', 'the-empress', 'the-world'];

/** A small card that floats beside the title and turns over every few seconds. */
function HeroCard() {
  const [k, setK] = useState(0);
  const [face, setFace] = useState(false);
  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
    const id = setInterval(() => {
      setFace((f) => {
        if (f) setK((n) => (n + 1) % HERO.length);
        return !f;
      });
    }, 2600);
    return () => clearInterval(id);
  }, []);
  return (
    <div
      aria-hidden
      className="absolute pointer-events-none"
      style={{ right: 18, top: 36, width: 74, aspectRatio: '2 / 3', perspective: 600, animation: 'heroFloat 5s ease-in-out infinite' }}
    >
      <div
        className="absolute"
        style={{ inset: -26, borderRadius: '50%', background: 'radial-gradient(circle, rgba(224,178,108,.32), transparent 68%)' }}
      />
      <div
        className="absolute inset-0"
        style={{
          transformStyle: 'preserve-3d', transition: 'transform 900ms var(--ease-flip)',
          transform: `rotateY(${face ? 180 : 0}deg)`,
        }}
      >
        <div
          className="absolute inset-0 flex items-center justify-center"
          style={{
            backfaceVisibility: 'hidden', borderRadius: 9, border: '1px solid rgba(224,178,108,.6)',
            background: 'radial-gradient(circle, rgba(224,178,108,.22), transparent 50%), repeating-linear-gradient(45deg, rgba(224,178,108,.08) 0 2px, transparent 2px 7px), linear-gradient(180deg,#1E1830,#0E0C14)',
            boxShadow: '0 14px 30px -12px #000',
          }}
        >
          <span style={{ color: 'var(--accent)', fontSize: 16, textShadow: '0 0 10px rgba(224,178,108,.8)' }}>✦</span>
        </div>
        <div
          className="absolute inset-0 overflow-hidden"
          style={{
            backfaceVisibility: 'hidden', transform: 'rotateY(180deg)', borderRadius: 9,
            border: '1px solid var(--accent)', boxShadow: '0 0 22px -4px rgba(224,178,108,.65)', background: '#0E0C14',
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`/cards/major/${HERO[k]}.jpg`} alt="" className="absolute inset-0 w-full h-full object-cover" />
        </div>
      </div>
    </div>
  );
}

/** The question comes first: the reading is about the person's situation. */
export default function QuestionBlock({
  locale, question, onQuestion, onShuffle, busy = false, topic, onTopic,
}: QuestionBlockProps) {
  const t = L[locale];
  const current = TOPICS.find((x) => x.key === topic);

  const choose = (key: TopicKey) => {
    selectionTick();
    if (key === topic) {
      onTopic(null);
      return;
    }
    const tp = TOPICS.find((x) => x.key === key)!;
    onTopic(key);
    onQuestion(tp[locale].q);
  };

  return (
    <section className="relative" style={{ padding: '22px 18px 0' }}>
      <HeroCard />
      <p
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '10.5px',
          letterSpacing: '.16em',
          textTransform: 'uppercase',
          color: '#8E879B',
        }}
      >
        {dateLine(locale)}
      </p>
      <h1
        className="font-serif"
        style={{ fontSize: 34, lineHeight: 1.08, marginTop: 12, paddingRight: 92, textWrap: 'pretty' } as React.CSSProperties}
      >
        {t.title}
      </h1>
      <p style={{ fontSize: '14.5px', lineHeight: 1.55, color: '#A49DAF', marginTop: 12, paddingRight: 70 }}>{t.lead}</p>

      <div
        style={{
          marginTop: 16,
          border: `1px solid ${current ? 'rgba(224,178,108,.45)' : 'rgba(255,255,255,.12)'}`,
          borderRadius: 16,
          background: 'rgba(255,255,255,.035)',
          padding: '14px 14px 10px',
          transition: 'border-color 300ms',
        }}
      >
        <textarea
          rows={2}
          value={question}
          maxLength={QUESTION_LIMIT}
          onChange={(e) => onQuestion(e.target.value.slice(0, QUESTION_LIMIT))}
          placeholder={t.placeholder}
          aria-label={t.title}
          className="w-full bg-transparent outline-none resize-none placeholder:text-[#6F6A7C]"
          style={{ fontSize: 15, lineHeight: 1.45, border: 0, color: 'var(--ink)' }}
        />
        <div className="flex items-center justify-between" style={{ marginTop: 6, gap: 10 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10.5px', color: current ? 'var(--accent)' : '#6F6A7C', lineHeight: 1.4 }}>
            {current ? `${t.spread}: ${current[locale].spread}` : `${question.length}/${QUESTION_LIMIT}`}
          </span>
          <button
            type="button"
            onClick={() => { tapImpact('medium'); onShuffle(); }}
            disabled={busy}
            aria-busy={busy}
            className="transition-transform hover:-translate-y-0.5 hover:scale-[1.02] active:scale-[.96]"
            style={{
              flex: 'none',
              background: 'var(--accent)',
              color: '#0B0A0F',
              fontSize: 14,
              fontWeight: 700,
              padding: '11px 18px',
              borderRadius: 999,
              boxShadow: '0 14px 30px -14px rgba(224,178,108,.9)',
              transitionDuration: '300ms',
              transitionTimingFunction: 'cubic-bezier(.2,.8,.2,1)',
              minHeight: 44,
              opacity: busy ? .7 : 1,
            }}
          >
            {busy ? t.busy : current ? t.lay : t.shuffle}
          </button>
        </div>
      </div>

      <p
        style={{
          fontFamily: 'var(--font-mono)', fontSize: '10.5px', letterSpacing: '.16em', textTransform: 'uppercase',
          color: '#8E879B', marginTop: 16,
        }}
      >
        {t.topics}
      </p>
      <div
        className="flex overflow-x-auto"
        style={{ gap: 8, margin: '10px -18px 0', padding: '0 18px 4px', scrollbarWidth: 'none' }}
      >
        {TOPICS.map((tp) => {
          const on = tp.key === topic;
          return (
            <button
              key={tp.key}
              type="button"
              onClick={() => choose(tp.key)}
              aria-pressed={on}
              className="active:scale-[.95]"
              style={{
                flex: 'none', fontSize: 13.5, padding: '9px 14px', borderRadius: 999, whiteSpace: 'nowrap', minHeight: 40,
                color: on ? '#0B0A0F' : 'var(--ink)',
                background: on ? 'var(--accent)' : 'rgba(255,255,255,.05)',
                border: `1px solid ${on ? 'var(--accent)' : 'rgba(255,255,255,.12)'}`,
                transition: 'background 250ms, color 250ms, transform 150ms',
              }}
            >
              {tp[locale].chip}
            </button>
          );
        })}
      </div>
    </section>
  );
}
