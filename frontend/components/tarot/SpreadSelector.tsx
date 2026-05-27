'use client';

import { motion, useReducedMotion } from 'framer-motion';
import { useTranslations } from 'next-intl';

export type SpreadSlug = 'three-card' | 'nine-card' | 'celtic-cross';

interface SpreadOption {
  slug: SpreadSlug;
  nameKey: string;
  descKey: string;
  cardsKey: string;
  premium: boolean;
  /** Entitlement key required to unlock when premium. */
  entitlement?: string;
  symbol: string;
}

const SPREADS: SpreadOption[] = [
  {
    slug: 'three-card',
    nameKey: 'spread_3_name',
    descKey: 'spread_3_desc',
    cardsKey: 'spread_3_cards',
    premium: false,
    symbol: '✦ ✦ ✦',
  },
  {
    slug: 'nine-card',
    nameKey: 'spread_9_name',
    descKey: 'spread_9_desc',
    cardsKey: 'spread_9_cards',
    premium: false,
    symbol: '✦ ✦ ✦\n✦ ✦ ✦\n✦ ✦ ✦',
  },
  {
    slug: 'celtic-cross',
    nameKey: 'spread_celtic_name',
    descKey: 'spread_celtic_desc',
    cardsKey: 'spread_celtic_cards',
    premium: true,
    entitlement: 'celtic_cross',
    symbol: '  ✦\n✦✦✦  ✦\n  ✦    ✦\n       ✦',
  },
];

interface SpreadSelectorProps {
  onSelect: (slug: SpreadSlug) => void;
  /** Entitlement keys the current user has — used to unlock premium spreads. */
  entitlements?: readonly string[];
}

export default function SpreadSelector({ onSelect, entitlements = [] }: SpreadSelectorProps) {
  const t = useTranslations('reading');
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      className="w-full max-w-2xl flex flex-col items-center gap-8"
      initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      <p
        className="font-serif text-sm tracking-widest uppercase text-center"
        style={{ color: 'rgba(212,175,55,0.7)', letterSpacing: '0.2em' }}
      >
        {t('choose_spread')}
      </p>

      <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-4">
        {SPREADS.map((spread, i) => {
          const unlocked =
            !spread.premium ||
            (spread.entitlement !== undefined &&
              entitlements.includes(spread.entitlement));
          const isLocked = !unlocked;

          return (
            <motion.button
              key={spread.slug}
              disabled={isLocked}
              onClick={() => unlocked && onSelect(spread.slug)}
              className="relative flex flex-col items-center gap-4 p-6 rounded-2xl text-left transition-all"
              style={{
                background: isLocked
                  ? 'rgba(212,175,55,0.03)'
                  : 'rgba(212,175,55,0.06)',
                border: isLocked
                  ? '1px solid rgba(212,175,55,0.15)'
                  : '1px solid rgba(212,175,55,0.35)',
                cursor: isLocked ? 'not-allowed' : 'pointer',
                opacity: isLocked ? 0.6 : 1,
              }}
              initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: isLocked ? 0.6 : 1, y: 0 }}
              transition={{ delay: i * 0.12, duration: 0.4 }}
              whileHover={
                isLocked || prefersReducedMotion
                  ? {}
                  : {
                      scale: 1.03,
                      borderColor: 'rgba(212,175,55,0.7)',
                      background: 'rgba(212,175,55,0.1)',
                    }
              }
              whileTap={isLocked || prefersReducedMotion ? {} : { scale: 0.98 }}
            >
              {spread.premium && (
                <span
                  className="absolute top-3 right-3 text-xs px-2 py-0.5 rounded-full font-sans"
                  style={{
                    background: 'rgba(212,175,55,0.15)',
                    color: 'rgba(212,175,55,0.7)',
                    border: '1px solid rgba(212,175,55,0.3)',
                    fontSize: '0.6rem',
                    letterSpacing: '0.1em',
                  }}
                >
                  {t('premium_badge')}
                </span>
              )}

              {/* Symbol grid — fixed height so names align across cards */}
              <div className="flex items-center justify-center" style={{ height: '64px' }}>
                <div
                  className="font-serif text-center leading-relaxed whitespace-pre-line"
                  style={{
                    color: isLocked ? 'rgba(212,175,55,0.3)' : 'rgba(212,175,55,0.5)',
                    fontSize: spread.slug === 'nine-card' || spread.slug === 'celtic-cross' ? '0.6rem' : '1rem',
                    letterSpacing: '0.3em',
                    lineHeight: spread.slug === 'nine-card' || spread.slug === 'celtic-cross' ? '1.8' : '1',
                  }}
                >
                  {spread.symbol}
                </div>
              </div>

              <div className="flex flex-col items-center gap-1 text-center">
                <p
                  className="font-serif text-base"
                  style={{ color: isLocked ? 'rgba(212,175,55,0.4)' : '#d4af37' }}
                >
                  {t(spread.nameKey)}
                </p>
                <p
                  className="text-xs leading-relaxed"
                  style={{ color: 'rgba(201,194,224,0.55)' }}
                >
                  {t(spread.descKey)}
                </p>
                <p
                  className="text-xs mt-1"
                  style={{
                    color: isLocked ? 'rgba(212,175,55,0.3)' : 'rgba(212,175,55,0.5)',
                    letterSpacing: '0.08em',
                  }}
                >
                  {isLocked ? t('premium_locked') : t(spread.cardsKey)}
                </p>
              </div>
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}
