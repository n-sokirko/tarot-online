'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { getRuneCast } from '@/lib/api';
import RuneCastBoard from '@/components/runes/RuneCastBoard';
import RuneInterpretationPanel from '@/components/runes/RuneInterpretationPanel';
import type { RuneCastResponse } from '@/lib/types';

const LOCALE = 'ru' as const;

const t = {
  ru: { loading: 'Руны раскрываются...', back: 'Бросить снова', error: 'Не получилось загрузить бросок.' },
  en: { loading: 'The runes are revealing...', back: 'Cast again', error: 'Failed to load the cast.' },
}[LOCALE];

export default function RuneCastPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [cast, setCast] = useState<RuneCastResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getRuneCast(params.id)
      .then(setCast)
      .catch(() => setError(true));
  }, [params.id]);

  if (error) {
    return (
      <main
        className="min-h-screen flex flex-col items-center justify-center"
        style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}
      >
        <p className="font-serif text-sm" style={{ color: 'rgba(201,194,224,0.6)' }}>
          {t.error}
        </p>
      </main>
    );
  }

  if (!cast) {
    return (
      <main
        className="min-h-screen flex flex-col items-center justify-center"
        style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}
      >
        <motion.p
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          className="font-serif italic"
          style={{ color: 'rgba(212,175,55,0.7)' }}
        >
          {t.loading}
        </motion.p>
      </main>
    );
  }

  return (
    <main
      className="min-h-screen px-4 py-12 md:py-16"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}
    >
      <div className="max-w-3xl mx-auto flex flex-col items-center gap-8">
        <RuneCastBoard
          layout={cast.layout}
          items={cast.items}
          positions={cast.positions}
          locale={LOCALE}
        />

        <RuneInterpretationPanel
          castId={cast.id}
          locale={LOCALE}
          initial={cast.interpretation}
        />

        <button
          onClick={() => router.push('/runes')}
          className="mt-4 px-6 py-2 rounded-full text-xs tracking-widest uppercase"
          style={{
            border: '1px solid rgba(212,175,55,0.3)',
            color: 'rgba(201,194,224,0.5)',
            letterSpacing: '0.12em',
          }}
        >
          ↺ {t.back}
        </button>
      </div>
    </main>
  );
}
