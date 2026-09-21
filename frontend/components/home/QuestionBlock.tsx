'use client';

import { dateLine } from '@/lib/moon';

interface QuestionBlockProps {
  locale: 'ru' | 'en';
  question: string;
  onQuestion: (q: string) => void;
  onShuffle: () => void;
}

export const QUESTION_LIMIT = 180;

const L = {
  ru: {
    title: 'Что сейчас требует внимания?',
    lead: 'Опиши ситуацию своими словами — разбор будет про тебя, а не про абстрактные значения карт.',
    placeholder: 'например: почему я тяну с решением о работе',
    shuffle: 'Перетасовать',
  },
  en: {
    title: 'What needs your attention right now?',
    lead: 'Describe it in your own words — the reading will be about you, not about abstract card meanings.',
    placeholder: "e.g. why I keep putting off the decision about work",
    shuffle: 'Shuffle',
  },
} as const;

/** The question comes first: the reading is about the person's situation. */
export default function QuestionBlock({ locale, question, onQuestion, onShuffle }: QuestionBlockProps) {
  const t = L[locale];
  return (
    <section style={{ padding: '22px 18px 0' }}>
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
        style={{ fontSize: 34, lineHeight: 1.08, marginTop: 12, textWrap: 'pretty' } as React.CSSProperties}
      >
        {t.title}
      </h1>
      <p style={{ fontSize: '14.5px', lineHeight: 1.55, color: '#A49DAF', marginTop: 12 }}>{t.lead}</p>

      <div
        style={{
          marginTop: 16,
          border: '1px solid rgba(255,255,255,.12)',
          borderRadius: 16,
          background: 'rgba(255,255,255,.035)',
          padding: '14px 14px 10px',
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
        <div className="flex items-center justify-between" style={{ marginTop: 6 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10.5px', color: '#6F6A7C' }}>
            {question.length}/{QUESTION_LIMIT}
          </span>
          <button
            type="button"
            onClick={onShuffle}
            className="transition-transform hover:-translate-y-0.5 hover:scale-[1.02]"
            style={{
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
            }}
          >
            {t.shuffle}
          </button>
        </div>
      </div>
    </section>
  );
}
