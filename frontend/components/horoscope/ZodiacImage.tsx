'use client';

import { useState } from 'react';

const SIGN_ORDER: Record<string, number> = {
  aries: 0, taurus: 1, gemini: 2, cancer: 3, leo: 4, virgo: 5,
  libra: 6, scorpio: 7, sagittarius: 8, capricorn: 9, aquarius: 10, pisces: 11,
};

export default function ZodiacImage({
  sign,
  symbol,
  size,
  accent,
  glow = false,
}: {
  sign: string;
  symbol: string;
  size: number;
  accent: string;
  glow?: boolean;
}) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <span
        style={{
          fontSize: size * 0.72,
          color: accent,
          lineHeight: 1,
          textShadow: glow ? `0 0 18px ${accent}cc, 0 0 36px ${accent}55` : undefined,
        }}
      >
        {symbol}
      </span>
    );
  }

  const order = SIGN_ORDER[sign] ?? 0;
  const shimmerDelay = `${(order * 0.42).toFixed(2)}s`;

  return (
    <div
      style={{
        position: 'relative',
        width: size,
        height: size,
        flexShrink: 0,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      <img
        src={`/zodiac/${sign}.png`}
        alt={sign}
        width={size}
        height={size}
        style={{
          objectFit: 'contain',
          display: 'block',
          filter: glow
            ? `drop-shadow(0 0 ${Math.round(size / 4)}px ${accent}bb) brightness(1.1)`
            : 'brightness(1.05)',
        }}
        onError={() => setFailed(true)}
      />
      <div
        className="zodiac-shimmer-overlay"
        style={{
          '--zs-delay': shimmerDelay,
          '--zs-dur': glow ? '4s' : '6s',
        } as React.CSSProperties}
      />
    </div>
  );
}
