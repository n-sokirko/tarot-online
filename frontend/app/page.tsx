'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { ApiError, createReading, getBillingMe, getDailyCard, type DailyCardResponse } from '@/lib/api';
import { getAccessToken } from '@/lib/auth';
import { useRitualContext } from '@/lib/ritual-context';
import QuestionBlock from '@/components/home/QuestionBlock';
import DailyFan from '@/components/home/DailyFan';
import WeekRitual from '@/components/home/WeekRitual';
import SpreadRail, { type RailSpread } from '@/components/home/SpreadRail';
import YesterdayCard from '@/components/home/YesterdayCard';
import ShareCard from '@/components/home/ShareCard';
import PremiumStrip from '@/components/home/PremiumStrip';

const ERRORS = {
  ru: {
    limit: 'Бесплатные расклады на сегодня закончились. Завтра будут новые — или загляни в Premium.',
    generic: 'Не получилось разложить карты. Попробуй ещё раз через минуту.',
  },
  en: {
    limit: "You've used today's free readings. New ones tomorrow — or have a look at Premium.",
    generic: "Couldn't lay out the cards. Try again in a minute.",
  },
} as const;

/** Home, design "1a Обсидиан": question → card of the day → ritual → spreads. */
export default function HomePage() {
  const rawLocale = useLocale();
  const locale: 'ru' | 'en' = rawLocale === 'ru' ? 'ru' : 'en';
  const router = useRouter();
  const { ritual, checkIn } = useRitualContext();

  const [question, setQuestion] = useState('');
  const [shuffleSignal, setShuffleSignal] = useState(0);
  const [daily, setDaily] = useState<DailyCardResponse | null>(null);
  const [flipped, setFlipped] = useState(false);
  const [opened, setOpened] = useState(false);
  const [busy, setBusy] = useState<RailSpread | null>(null);
  const [error, setError] = useState<{ text: string; at: 'top' | 'rail' } | null>(null);
  const [premium, setPremium] = useState(false);

  useEffect(() => {
    getDailyCard().then(setDaily).catch(() => {/* the fan still shows card backs */});
    if (getAccessToken()) {
      getBillingMe()
        .then((me) => setPremium((me.entitlements ?? []).includes('sonnet_ai')))
        .catch(() => {});
    }
  }, []);

  const onOpened = useCallback(() => {
    setOpened(true);
    if (!ritual.done_today) void checkIn();
  }, [ritual.done_today, checkIn]);

  const pick = useCallback(async (slug: RailSpread, at: 'top' | 'rail' = 'rail') => {
    if (slug === 'free') {
      router.push('/table');
      return;
    }
    setBusy(slug);
    setError(null);
    try {
      const reading = await createReading(rawLocale, slug, question.trim());
      router.push(`/reading/${reading.id}`);
    } catch (e) {
      setError({
        text: e instanceof ApiError && (e.status === 402 || e.status === 429)
          ? ERRORS[locale].limit
          : ERRORS[locale].generic,
        at,
      });
      setBusy(null);
    }
  }, [router, rawLocale, question, locale]);

  return (
    <main
      className="relative min-h-screen mx-auto"
      style={{
        maxWidth: 560,
        overflowX: 'hidden',
        paddingBottom: 40,
        background:
          'radial-gradient(520px 340px at 84% -6%, rgba(182,167,240,.20), transparent 70%),' +
          'radial-gradient(420px 300px at 0% 18%, rgba(224,178,108,.12), transparent 70%)',
      }}
    >
      {/* Decorative slow ring behind the title. */}
      <div
        aria-hidden
        className="absolute pointer-events-none"
        style={{
          width: 280, height: 280, top: -90, right: -110, borderRadius: '50%',
          border: '1px dashed rgba(224,178,108,.18)',
          animation: 'spin 140s linear infinite',
        }}
      />

      <QuestionBlock
        locale={locale}
        question={question}
        onQuestion={setQuestion}
        busy={busy === 'three-card'}
        onShuffle={() => {
          // "Перетасовать" opens the standard three-card reading right away.
          setShuffleSignal((n) => n + 1);
          void pick('three-card', 'top');
        }}
      />
      {error?.at === 'top' && (
        <p role="alert" style={{ margin: '12px 18px 0', fontSize: 13.5, lineHeight: 1.5, color: '#E7A48B' }}>
          {error.text}
        </p>
      )}
      <DailyFan
        locale={locale}
        daily={daily}
        flipped={flipped}
        onFlip={setFlipped}
        shuffleSignal={shuffleSignal}
        onOpened={onOpened}
      />
      <WeekRitual locale={locale} ritual={ritual} />
      <SpreadRail locale={locale} busy={busy} onPick={(slug) => void pick(slug)} />
      {error?.at === 'rail' && (
        <p role="alert" style={{ margin: '14px 18px 0', fontSize: 13.5, lineHeight: 1.5, color: '#E7A48B' }}>
          {error.text}
        </p>
      )}
      <YesterdayCard locale={locale} />
      <ShareCard locale={locale} daily={daily} opened={opened} />
      {!premium && <PremiumStrip locale={locale} />}
    </main>
  );
}
