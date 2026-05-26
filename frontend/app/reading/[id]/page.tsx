'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import ThreeCardSpread from '@/components/tarot/ThreeCardSpread';
import NineCardSpread from '@/components/tarot/NineCardSpread';
import type { ReadingResponse, SpreadPosition } from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const LOCALE = 'ru' as const;

const STAR_POSITIONS = [
  { top: '8%', left: '12%', size: '1px', opacity: 0.6 },
  { top: '15%', left: '78%', size: '2px', opacity: 0.4 },
  { top: '25%', left: '5%', size: '1px', opacity: 0.5 },
  { top: '35%', left: '92%', size: '1px', opacity: 0.7 },
  { top: '60%', left: '3%', size: '2px', opacity: 0.3 },
  { top: '70%', left: '88%', size: '1px', opacity: 0.5 },
  { top: '85%', left: '15%', size: '1px', opacity: 0.4 },
  { top: '90%', left: '70%', size: '2px', opacity: 0.3 },
] as const;

export default function ReadingPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const router = useRouter();
  const tReading = useTranslations('reading');

  const [reading, setReading] = useState<ReadingResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchReading = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/readings/${id}/`);
        if (!res.ok) throw new Error('Not found');
        const data = await res.json() as ReadingResponse;
        setReading(data);
      } catch {
        setError(true);
      }
    };
    void fetchReading();
  }, [id]);

  const spreadPositions: SpreadPosition[] = reading?.spread_type?.positions ?? [];

  if (error) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center px-4"
        style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}>
        <p className="font-serif text-sm" style={{ color: 'rgba(201,194,224,0.6)' }}>
          {tReading('error')}
        </p>
        <button
          onClick={() => router.push('/')}
          className="mt-4 text-xs underline"
          style={{ color: 'rgba(201,194,224,0.4)' }}
        >
          ↩ {tReading('shuffle')}
        </button>
      </main>
    );
  }

  if (!reading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center px-4"
        style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}>
        <motion.p
          className="font-serif italic"
          style={{ color: 'rgba(212,175,55,0.7)' }}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
        >
          {tReading('loading')}
        </motion.p>
      </main>
    );
  }

  const spreadSlug = reading.spread_type.slug;

  return (
    <main
      className="min-h-screen flex flex-col items-center px-4 py-12 md:py-20 relative overflow-x-hidden"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}
    >
      {/* Decorative stars */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
        {STAR_POSITIONS.map((star, i) => (
          <div key={i} className="absolute rounded-full"
            style={{ top: star.top, left: star.left, width: star.size, height: star.size, background: '#d4af37', opacity: star.opacity }}
          />
        ))}
      </div>

      <div className="w-full max-w-2xl flex flex-col items-center gap-10">
        {/* Divider */}
        <div className="flex items-center gap-4 w-full max-w-xs" aria-hidden="true">
          <div className="flex-1 h-px" style={{ background: 'rgba(212,175,55,0.25)' }} />
          <span style={{ color: 'rgba(212,175,55,0.5)', fontSize: '0.7rem' }}>✦</span>
          <div className="flex-1 h-px" style={{ background: 'rgba(212,175,55,0.25)' }} />
        </div>

        <motion.div
          className="w-full flex flex-col items-center gap-8"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {spreadSlug === 'nine-card' ? (
            <NineCardSpread cards={reading.cards} spreadPositions={spreadPositions} locale={LOCALE} />
          ) : (
            <ThreeCardSpread cards={reading.cards} spreadPositions={spreadPositions} locale={LOCALE} />
          )}

          <button
            onClick={() => router.push('/')}
            className="mt-4 px-6 py-2 rounded-full text-xs tracking-widest uppercase"
            style={{
              border: '1px solid rgba(212,175,55,0.3)',
              color: 'rgba(201,194,224,0.5)',
              letterSpacing: '0.12em',
            }}
          >
            ↺ {tReading('shuffle')}
          </button>
        </motion.div>
      </div>
    </main>
  );
}
