'use client';

import { useState } from 'react';

/**
 * Renders a zodiac sign as an image from /public/zodiac/{slug}.png.
 * Falls back to the Unicode glyph if the image is missing — so it works both
 * before and after the artwork is uploaded.
 */
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

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={`/zodiac/${sign}.png`}
      alt={sign}
      width={size}
      height={size}
      style={{
        objectFit: 'contain',
        filter: glow ? `drop-shadow(0 0 14px ${accent}aa)` : undefined,
      }}
      onError={() => setFailed(true)}
    />
  );
}
