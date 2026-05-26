'use client';

import { useEffect, useCallback, useState } from 'react';
import Image from 'next/image';
import { motion, useReducedMotion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import type { TarotCard } from '@/lib/types';

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
        className="relative w-full max-w-3xl rounded-2xl overflow-hidden"
        style={{
          background: '#0f0c24',
          border: '1px solid rgba(212,175,55,0.4)',
          maxHeight: '90vh',
          overflowY: 'auto',
        }}
        initial={prefersReducedMotion ? false : { opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={prefersReducedMotion ? {} : { opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
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
        <div className="flex flex-col md:flex-row gap-0">
          {/* Card image column */}
          <div
            className="flex-shrink-0 flex items-center justify-center bg-slate-950 p-6 md:p-8"
            style={{ minWidth: '280px' }}
          >
            <div
              className="relative rounded-xl overflow-hidden"
              style={{
                width: '200px',
                height: '300px',
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
                  <div
                    className="absolute inset-0 flex flex-col items-center justify-center gap-3"
                    style={{ background: 'linear-gradient(135deg, #2a1a5e 0%, #0b0b1f 100%)' }}
                  >
                    <span style={{ color: 'rgba(212,175,55,0.4)', fontSize: '3rem' }}>✦</span>
                    <span className="font-serif text-center px-2" style={{ color: 'rgba(212,175,55,0.6)', fontSize: '0.75rem' }}>{name}</span>
                  </div>
                ) : (
                  <Image
                    src={card.image_url}
                    alt={name}
                    fill
                    className="object-cover"
                    sizes="(max-width: 768px) 200px, 280px"
                    unoptimized
                    onError={() => setImgError(true)}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Text column */}
          <div className="flex-1 p-6 md:p-8 flex flex-col gap-4">
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
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
