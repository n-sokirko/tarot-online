'use client';

import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocale } from 'next-intl';
import { useRouter } from 'next/navigation';
import {
  createNumerologyReading,
  interpretNumerology,
  getBillingMe,
  ApiError,
} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { NumerologyReading, NumerologyInterpretation } from '@/lib/types';

const STRINGS = {
  ru: {
    title: 'Нумерология',
    subtitle: 'Числа, которые звучат в твоём имени и дне рождения',
    name_label: 'Полное имя (как при рождении)',
    name_placeholder: 'Анна Иванова Петровна',
    date_label: 'Дата рождения',
    submit: 'Рассчитать профиль',
    calculating: 'Считаю числа...',
    new_reading: 'Новый расчёт',
    interpret: 'Глубокая интерпретация',
    interpreting: 'Раскрывается...',
    interpret_cta: 'AI-интерпретация доступна по Premium-подписке',
    open_pricing: 'Открыть тарифы',
    life_path: 'Жизненный путь',
    destiny: 'Судьба',
    soul_urge: 'Душа',
    personality: 'Личность',
    birthday: 'День рождения',
    error: 'Что-то пошло не так. Попробуйте ещё раз.',
    name_required: 'Введите полное имя.',
  },
  en: {
    title: 'Numerology',
    subtitle: 'Numbers that sound in your name and birth date',
    name_label: 'Full name (as given at birth)',
    name_placeholder: 'Jane Mary Doe',
    date_label: 'Birth date',
    submit: 'Calculate profile',
    calculating: 'Calculating...',
    new_reading: 'New reading',
    interpret: 'Deep interpretation',
    interpreting: 'Unfolding...',
    interpret_cta: 'AI interpretation is available with a Premium subscription',
    open_pricing: 'Open pricing',
    life_path: 'Life Path',
    destiny: 'Destiny',
    soul_urge: 'Soul Urge',
    personality: 'Personality',
    birthday: 'Birthday',
    error: 'Something went wrong. Please try again.',
    name_required: 'Enter your full name.',
  },
} as const;

function NumberOrb({ value, label, sublabel, accent = '#d4af37' }: {
  value: number;
  label: string;
  sublabel: string;
  accent?: string;
}) {
  return (
    <motion.div
      className="flex flex-col items-center gap-2"
      initial={{ opacity: 0, scale: 0.7 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      <div
        className="relative flex items-center justify-center rounded-full"
        style={{
          width: '108px',
          height: '108px',
          background: `radial-gradient(circle at 35% 35%, rgba(212,175,55,0.18) 0%, rgba(11,11,31,0.6) 70%)`,
          border: `1px solid ${accent}55`,
          boxShadow: `0 0 24px ${accent}33, inset 0 0 16px ${accent}22`,
        }}
      >
        <span
          className="font-serif"
          style={{
            fontSize: value >= 10 ? '2.6rem' : '3.2rem',
            color: accent,
            textShadow: `0 0 10px ${accent}aa`,
            lineHeight: 1,
          }}
        >
          {value}
        </span>
      </div>
      <p
        className="font-sans text-[0.65rem] uppercase tracking-widest"
        style={{ color: 'rgba(201,194,224,0.55)', letterSpacing: '0.2em' }}
      >
        {label}
      </p>
      <p
        className="font-serif text-xs italic"
        style={{ color: accent, opacity: 0.85 }}
      >
        {sublabel}
      </p>
    </motion.div>
  );
}

export default function NumerologyPage() {
  const locale = useLocale() as 'ru' | 'en';
  const t = STRINGS[locale];
  const router = useRouter();
  const { user } = useAuth();

  const [fullName, setFullName] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [reading, setReading] = useState<NumerologyReading | null>(null);
  const [interpretation, setInterpretation] = useState<NumerologyInterpretation | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [interpreting, setInterpreting] = useState(false);
  const [isPremium, setIsPremium] = useState(false);

  useEffect(() => {
    if (!user) { setIsPremium(false); return; }
    void getBillingMe().then((b) => setIsPremium(b.entitlements.includes('natal_chart')))
      .catch(() => setIsPremium(false));
  }, [user]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (fullName.trim().length < 2) { setError(t.name_required); return; }
    setLoading(true);
    try {
      const result = await createNumerologyReading({
        full_name: fullName.trim(),
        birth_date: birthDate,
        locale,
      });
      setReading(result);
      setInterpretation(result.interpretation);
    } catch (e) {
      setError(e instanceof ApiError ? t.error : t.error);
    } finally {
      setLoading(false);
    }
  }, [fullName, birthDate, locale, t]);

  const handleInterpret = useCallback(async () => {
    if (!reading) return;
    if (!isPremium) { router.push('/pricing'); return; }
    setError('');
    setInterpreting(true);
    try {
      const result = await interpretNumerology(reading.id);
      setInterpretation(result);
    } catch (e) {
      if (e instanceof ApiError && e.status === 402) router.push('/pricing');
      else setError(t.error);
    } finally {
      setInterpreting(false);
    }
  }, [reading, isPremium, router, t]);

  const handleReset = () => {
    setReading(null);
    setInterpretation(null);
    setError('');
  };

  return (
    <main
      className="min-h-screen flex flex-col items-center px-4 py-12"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.85) 0%, #0b0b1f 60%)' }}
    >
      <motion.div
        className="w-full max-w-2xl flex flex-col gap-8"
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
            {locale === 'ru' ? 'Числа твоей жизни' : 'The numbers of your life'}
          </h1>
          <p
            className="font-sans text-sm leading-relaxed max-w-md mx-auto"
            style={{ color: 'rgba(201,194,224,0.7)' }}
          >
            {t.subtitle}
          </p>
        </header>

        <AnimatePresence mode="wait">
          {!reading ? (
            <motion.form
              key="form"
              onSubmit={(e) => void handleSubmit(e)}
              className="flex flex-col gap-5"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="flex flex-col gap-2">
                <label
                  className="font-sans text-xs uppercase tracking-widest"
                  style={{ color: 'rgba(201,194,224,0.6)', letterSpacing: '0.2em' }}
                >
                  {t.name_label}
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder={t.name_placeholder}
                  className="w-full px-4 py-3 rounded-xl bg-transparent outline-none font-sans"
                  style={{
                    border: '1px solid rgba(212,175,55,0.3)',
                    color: 'rgba(201,194,224,0.9)',
                    background: 'rgba(212,175,55,0.04)',
                  }}
                  required
                />
              </div>
              <div className="flex flex-col gap-2">
                <label
                  className="font-sans text-xs uppercase tracking-widest"
                  style={{ color: 'rgba(201,194,224,0.6)', letterSpacing: '0.2em' }}
                >
                  {t.date_label}
                </label>
                <input
                  type="date"
                  value={birthDate}
                  onChange={(e) => setBirthDate(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-transparent outline-none font-sans"
                  style={{
                    border: '1px solid rgba(212,175,55,0.3)',
                    color: 'rgba(201,194,224,0.9)',
                    background: 'rgba(212,175,55,0.04)',
                  }}
                  required
                />
              </div>

              {error && (
                <p className="text-center text-xs" style={{ color: 'rgba(200,80,80,0.85)' }}>
                  {error}
                </p>
              )}

              <motion.button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-full font-serif text-sm tracking-widest uppercase"
                style={{
                  background: loading ? 'rgba(212,175,55,0.05)' : 'rgba(212,175,55,0.1)',
                  border: '1px solid #d4af37',
                  color: '#d4af37',
                  letterSpacing: '0.15em',
                  opacity: loading ? 0.6 : 1,
                }}
                whileHover={loading ? {} : { backgroundColor: 'rgba(212,175,55,0.2)' }}
              >
                ✦ {loading ? t.calculating : t.submit}
              </motion.button>
            </motion.form>
          ) : (
            <motion.div
              key="result"
              className="flex flex-col gap-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Header with name + new reading */}
              <div className="flex flex-col items-center gap-2">
                <p className="font-serif text-2xl" style={{ color: 'rgba(212,175,55,0.9)' }}>
                  {reading.full_name}
                </p>
                <p className="font-sans text-xs" style={{ color: 'rgba(201,194,224,0.45)' }}>
                  {new Date(reading.birth_date).toLocaleDateString(
                    locale === 'ru' ? 'ru-RU' : 'en-US',
                    { day: 'numeric', month: 'long', year: 'numeric' },
                  )}
                </p>
                <button
                  onClick={handleReset}
                  className="mt-2 text-[0.65rem] font-sans uppercase tracking-widest"
                  style={{
                    color: 'rgba(201,194,224,0.5)',
                    letterSpacing: '0.2em',
                  }}
                >
                  ↺ {t.new_reading}
                </button>
              </div>

              {/* Number orbs grid */}
              <div className="flex flex-wrap justify-center gap-6">
                <NumberOrb value={reading.life_path} label={t.life_path} sublabel={reading.titles.life_path} accent="#d4af37" />
                <NumberOrb value={reading.destiny} label={t.destiny} sublabel={reading.titles.destiny} accent="#c9a4d8" />
                <NumberOrb value={reading.soul_urge} label={t.soul_urge} sublabel={reading.titles.soul_urge} accent="#a8c4ea" />
                <NumberOrb value={reading.personality} label={t.personality} sublabel={reading.titles.personality} accent="#e8b88a" />
                <NumberOrb value={reading.birthday} label={t.birthday} sublabel={reading.titles.birthday} accent="#9ad9c0" />
              </div>

              {/* Life path summary */}
              {reading.life_path_summary && (
                <div
                  className="p-6 rounded-2xl text-center"
                  style={{
                    background: 'rgba(212,175,55,0.05)',
                    border: '1px solid rgba(212,175,55,0.2)',
                  }}
                >
                  <p
                    className="font-sans text-xs uppercase tracking-widest mb-3"
                    style={{ color: 'rgba(212,175,55,0.7)', letterSpacing: '0.2em' }}
                  >
                    ✦ {t.life_path} {reading.life_path}
                  </p>
                  <p
                    className="font-serif text-base leading-relaxed italic"
                    style={{ color: 'rgba(201,194,224,0.92)' }}
                  >
                    {reading.life_path_summary}
                  </p>
                </div>
              )}

              {/* AI interpretation */}
              {interpretation ? (
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
                    ✦ {t.interpret}
                  </p>
                  <div
                    className="font-serif text-sm leading-relaxed whitespace-pre-wrap"
                    style={{ color: 'rgba(201,194,224,0.9)' }}
                  >
                    {interpretation.body_md}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  {!isPremium && (
                    <p
                      className="text-xs text-center max-w-xs font-sans"
                      style={{ color: 'rgba(201,194,224,0.55)' }}
                    >
                      {t.interpret_cta}
                    </p>
                  )}
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
                    ✦ {interpreting ? t.interpreting : (isPremium ? t.interpret : t.open_pricing)}
                  </motion.button>
                </div>
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
