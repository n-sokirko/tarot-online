'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { getMyReadings } from '@/lib/api';
import { getAccessToken } from '@/lib/auth';

/**
 * A line from the person's last reading, to give them a reason to come back to
 * the journal. Only for signed-in people with at least one interpreted reading;
 * otherwise the section stays out of the way rather than showing a made-up
 * quote.
 */

function firstSentence(md: string): string {
  const plain = md
    .replace(/[#>*_`]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  const match = plain.match(/^(.{20,160}?[.!?…])(\s|$)/);
  const sentence = match ? match[1] : plain.slice(0, 140);
  return sentence.length < plain.length && !match ? `${sentence}…` : sentence;
}

function whenLabel(iso: string, locale: 'ru' | 'en'): string {
  const then = new Date(iso);
  const now = new Date();
  const days = Math.floor(
    (Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())
      - Date.UTC(then.getFullYear(), then.getMonth(), then.getDate())) / 86_400_000,
  );
  if (locale === 'ru') {
    if (days <= 0) return 'Сегодняшний разбор';
    if (days === 1) return 'Вчерашний разбор';
    return `Разбор ${days} дн. назад`;
  }
  if (days <= 0) return "Today's reading";
  if (days === 1) return "Yesterday's reading";
  return `Reading from ${days} days ago`;
}

export default function YesterdayCard({ locale }: { locale: 'ru' | 'en' }) {
  const [item, setItem] = useState<{ quote: string; when: string; question: string } | null>(null);

  useEffect(() => {
    if (!getAccessToken()) return;
    getMyReadings()
      .then((list) => {
        const last = list.find((r) => r.interpretation?.body_md);
        if (!last?.interpretation) return;
        setItem({
          quote: firstSentence(last.interpretation.body_md),
          when: whenLabel(last.created_at, locale),
          question: last.question,
        });
      })
      .catch(() => {/* no journal, no card */});
  }, [locale]);

  if (!item) return null;

  return (
    <section style={{ padding: '10px 18px 0' }}>
      <div
        className="reveal-3d"
        style={{
          borderRadius: 18,
          border: '1px solid rgba(255,255,255,.10)',
          background: 'rgba(255,255,255,.03)',
          padding: 18,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '10.5px',
            letterSpacing: '.16em',
            textTransform: 'uppercase',
            color: '#8E879B',
          }}
        >
          {item.when}
        </span>
        <p className="font-serif" style={{ fontSize: 18, lineHeight: 1.35, marginTop: 10 }}>
          «{item.quote}»
        </p>
        {item.question && (
          <p style={{ fontSize: '13.5px', lineHeight: 1.6, color: '#A49DAF', marginTop: 8 }}>
            {locale === 'ru' ? 'Вопрос: ' : 'Question: '}{item.question}
          </p>
        )}
        <Link
          href="/history"
          className="inline-flex items-center justify-center transition-colors hover:border-[var(--accent)] hover:text-[var(--accent)]"
          style={{
            marginTop: 14,
            border: '1px solid rgba(255,255,255,.16)',
            borderRadius: 999,
            padding: '10px 18px',
            fontSize: 13.5,
            minHeight: 44,
          }}
        >
          {locale === 'ru' ? 'Открыть дневник' : 'Open the journal'}
        </Link>
      </div>
    </section>
  );
}
