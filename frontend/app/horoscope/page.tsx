'use client';

import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocale } from 'next-intl';
import { useRouter } from 'next/navigation';
import {
  listZodiacSigns,
  getDailyHoroscope,
  interpretHoroscope,
  ApiError,
} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import ZodiacConstellation from '@/components/horoscope/ZodiacConstellation';
import ZodiacImage from '@/components/horoscope/ZodiacImage';
import Starfield from '@/components/visual/Starfield';
import SpeakButton from '@/components/a11y/SpeakButton';
import type { ZodiacSign, DailyHoroscope, HoroscopeAIReading } from '@/lib/types';

const STRINGS = {
  ru: {
    title: 'Гороскоп',
    heading: 'Гороскоп на сегодня',
    subtitle: 'Выбери свой знак зодиака и узнай, чем дышит этот день',
    pick: 'Выбери знак',
    back: '← Все знаки',
    overall: 'Тон дня',
    love: 'Любовь',
    career: 'Дела и финансы',
    wellbeing: 'Самочувствие',
    mood: 'Настрой дня',
    lucky_number: 'Число дня',
    lucky_color: 'Цвет дня',
    energy: 'Энергия',
    deep: 'Подробный AI-гороскоп',
    interpreting: 'Звёзды складываются...',
    deep_cta: 'Стоит 1 кредит. Кредиты можно купить звёздами ⭐ или получить по Premium.',
    login_cta: 'Войти, чтобы открыть',
    error: 'Что-то пошло не так. Попробуйте ещё раз.',
  },
  en: {
    title: 'Horoscope',
    heading: 'Today’s horoscope',
    subtitle: 'Choose your zodiac sign and see what this day breathes',
    pick: 'Choose a sign',
    back: '← All signs',
    overall: 'Tone of the day',
    love: 'Love',
    career: 'Work & money',
    wellbeing: 'Wellbeing',
    mood: 'Mood of the day',
    lucky_number: 'Number of the day',
    lucky_color: 'Colour of the day',
    energy: 'Energy',
    deep: 'Detailed AI horoscope',
    interpreting: 'The stars are aligning...',
    deep_cta: 'Costs 1 credit. Buy credits with stars ⭐ or get them with Premium.',
    login_cta: 'Sign in to unlock',
    error: 'Something went wrong. Please try again.',
  },
} as const;

const ELEMENT_ACCENT: Record<string, string> = {
  fire: '#e8915a',
  earth: '#9ad9a0',
  air: '#a8c4ea',
  water: '#7fb0d8',
};

function Section({ label, text, accent }: { label: string; text: string; accent: string }) {
  return (
    <div
      className="p-5 rounded-2xl"
      style={{ background: 'rgba(212,175,55,0.04)', border: `1px solid ${accent}33` }}
    >
      <p
        className="font-sans text-[0.65rem] uppercase tracking-widest mb-2"
        style={{ color: accent, letterSpacing: '0.2em' }}
      >
        {label}
      </p>
      <p className="font-serif text-sm leading-relaxed" style={{ color: 'rgba(201,194,224,0.92)' }}>
        {text}
      </p>
    </div>
  );
}

export default function HoroscopePage() {
  const locale = useLocale() as 'ru' | 'en';
  const t = STRINGS[locale];
  const router = useRouter();
  const { user } = useAuth();

  const [signs, setSigns] = useState<ZodiacSign[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [horo, setHoro] = useState<DailyHoroscope | null>(null);
  const [aiReading, setAiReading] = useState<HoroscopeAIReading | null>(null);
  const [loading, setLoading] = useState(false);
  const [interpreting, setInterpreting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    void listZodiacSigns(locale).then((r) => setSigns(r.signs)).catch(() => setSigns([]));
  }, [locale]);

  const handleSelect = useCallback(async (slug: string) => {
    setSelected(slug);
    setError('');
    setHoro(null);
    setAiReading(null);
    setLoading(true);
    try {
      const result = await getDailyHoroscope(slug, locale);
      setHoro(result);
    } catch {
      setError(t.error);
    } finally {
      setLoading(false);
    }
  }, [locale, t]);

  const handleInterpret = useCallback(async () => {
    if (!selected) return;
    if (!user) { router.push('/login?next=/horoscope'); return; }
    setError('');
    setInterpreting(true);
    try {
      const result = await interpretHoroscope(selected, locale);
      setAiReading(result);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) router.push('/login?next=/horoscope');
      else if (e instanceof ApiError && e.status === 402) router.push('/pricing');
      else setError(t.error);
    } finally {
      setInterpreting(false);
    }
  }, [selected, user, locale, router, t]);

  const handleBack = () => {
    setSelected(null);
    setHoro(null);
    setAiReading(null);
    setError('');
  };

  const accent = horo ? (ELEMENT_ACCENT[horo.element] ?? '#d4af37') : '#d4af37';

  return (
    <main
      className="relative overflow-hidden min-h-screen flex flex-col items-center px-4 py-12"
      style={{ background: 'transparent' }}
    >
      <Starfield seed={selected ?? 'horoscope'} count={54} />
      <motion.div
        className="relative z-10 w-full max-w-2xl flex flex-col gap-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <header className="text-center flex flex-col gap-2">
          <p
            className="font-sans text-xs uppercase tracking-widest"
            style={{ color: 'rgba(212,175,55,0.55)', letterSpacing: '0.25em' }}
          >
            ✦ {t.title} ✦
          </p>
          <h1 className="font-serif text-4xl" style={{ color: '#d4af37' }}>
            {t.heading}
          </h1>
          <p
            className="font-sans text-sm leading-relaxed max-w-md mx-auto"
            style={{ color: 'rgba(201,194,224,0.7)' }}
          >
            {t.subtitle}
          </p>
        </header>

        <AnimatePresence mode="wait">
          {!selected ? (
            <motion.div
              key="grid"
              className="grid grid-cols-3 sm:grid-cols-4 gap-3"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {signs.map((s) => {
                const a = ELEMENT_ACCENT[s.element] ?? '#d4af37';
                return (
                  <motion.button
                    key={s.slug}
                    onClick={() => void handleSelect(s.slug)}
                    className="flex flex-col items-center gap-1.5 py-4 rounded-2xl"
                    style={{
                      background: 'rgba(212,175,55,0.04)',
                      border: `1px solid ${a}33`,
                    }}
                    whileHover={{ backgroundColor: 'rgba(212,175,55,0.1)', scale: 1.04 }}
                    whileTap={{ scale: 0.97 }}
                  >
                    <ZodiacImage sign={s.slug} symbol={s.symbol} size={40} accent={a} />
                    <span
                      className="font-serif text-sm"
                      style={{ color: 'rgba(201,194,224,0.9)' }}
                    >
                      {s.name}
                    </span>
                    <span
                      className="font-sans text-[0.55rem] uppercase tracking-wider"
                      style={{ color: 'rgba(201,194,224,0.4)', letterSpacing: '0.1em' }}
                    >
                      {s.date_range}
                    </span>
                  </motion.button>
                );
              })}
            </motion.div>
          ) : (
            <motion.div
              key="reading"
              className="flex flex-col gap-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <button
                onClick={handleBack}
                className="self-start text-[0.7rem] font-sans uppercase tracking-widest"
                style={{ color: 'rgba(201,194,224,0.5)', letterSpacing: '0.2em' }}
              >
                {t.back}
              </button>

              {loading && (
                <p className="text-center font-serif text-sm" style={{ color: 'rgba(201,194,224,0.6)' }}>
                  ✦ ...
                </p>
              )}

              {horo && (
                <>
                  {/* Sign header with animated constellation */}
                  <div className="flex flex-col items-center gap-1">
                    <ZodiacConstellation sign={horo.sign} symbol={horo.symbol} accent={accent} />
                    <p className="font-serif text-2xl" style={{ color: accent }}>
                      {locale === 'ru' ? horo.name_ru : horo.name_en}
                    </p>
                    <p className="font-sans text-xs" style={{ color: 'rgba(201,194,224,0.45)' }}>
                      {new Date(horo.date).toLocaleDateString(
                        locale === 'ru' ? 'ru-RU' : 'en-US',
                        { day: 'numeric', month: 'long', year: 'numeric' },
                      )}
                      {' · '}
                      {locale === 'ru' ? horo.element_ru : horo.element_en}
                      {' · '}
                      {locale === 'ru' ? horo.planet_ru : horo.planet_en}
                    </p>
                  </div>

                  {/* Stat chips */}
                  <div className="flex flex-wrap justify-center gap-3">
                    {[
                      { label: t.mood, value: horo.mood },
                      { label: t.lucky_number, value: String(horo.lucky_number) },
                      { label: t.lucky_color, value: horo.lucky_color },
                      { label: t.energy, value: '★'.repeat(horo.energy) + '☆'.repeat(5 - horo.energy) },
                    ].map((chip) => (
                      <div
                        key={chip.label}
                        className="px-4 py-2 rounded-full text-center"
                        style={{ background: 'rgba(212,175,55,0.06)', border: `1px solid ${accent}33` }}
                      >
                        <p
                          className="font-sans text-[0.55rem] uppercase tracking-widest"
                          style={{ color: 'rgba(201,194,224,0.45)', letterSpacing: '0.15em' }}
                        >
                          {chip.label}
                        </p>
                        <p className="font-serif text-sm" style={{ color: accent }}>{chip.value}</p>
                      </div>
                    ))}
                  </div>

                  {/* Sections */}
                  <Section label={t.overall} text={horo.overall} accent={accent} />
                  <Section label={t.love} text={horo.love} accent="#c9a4d8" />
                  <Section label={t.career} text={horo.career} accent="#d4af37" />
                  <Section label={t.wellbeing} text={horo.wellbeing} accent="#9ad9c0" />

                  {/* Listen to the daily horoscope */}
                  <div className="flex justify-center">
                    <SpeakButton
                      text={`${horo.overall} ${horo.love} ${horo.career} ${horo.wellbeing}`}
                      lang={locale}
                    />
                  </div>

                  {/* AI deep reading */}
                  {aiReading ? (
                    <div
                      className="p-6 rounded-2xl"
                      style={{
                        background: 'linear-gradient(135deg, rgba(28,24,64,0.6), rgba(11,11,31,0.4))',
                        border: '1px solid rgba(180,140,200,0.2)',
                      }}
                    >
                      <p
                        className="font-sans text-xs uppercase tracking-widest mb-4 text-center"
                        style={{ color: 'rgba(180,140,200,0.7)', letterSpacing: '0.2em' }}
                      >
                        ✦ {t.deep}
                      </p>
                      <div className="flex justify-center mb-4">
                        <SpeakButton text={aiReading.body_md} lang={locale} autoPlay />
                      </div>
                      <div
                        className="font-serif text-sm leading-relaxed whitespace-pre-wrap"
                        style={{ color: 'rgba(201,194,224,0.9)' }}
                      >
                        {aiReading.body_md}
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-3">
                      <p
                        className="text-xs text-center max-w-xs font-sans"
                        style={{ color: 'rgba(201,194,224,0.55)' }}
                      >
                        {user ? t.deep_cta : t.login_cta}
                      </p>
                      <motion.button
                        onClick={() => void handleInterpret()}
                        disabled={interpreting}
                        className="px-8 py-3 rounded-full font-serif text-sm tracking-widest uppercase"
                        style={{
                          background: interpreting ? 'rgba(180,140,200,0.05)' : 'rgba(180,140,200,0.1)',
                          border: '1px solid rgba(180,140,200,0.6)',
                          color: 'rgba(220,180,240,0.9)',
                          letterSpacing: '0.15em',
                          opacity: interpreting ? 0.6 : 1,
                        }}
                        whileHover={interpreting ? {} : { backgroundColor: 'rgba(180,140,200,0.2)' }}
                      >
                        ✦ {interpreting ? t.interpreting : (user ? t.deep : t.login_cta)}
                      </motion.button>
                    </div>
                  )}
                </>
              )}

              {error && (
                <p className="text-center text-xs" style={{ color: 'rgba(200,80,80,0.85)' }}>
                  {error}
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </main>
  );
}
