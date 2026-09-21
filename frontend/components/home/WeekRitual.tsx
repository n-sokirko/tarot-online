'use client';

import type { RitualState } from '@/lib/api';

const L = {
  ru: {
    title: 'Ритуал недели',
    keep: 'не прерывай',
    days: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
    todo: 'Сегодня осталось вытянуть карту дня — это 40 секунд.',
    done: 'Сегодня карта уже открыта. До завтра.',
  },
  en: {
    title: 'This week',
    keep: "don't break it",
    days: ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'],
    todo: "Today's card is still waiting — it takes 40 seconds.",
    done: "Today's card is open. See you tomorrow.",
  },
} as const;

const MONO: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '10.5px',
  letterSpacing: '.16em',
  textTransform: 'uppercase',
  color: '#8E879B',
};

export default function WeekRitual({ locale, ritual }: { locale: 'ru' | 'en'; ritual: RitualState }) {
  const t = L[locale];
  return (
    <section style={{ padding: '26px 18px 0' }}>
      <div
        className="reveal-3d"
        style={{
          border: '1px solid rgba(255,255,255,.10)',
          borderRadius: 18,
          background: 'linear-gradient(180deg,#121019,#0C0A11)',
          padding: 18,
        }}
      >
        <div className="flex items-baseline justify-between">
          <span style={MONO}>{t.title}</span>
          <span style={{ fontSize: '12.5px', color: '#8FD3C4' }}>{t.keep}</span>
        </div>

        <div className="grid" style={{ gridTemplateColumns: 'repeat(7,1fr)', gap: 6, marginTop: 14 }}>
          {ritual.week.map((d) => {
            const upToToday = !d.is_future;
            const bg = d.done
              ? 'var(--accent)'
              : d.is_today
                ? 'rgba(224,178,108,.18)'
                : 'rgba(255,255,255,.03)';
            return (
              <div key={d.date} className="flex flex-col items-center" style={{ gap: 6 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#7E7890' }}>
                  {t.days[d.weekday]}
                </span>
                <span
                  aria-label={`${t.days[d.weekday]}: ${d.done ? '✓' : '—'}`}
                  className="w-full"
                  style={{
                    aspectRatio: '1',
                    borderRadius: 9,
                    background: bg,
                    border: `1px solid ${upToToday ? 'rgba(224,178,108,.55)' : 'rgba(255,255,255,.10)'}`,
                  }}
                />
              </div>
            );
          })}
        </div>

        <p style={{ marginTop: 14, fontSize: '13.5px', lineHeight: 1.5, color: '#A49DAF' }}>
          {ritual.done_today ? t.done : t.todo}
        </p>
      </div>
    </section>
  );
}
