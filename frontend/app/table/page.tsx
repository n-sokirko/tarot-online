'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useLocale } from 'next-intl';
import FreeTable from '@/components/tarot/FreeTable';
import InterpretationPanel from '@/components/tarot/InterpretationPanel';
import { openTable } from '@/lib/api';
import type { DrawnCard, ReadingResponse } from '@/lib/types';

const labels = {
  ru: {
    title: 'Свободный стол',
    lead: 'Здесь нет заданных позиций. Вытяни столько карт, сколько захочешь, и разложи их так, как тебе понятно.',
    help: 'Помоги с разъяснением',
    helpHint: 'Разберу то, что у тебя получилось: и карты, и то, как ты их выложил.',
    loading: 'Раскладываю стол…',
    error: 'Не получилось открыть стол. Попробуй ещё раз.',
    retry: 'Попробовать снова',
    back: '← На главную',
    needCard: 'Выложи хотя бы одну карту.',
  },
  en: {
    title: 'Free table',
    lead: 'No fixed positions here. Pull as many cards as you want and arrange them in whatever way makes sense to you.',
    help: 'Help me read this',
    helpHint: "I'll go through what you laid out — the cards and the shape you gave them.",
    loading: 'Setting the table…',
    error: "Couldn't open the table. Try again.",
    retry: 'Try again',
    back: '← Home',
    needCard: 'Lay out at least one card.',
  },
} as const;

export default function TablePage() {
  const locale = (useLocale() === 'ru' ? 'ru' : 'en') as 'ru' | 'en';
  const t = labels[locale];
  const router = useRouter();

  const [reading, setReading] = useState<ReadingResponse | null>(null);
  const [failed, setFailed] = useState(false);
  const [cards, setCards] = useState<DrawnCard[]>([]);
  const [askedForHelp, setAskedForHelp] = useState(false);

  const start = useCallback(() => {
    setFailed(false);
    setReading(null);
    openTable(locale)
      .then((r) => {
        setReading(r);
        setCards(r.cards);
      })
      .catch(() => setFailed(true));
  }, [locale]);

  useEffect(() => { start(); }, [start]);

  if (failed) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
        <p style={{ color: 'rgba(201,194,224,0.7)' }}>{t.error}</p>
        <button
          onClick={start}
          className="px-5 py-2 rounded-full text-xs tracking-widest uppercase"
          style={{ border: '1px solid rgba(212,175,55,0.35)', color: 'rgba(212,175,55,0.85)' }}
        >
          {t.retry}
        </button>
      </main>
    );
  }

  if (!reading) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <motion.p
          className="font-serif italic"
          style={{ color: 'rgba(212,175,55,0.7)' }}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
        >
          {t.loading}
        </motion.p>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center px-4 py-10 md:py-16">
      <div className="w-full max-w-md flex flex-col gap-6">
        <header className="flex flex-col gap-2 text-center">
          <h1 className="font-serif text-2xl" style={{ color: 'rgba(212,175,55,0.9)' }}>
            {t.title}
          </h1>
          <p className="text-sm" style={{ color: 'rgba(201,194,224,0.6)' }}>{t.lead}</p>
        </header>

        <FreeTable
          readingId={reading.id}
          locale={locale}
          initialCards={reading.cards}
          onCardsChange={setCards}
        />

        {/* The reading is never forced: it happens when the person asks for it,
            after they are done arranging. */}
        {!askedForHelp ? (
          <div className="flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={() => setAskedForHelp(true)}
              disabled={cards.length === 0}
              className="px-6 py-3 rounded-full text-sm tracking-wide disabled:opacity-40"
              style={{
                border: '1px solid rgba(212,175,55,0.45)',
                color: 'rgba(212,175,55,0.95)',
                background: 'rgba(212,175,55,0.06)',
              }}
            >
              ✦ {t.help}
            </button>
            <p className="text-xs text-center" style={{ color: 'rgba(201,194,224,0.45)' }}>
              {cards.length === 0 ? t.needCard : t.helpHint}
            </p>
          </div>
        ) : (
          <InterpretationPanel
            readingId={reading.id}
            locale={locale}
            initial={reading.interpretation}
          />
        )}

        <button
          onClick={() => router.push('/')}
          className="self-center mt-2 text-xs underline"
          style={{ color: 'rgba(201,194,224,0.4)' }}
        >
          {t.back}
        </button>
      </div>
    </main>
  );
}
