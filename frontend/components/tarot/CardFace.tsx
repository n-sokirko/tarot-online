'use client';

import Image from 'next/image';
import { useState } from 'react';
import type { TarotCard } from '@/lib/types';

interface CardFaceProps {
  card: TarotCard;
  isReversed: boolean;
  locale: 'ru' | 'en';
  className?: string;
}

export default function CardFace({
  card,
  isReversed,
  locale,
  className = '',
}: CardFaceProps) {
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

  return (
    <div
      className={`relative flex-shrink-0 ${className}`}
      style={{ width: '100%', aspectRatio: '2 / 3' }}
    >
      <div
        className="absolute inset-0 rounded-xl overflow-hidden flex flex-col"
        style={{
          background: 'linear-gradient(135deg, #1e1245 0%, #0b0b1f 100%)',
          border: '2px solid #d4af37',
        }}
      >
        {/* Card image area */}
        <div
          className="relative flex-1 min-h-0"
          style={{ transform: isReversed ? 'rotate(180deg)' : undefined }}
        >
          {imgError ? (
            /* Placeholder when image fails */
            <div
              className="absolute inset-0 flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #2a1a5e 0%, #0b0b1f 100%)',
              }}
            >
              <span
                className="text-4xl"
                style={{ color: 'rgba(212,175,55,0.3)' }}
              >
                ✦
              </span>
            </div>
          ) : (
            <Image
              src={card.image_url}
              alt={name}
              fill
              className="object-cover"
              onError={() => setImgError(true)}
              sizes="(max-width: 768px) 40vw, 200px"
              unoptimized
            />
          )}
        </div>

        {/* Card info footer */}
        <div className="px-2 py-2 flex flex-col gap-1" style={{ flexShrink: 0 }}>
          {/* Name */}
          <p
            className="font-serif text-center leading-tight truncate"
            style={{ color: '#d4af37', fontSize: '0.7rem' }}
          >
            {name}
            {isReversed && (
              <span className="ml-1 opacity-60">↕</span>
            )}
          </p>

          {/* Keywords */}
          <div className="flex flex-wrap gap-1 justify-center">
            {keywords.slice(0, 2).map((kw) => (
              <span
                key={kw}
                className="rounded-full px-1.5 py-0.5 leading-none"
                style={{
                  background: 'rgba(212,175,55,0.12)',
                  color: 'rgba(212,175,55,0.8)',
                  border: '1px solid rgba(212,175,55,0.25)',
                  fontSize: '0.55rem',
                }}
              >
                {kw}
              </span>
            ))}
          </div>

          {/* Short meaning */}
          <p
            className="text-center leading-tight line-clamp-2"
            style={{
              color: '#c9c2e0',
              fontSize: '0.55rem',
              opacity: 0.8,
            }}
          >
            {meaning}
          </p>
        </div>
      </div>
    </div>
  );
}
