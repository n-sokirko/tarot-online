'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useLocale } from 'next-intl';
import { motion } from 'framer-motion';
import { getMyReadings } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { ReadingResponse } from '@/lib/types';

const STRINGS = {
  ru: {
    title: 'Дневник раскладов',
    subtitle: 'Все твои расклады в одном месте — вернись и перечитай',
    login: 'Войди, чтобы видеть свою историю раскладов',
    loginCta: 'Войти',
    empty: 'Пока пусто. Сделай первый расклад — он появится здесь.',
    emptyCta: 'Сделать расклад',
    noQuestion: 'Без вопроса',
    interpreted: 'разобрано',
    notInterpreted: 'без разбора',
    loading: 'Открываю дневник…',
  },
  en: {
    title: 'Reading journal',
    subtitle: 'All your readings in one place — return and re-read',
    login: 'Sign in to see your reading history',
    loginCta: 'Sign in',
    empty: 'Nothing yet. Draw your first reading — it will appear here.',
    emptyCta: 'Draw a reading',
    noQuestion: 'No question',
    interpreted: 'interpreted',
    notInterpreted: 'no reading yet',
    loading: 'Opening the journal…',
  },
} as const;

export default function HistoryPage() {
  const locale = useLocale() as 'ru' | 'en';
  const t = STRINGS[locale];
  const { user, isLoading: authLoading } = useAuth();
  const [readings, setReadings] = useState<ReadingResponse[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) { setReadings(null); return; }
    setLoading(true);
    void getMyReadings()
      .then((r) => setReadings(r))
      .catch(() => setReadings([]))
      .finally(() => setLoading(false));
  }, [user]);

  return (
    <main
      className="relative overflow-hidden min-h-screen flex flex-col items-center px-4 py-12"
      style={{ background: 'transparent' }}
    >
      <motion.div
        className="relative z-10 w-full max-w-2xl flex flex-col gap-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <header className="text-center flex flex-col gap-2">
          <p className="font-sans text-xs uppercase tracking-widest" style={{ color: 'rgba(212,175,55,0.55)', letterSpacing: '0.25em' }}>
            ✦ {t.title} ✦
          </p>
          <h1 className="font-serif text-4xl" style={{ color: '#d4af37' }}>{t.title}</h1>
          <p className="font-sans text-sm max-w-md mx-auto" style={{ color: 'rgba(201,194,224,0.7)' }}>{t.subtitle}</p>
        </header>

        {authLoading || loading ? (
          <p className="text-center font-serif italic" style={{ color: 'rgba(212,175,55,0.7)' }}>{t.loading}</p>
        ) : !user ? (
          <div className="flex flex-col items-center gap-4">
            <p className="text-center font-sans text-sm" style={{ color: 'rgba(201,194,224,0.7)' }}>{t.login}</p>
            <Link href="/login?next=/history" className="px-6 py-2.5 rounded-full text-xs tracking-widest uppercase"
              style={{ background: 'rgba(212,175,55,0.1)', border: '1px solid #d4af37', color: '#d4af37', letterSpacing: '0.15em' }}>
              ✦ {t.loginCta}
            </Link>
          </div>
        ) : readings && readings.length === 0 ? (
          <div className="flex flex-col items-center gap-4">
            <p className="text-center font-sans text-sm" style={{ color: 'rgba(201,194,224,0.6)' }}>{t.empty}</p>
            <Link href="/" className="px-6 py-2.5 rounded-full text-xs tracking-widest uppercase"
              style={{ background: 'rgba(212,175,55,0.1)', border: '1px solid #d4af37', color: '#d4af37', letterSpacing: '0.15em' }}>
              ✦ {t.emptyCta}
            </Link>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {readings?.map((r) => {
              const done = r.interpretation !== null;
              return (
                <Link key={r.id} href={`/reading/${r.id}`}
                  className="flex flex-col gap-1.5 p-4 rounded-2xl transition-colors hover:bg-[rgba(212,175,55,0.08)]"
                  style={{ background: 'rgba(212,175,55,0.04)', border: '1px solid rgba(212,175,55,0.18)' }}>
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-serif text-base" style={{ color: 'rgba(201,194,224,0.95)' }}>
                      {r.question?.trim() || t.noQuestion}
                    </span>
                    <span className="font-sans text-[0.6rem] uppercase tracking-wider shrink-0 px-2 py-0.5 rounded-full"
                      style={{
                        color: done ? '#d4af37' : 'rgba(201,194,224,0.45)',
                        border: `1px solid ${done ? 'rgba(212,175,55,0.4)' : 'rgba(201,194,224,0.2)'}`,
                      }}>
                      {done ? t.interpreted : t.notInterpreted}
                    </span>
                  </div>
                  <span className="font-sans text-xs" style={{ color: 'rgba(201,194,224,0.45)' }}>
                    {r.cards?.length ?? r.spread_type?.positions?.length ?? ''} {locale === 'ru' ? 'карт' : 'cards'}
                    {' · '}
                    {new Date(r.created_at).toLocaleDateString(locale === 'ru' ? 'ru-RU' : 'en-US', {
                      day: 'numeric', month: 'long', year: 'numeric',
                    })}
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </motion.div>
    </main>
  );
}
