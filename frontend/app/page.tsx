'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import DeckPile from '@/components/tarot/DeckPile';
import ThreeCardSpread from '@/components/tarot/ThreeCardSpread';
import NineCardSpread from '@/components/tarot/NineCardSpread';
import SpreadSelector, { type SpreadSlug } from '@/components/tarot/SpreadSelector';
import { createReading } from '@/lib/api';
import type { ReadingResponse, SpreadPosition } from '@/lib/types';

type PageState = 'selecting' | 'idle' | 'shuffled' | 'loading' | 'spread' | 'error';

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

export default function HomePage() {
  const t = useTranslations('home');
  const tReading = useTranslations('reading');
  const prefersReducedMotion = useReducedMotion();

  const [pageState, setPageState] = useState<PageState>('selecting');
  const [selectedSpread, setSelectedSpread] = useState<SpreadSlug>('three-card');
  const [reading, setReading] = useState<ReadingResponse | null>(null);
  const [sessionKey, setSessionKey] = useState(0);

  const handleSpreadSelect = useCallback((slug: SpreadSlug) => {
    setSelectedSpread(slug);
    setPageState('idle');
  }, []);

  const handleShuffleComplete = useCallback(() => {
    setPageState('shuffled');
  }, []);

  const handleDraw = useCallback(async () => {
    setPageState('loading');
    try {
      const result = await createReading(LOCALE, selectedSpread);
      setReading(result);
      setPageState('spread');
    } catch {
      setPageState('error');
    }
  }, [selectedSpread]);

  const handleReset = useCallback(() => {
    setReading(null);
    setPageState('selecting');
    setSessionKey((k) => k + 1);
  }, []);

  const spreadPositions: SpreadPosition[] =
    reading?.spread_type?.positions ?? [];

  return (
    <main
      className="min-h-screen flex flex-col items-center px-4 py-12 md:py-20 relative overflow-x-hidden"
      style={{
        background:
          'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)',
      }}
    >
      {/* Decorative stars */}
      <div
        className="pointer-events-none absolute inset-0 overflow-hidden"
        aria-hidden="true"
      >
        {STAR_POSITIONS.map((star, i) => (
          <div
            key={i}
            className="absolute rounded-full"
            style={{
              top: star.top,
              left: star.left,
              width: star.size,
              height: star.size,
              background: '#d4af37',
              opacity: star.opacity,
            }}
          />
        ))}
      </div>

      {/* Hero */}
      <motion.header
        className="text-center mb-10 md:mb-14 max-w-xl"
        initial={prefersReducedMotion ? false : { opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: 'easeOut' }}
      >
        <h1
          className="font-serif text-4xl md:text-6xl lg:text-7xl leading-tight mb-4"
          style={{ color: '#d4af37', textShadow: '0 0 40px rgba(212,175,55,0.2)' }}
        >
          {t('title')}
        </h1>
        <p
          className="font-serif text-base md:text-lg italic"
          style={{ color: 'rgba(201,194,224,0.75)' }}
        >
          {t('subtitle')}
        </p>
        <p
          className="mt-3 text-sm tracking-widest uppercase"
          style={{ color: 'rgba(201,194,224,0.4)', letterSpacing: '0.15em' }}
        >
          {t('description')}
        </p>
      </motion.header>

      {/* Main content */}
      <div className="w-full max-w-2xl flex flex-col items-center gap-10">

        {/* Step 0: Spread selector */}
        <AnimatePresence mode="wait">
          {pageState === 'selecting' && (
            <motion.div
              key="selector"
              initial={prefersReducedMotion ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={prefersReducedMotion ? {} : { opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.35 }}
            >
              <SpreadSelector key={sessionKey} onSelect={handleSpreadSelect} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Step 1: Deck + Shuffle */}
        <AnimatePresence mode="wait">
          {pageState !== 'selecting' && pageState !== 'spread' && (
            <motion.div
              key="deck"
              className="flex flex-col items-center gap-8"
              initial={prefersReducedMotion ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={prefersReducedMotion ? {} : { opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.4 }}
            >
              <DeckPile
                key={sessionKey}
                onShuffleComplete={handleShuffleComplete}
              />

              <AnimatePresence mode="wait">
                {pageState === 'shuffled' && (
                  <motion.div
                    key="draw-btn"
                    className="flex flex-col items-center gap-3"
                    initial={prefersReducedMotion ? false : { opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={prefersReducedMotion ? {} : { opacity: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                  >
                    <p
                      className="font-serif text-sm italic text-center"
                      style={{ color: 'rgba(201,194,224,0.6)' }}
                    >
                      {tReading('draw_prompt')}
                    </p>
                    <motion.button
                      className="px-10 py-3 rounded-full font-serif text-sm tracking-widest uppercase"
                      style={{
                        background: 'rgba(212,175,55,0.1)',
                        border: '1px solid #d4af37',
                        color: '#d4af37',
                        letterSpacing: '0.15em',
                      }}
                      whileHover={
                        prefersReducedMotion
                          ? {}
                          : {
                              scale: 1.05,
                              backgroundColor: 'rgba(212,175,55,0.2)',
                              boxShadow: '0 0 20px rgba(212,175,55,0.2)',
                            }
                      }
                      whileTap={prefersReducedMotion ? {} : { scale: 0.97 }}
                      onClick={() => void handleDraw()}
                    >
                      {tReading('draw')}
                    </motion.button>
                  </motion.div>
                )}

                {pageState === 'loading' && (
                  <motion.p
                    key="loading"
                    className="font-serif italic text-center"
                    style={{ color: 'rgba(212,175,55,0.7)' }}
                    initial={prefersReducedMotion ? false : { opacity: 0 }}
                    animate={
                      prefersReducedMotion
                        ? { opacity: 1 }
                        : { opacity: [0.4, 1, 0.4] }
                    }
                    transition={
                      prefersReducedMotion
                        ? {}
                        : { duration: 1.5, repeat: Infinity, ease: 'easeInOut' }
                    }
                  >
                    {tReading('loading')}
                  </motion.p>
                )}

                {pageState === 'error' && (
                  <motion.div
                    key="error"
                    className="flex flex-col items-center gap-3"
                    initial={prefersReducedMotion ? false : { opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <p
                      className="text-sm text-center"
                      style={{ color: 'rgba(160,44,44,0.9)' }}
                    >
                      {tReading('error')}
                    </p>
                    <button
                      className="text-xs underline"
                      style={{ color: 'rgba(201,194,224,0.5)' }}
                      onClick={handleReset}
                    >
                      ↺
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Step 2: Card spread */}
        <AnimatePresence>
          {pageState === 'spread' && reading !== null && (
            <motion.div
              key="spread"
              className="w-full flex flex-col items-center gap-8"
              initial={prefersReducedMotion ? false : { opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div
                className="flex items-center gap-4 w-full max-w-xs"
                aria-hidden="true"
              >
                <div
                  className="flex-1 h-px"
                  style={{ background: 'rgba(212,175,55,0.25)' }}
                />
                <span style={{ color: 'rgba(212,175,55,0.5)', fontSize: '0.7rem' }}>
                  ✦
                </span>
                <div
                  className="flex-1 h-px"
                  style={{ background: 'rgba(212,175,55,0.25)' }}
                />
              </div>

              {selectedSpread === 'nine-card' ? (
                <NineCardSpread
                  cards={reading.cards}
                  spreadPositions={spreadPositions}
                  locale={LOCALE}
                />
              ) : (
                <ThreeCardSpread
                  cards={reading.cards}
                  spreadPositions={spreadPositions}
                  locale={LOCALE}
                />
              )}

              <motion.button
                className="mt-4 px-6 py-2 rounded-full text-xs tracking-widest uppercase"
                style={{
                  border: '1px solid rgba(212,175,55,0.3)',
                  color: 'rgba(201,194,224,0.5)',
                  letterSpacing: '0.12em',
                }}
                whileHover={
                  prefersReducedMotion
                    ? {}
                    : {
                        borderColor: 'rgba(212,175,55,0.6)',
                        color: 'rgba(201,194,224,0.8)',
                      }
                }
                onClick={handleReset}
              >
                ↺ {tReading('shuffle')}
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <footer
        className="mt-auto pt-16 text-center"
        style={{
          color: 'rgba(201,194,224,0.25)',
          fontSize: '0.65rem',
          letterSpacing: '0.1em',
        }}
      >
        TAROT ONLINE · {new Date().getFullYear()}
      </footer>
    </main>
  );
}
