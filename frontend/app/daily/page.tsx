'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocale } from 'next-intl';
import CardFace from '@/components/tarot/CardFace';
import CardBack from '@/components/tarot/CardBack';
import { getDailyCard, type DailyCardResponse, ApiError } from '@/lib/api';

const STRINGS = {
  ru: {
    title: 'Карта дня',
    subtitle: 'Одна карта на сегодня — послание, на которое стоит обратить внимание',
    reveal: 'Открыть карту',
    revealing: 'Раскрывается...',
    todayLabel: 'Сегодня',
    reversedNote: 'Перевёрнутая позиция',
    upright: 'Прямое значение',
    reversed: 'Перевёрнутое значение',
    keywords: 'Ключевые темы',
    reflection: 'Размышление',
    error: 'Что-то пошло не так. Попробуйте ещё раз.',
  },
  en: {
    title: 'Card of the Day',
    subtitle: 'One card for today — a message worth your attention',
    reveal: 'Reveal the card',
    revealing: 'Unfolding...',
    todayLabel: 'Today',
    reversedNote: 'Reversed position',
    upright: 'Upright meaning',
    reversed: 'Reversed meaning',
    keywords: 'Key themes',
    reflection: 'Reflection',
    error: 'Something went wrong. Please try again.',
  },
} as const;

const REFLECTION_RU = [
  'Какая часть этого послания резонирует с тем, что ты сейчас чувствуешь?',
  'Если бы эта карта была голосом — что бы она сказала тебе сегодня шёпотом?',
  'Что в твоей жизни ждёт того, чтобы ты увидел его в этом свете?',
  'Какой первый шаг подсказывает тебе эта карта?',
];
const REFLECTION_EN = [
  'Which part of this message resonates with what you feel right now?',
  'If this card had a voice — what would it whisper to you today?',
  'What in your life is waiting to be seen in this light?',
  'What first step does this card suggest?',
];

export default function DailyCardPage() {
  const locale = useLocale() as 'ru' | 'en';
  const t = STRINGS[locale];
  const [data, setData] = useState<DailyCardResponse | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const result = await getDailyCard();
        if (!cancelled) setData(result);
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? t.error : t.error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [t.error]);

  const reflection = data
    ? (locale === 'ru' ? REFLECTION_RU : REFLECTION_EN)[
        Math.abs(data.card.slug.split('').reduce((a, c) => a + c.charCodeAt(0), 0)) %
        (locale === 'ru' ? REFLECTION_RU.length : REFLECTION_EN.length)
      ]
    : '';

  const today = new Date().toLocaleDateString(locale === 'ru' ? 'ru-RU' : 'en-US', {
    weekday: 'long', day: 'numeric', month: 'long',
  });

  const meaning = data
    ? (data.is_reversed
        ? (locale === 'ru' ? data.card.reversed_meaning_ru : data.card.reversed_meaning_en)
        : (locale === 'ru' ? data.card.upright_meaning_ru : data.card.upright_meaning_en))
    : '';

  return (
    <main
      className="min-h-screen flex flex-col items-center px-4 py-12"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.85) 0%, #0b0b1f 60%)' }}
    >
      <motion.div
        className="w-full max-w-md flex flex-col items-center gap-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <header className="text-center flex flex-col gap-2">
          <p
            className="font-sans text-xs uppercase tracking-widest"
            style={{ color: 'rgba(212,175,55,0.55)', letterSpacing: '0.25em' }}
          >
            {t.todayLabel} · {today}
          </p>
          <h1 className="font-serif text-4xl" style={{ color: '#d4af37' }}>
            {t.title}
          </h1>
          <p
            className="font-sans text-sm leading-relaxed max-w-xs mx-auto"
            style={{ color: 'rgba(201,194,224,0.7)' }}
          >
            {t.subtitle}
          </p>
        </header>

        {loading && (
          <div className="text-center" style={{ color: 'rgba(201,194,224,0.5)' }}>
            <span className="font-serif italic">{t.revealing}</span>
          </div>
        )}

        {error && (
          <p className="text-center" style={{ color: 'rgba(200,80,80,0.85)' }}>{error}</p>
        )}

        {data && (
          <div className="w-full flex flex-col items-center gap-6">
            <div
              className="cursor-pointer select-none"
              style={{ width: '220px', perspective: '1200px' }}
              onClick={() => setRevealed(true)}
            >
              <AnimatePresence mode="wait">
                {!revealed ? (
                  <motion.div
                    key="back"
                    initial={{ rotateY: 0 }}
                    exit={{ rotateY: 180, opacity: 0 }}
                    transition={{ duration: 0.7 }}
                    style={{ transformStyle: 'preserve-3d' }}
                  >
                    <CardBack />
                    <p
                      className="mt-3 text-center font-serif text-xs italic"
                      style={{ color: 'rgba(212,175,55,0.7)' }}
                    >
                      {t.reveal}
                    </p>
                  </motion.div>
                ) : (
                  <motion.div
                    key="face"
                    initial={{ rotateY: -180, opacity: 0 }}
                    animate={{ rotateY: 0, opacity: 1 }}
                    transition={{ duration: 0.7 }}
                    style={{ transformStyle: 'preserve-3d' }}
                  >
                    <CardFace card={data.card} isReversed={data.is_reversed} locale={locale} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {revealed && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.6 }}
                className="w-full flex flex-col gap-5 px-2"
              >
                {data.is_reversed && (
                  <p
                    className="text-center text-xs uppercase tracking-widest"
                    style={{ color: 'rgba(180,140,200,0.7)', letterSpacing: '0.2em' }}
                  >
                    ↕ {t.reversedNote}
                  </p>
                )}

                {/* Keywords */}
                <div className="flex flex-wrap gap-2 justify-center">
                  {(locale === 'ru' ? data.card.keywords_ru : data.card.keywords_en).map((kw) => (
                    <span
                      key={kw}
                      className="rounded-full px-3 py-1 text-xs"
                      style={{
                        background: 'rgba(212,175,55,0.08)',
                        color: 'rgba(212,175,55,0.9)',
                        border: '1px solid rgba(212,175,55,0.2)',
                      }}
                    >
                      {kw}
                    </span>
                  ))}
                </div>

                {/* Meaning */}
                <div
                  className="p-5 rounded-2xl"
                  style={{
                    background: 'rgba(212,175,55,0.04)',
                    border: '1px solid rgba(212,175,55,0.18)',
                  }}
                >
                  <p
                    className="font-sans text-xs uppercase tracking-widest mb-3"
                    style={{ color: 'rgba(212,175,55,0.6)', letterSpacing: '0.2em' }}
                  >
                    {data.is_reversed ? t.reversed : t.upright}
                  </p>
                  <p
                    className="font-serif text-sm leading-relaxed"
                    style={{ color: 'rgba(201,194,224,0.92)' }}
                  >
                    {meaning}
                  </p>
                </div>

                {/* Reflection */}
                <div
                  className="p-5 rounded-2xl text-center"
                  style={{
                    background: 'linear-gradient(135deg, rgba(28,24,64,0.6), rgba(11,11,31,0.4))',
                    border: '1px solid rgba(180,140,200,0.18)',
                  }}
                >
                  <p
                    className="font-sans text-xs uppercase tracking-widest mb-3"
                    style={{ color: 'rgba(180,140,200,0.7)', letterSpacing: '0.2em' }}
                  >
                    ✦ {t.reflection}
                  </p>
                  <p
                    className="font-serif italic text-sm leading-relaxed"
                    style={{ color: 'rgba(201,194,224,0.85)' }}
                  >
                    {reflection}
                  </p>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </motion.div>
    </main>
  );
}
