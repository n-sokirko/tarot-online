'use client';

import { useEffect, useCallback, useState } from 'react';
import Image from 'next/image';
import { motion, useReducedMotion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import type { TarotCard } from '@/lib/types';

const SUIT_SHIMMER: Record<string, { color: string; duration: string }> = {
  major:     { color: 'rgba(212,175,55,0.22)',  duration: '4s' },
  wands:     { color: 'rgba(255,110,40,0.22)',  duration: '3.5s' },
  cups:      { color: 'rgba(60,160,230,0.22)',  duration: '4.5s' },
  swords:    { color: 'rgba(180,210,240,0.22)', duration: '3.8s' },
  pentacles: { color: 'rgba(80,190,100,0.22)',  duration: '4.2s' },
};

interface CardDetailModalProps {
  card: TarotCard;
  isReversed: boolean;
  positionLabel: string;
  positionMeaning: string;
  locale: 'ru' | 'en';
  onClose: () => void;
}

export default function CardDetailModal({
  card,
  isReversed,
  positionLabel,
  positionMeaning,
  locale,
  onClose,
}: CardDetailModalProps) {
  const t = useTranslations('card');
  const prefersReducedMotion = useReducedMotion();
  const [imgError, setImgError] = useState(false);

  const name = locale === 'ru' ? card.name_ru : card.name_en;
  const meaning = isReversed
    ? locale === 'ru'
      ? card.reversed_meaning_ru
      : card.reversed_meaning_en
    : locale === 'ru'
      ? card.upright_meaning_ru
      : card.upright_meaning_en;
  const keywords = locale === 'ru' ? card.keywords_ru : card.keywords_en;

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    // Prevent body scroll while modal is open
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);

  return (
    /* Backdrop */
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0,0,0,0.85)' }}
      initial={prefersReducedMotion ? false : { opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={prefersReducedMotion ? {} : { opacity: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      onClick={onClose}
      aria-modal="true"
      role="dialog"
      aria-label={name}
    >
      {/* Panel — stop propagation so clicking inside doesn't close */}
      <motion.div
        className="relative w-full max-w-3xl rounded-2xl flex flex-col"
        style={{
          background: '#0f0c24',
          border: '1px solid rgba(212,175,55,0.4)',
          maxHeight: '90vh',
          overflow: 'hidden',
        }}
        initial={prefersReducedMotion ? false : { opacity: 0, scale: 0.85, y: 30 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={prefersReducedMotion ? {} : { opacity: 0, scale: 0.85, y: 30 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          className="absolute top-4 right-4 z-10 text-white/50 hover:text-white transition-colors text-2xl leading-none"
          onClick={onClose}
          aria-label={t('close')}
        >
          ✕
        </button>

        {/* Content grid: image LEFT, text RIGHT */}
        <div className="flex flex-col md:flex-row flex-1 min-h-0">
          {/* Card image column — fills full panel height */}
          <div
            className="flex-shrink-0 flex flex-col bg-slate-950 p-4 md:p-6"
            style={{ width: '260px' }}
          >
            <div
              className="relative rounded-xl overflow-hidden flex-1"
              style={{
                minHeight: '340px',
                border: '2px solid #d4af37',
              }}
            >
              <div
                className="absolute inset-0"
                style={{
                  transform: isReversed ? 'rotate(180deg)' : undefined,
                  transition: 'transform 0.3s ease',
                }}
              >
                {imgError ? (
                  /* Ornamental golden placeholder */
                  <div
                    className="absolute inset-0 flex flex-col items-center justify-center gap-4"
                    style={{ background: 'linear-gradient(135deg, #1e1245 0%, #0b0b1f 100%)' }}
                  >
                    <svg
                      width="96"
                      height="96"
                      viewBox="0 0 96 96"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                      aria-hidden="true"
                    >
                      {/* Outer circle */}
                      <circle cx="48" cy="48" r="44" stroke="rgba(212,175,55,0.35)" strokeWidth="1" />
                      {/* Middle circle */}
                      <circle cx="48" cy="48" r="32" stroke="rgba(212,175,55,0.25)" strokeWidth="1" />
                      {/* Inner circle */}
                      <circle cx="48" cy="48" r="18" stroke="rgba(212,175,55,0.2)" strokeWidth="1" />
                      {/* Eight spokes */}
                      {[0, 45, 90, 135].map((deg) => (
                        <line
                          key={deg}
                          x1="48"
                          y1="5"
                          x2="48"
                          y2="91"
                          stroke="rgba(212,175,55,0.4)"
                          strokeWidth="0.75"
                          transform={`rotate(${deg} 48 48)`}
                        />
                      ))}
                      {/* Compass tip diamonds */}
                      {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
                        const rad = (deg * Math.PI) / 180;
                        const cx = 48 + 44 * Math.sin(rad);
                        const cy = 48 - 44 * Math.cos(rad);
                        return (
                          <circle
                            key={deg}
                            cx={cx}
                            cy={cy}
                            r="2.5"
                            fill="rgba(212,175,55,0.5)"
                          />
                        );
                      })}
                      {/* Mid-ring accent dots */}
                      {[22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5].map((deg) => {
                        const rad = (deg * Math.PI) / 180;
                        const cx = 48 + 32 * Math.sin(rad);
                        const cy = 48 - 32 * Math.cos(rad);
                        return (
                          <circle
                            key={deg}
                            cx={cx}
                            cy={cy}
                            r="1.5"
                            fill="rgba(212,175,55,0.3)"
                          />
                        );
                      })}
                      {/* Central orb */}
                      <circle cx="48" cy="48" r="5" fill="rgba(212,175,55,0.5)" />
                    </svg>
                    <span
                      className="font-serif text-center px-4 leading-snug"
                      style={{ color: '#d4af37', fontSize: '0.85rem' }}
                    >
                      {name}
                    </span>
                  </div>
                ) : (
                  <>
                    <Image
                      src={card.image_url}
                      alt={name}
                      fill
                      className="object-cover object-top"
                      sizes="(max-width: 768px) 240px, 280px"
                      unoptimized
                      onError={() => setImgError(true)}
                    />
                    <div
                      className="card-shimmer absolute inset-0 overflow-hidden"
                      style={{
                        ['--shimmer-color' as string]: SUIT_SHIMMER[card.suit]?.color ?? 'rgba(212,175,55,0.22)',
                        ['--shimmer-duration' as string]: SUIT_SHIMMER[card.suit]?.duration ?? '4s',
                        ['--shimmer-delay' as string]: '0.5s',
                      }}
                    />
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Text column — scrolls if content overflows */}
          <div className="flex-1 p-6 md:p-8 flex flex-col gap-4 overflow-y-auto">
            {/* Position label */}
            {positionLabel && (
              <p
                className="text-xs font-sans uppercase tracking-widest"
                style={{ color: 'rgba(212,175,55,0.65)', letterSpacing: '0.15em' }}
              >
                {t('position_context')}: {positionLabel}
              </p>
            )}

            {/* Card name */}
            <h2
              className="font-serif text-2xl md:text-3xl leading-tight"
              style={{ color: '#d4af37' }}
            >
              {name}
            </h2>

            {/* Reversed badge */}
            {isReversed && (
              <span
                className="self-start text-xs font-sans px-3 py-1 rounded-full"
                style={{
                  color: '#d4af37',
                  border: '1px solid rgba(212,175,55,0.5)',
                  background: 'rgba(212,175,55,0.08)',
                }}
              >
                {t('reversed')}
              </span>
            )}

            {/* Position meaning (context) */}
            {positionMeaning && (
              <p
                className="text-sm leading-relaxed italic"
                style={{ color: 'rgba(201,194,224,0.55)' }}
              >
                {positionMeaning}
              </p>
            )}

            {/* Full card meaning */}
            <p
              className="text-sm md:text-base leading-relaxed"
              style={{ color: 'rgba(201,194,224,0.9)' }}
            >
              {meaning}
            </p>

            {/* Keywords */}
            {keywords.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-auto pt-2">
                {keywords.map((kw) => (
                  <span
                    key={kw}
                    className="text-xs rounded-full px-3 py-1"
                    style={{
                      color: 'rgba(212,175,55,0.6)',
                      border: '1px solid rgba(212,175,55,0.4)',
                      background: 'rgba(212,175,55,0.06)',
                    }}
                  >
                    {kw}
                  </span>
                ))}
              </div>
            )}

            {/* Premium AI interpretation placeholder */}
            <div className="mt-4 pt-4" style={{ borderTop: '1px solid rgba(212,175,55,0.15)' }}>
              <button
                disabled
                className="w-full py-3 px-4 rounded-xl font-serif text-sm tracking-wide flex items-center justify-center gap-2 cursor-not-allowed"
                style={{
                  background: 'rgba(212,175,55,0.05)',
                  border: '1px solid rgba(212,175,55,0.2)',
                  color: 'rgba(212,175,55,0.4)',
                }}
              >
                <span>✦</span>
                <span>{t('interpret_cta')}</span>
                <span style={{ fontSize: '0.65rem', marginLeft: 'auto', opacity: 0.6 }}>
                  {t('interpret_soon')}
                </span>
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
