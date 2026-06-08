'use client';

import { useState } from 'react';

const PLANET_SLUGS: Record<string, string> = {
  Sun:       'sun',
  Moon:      'moon',
  Mercury:   'mercury',
  Venus:     'venus',
  Mars:      'mars',
  Jupiter:   'jupiter',
  Saturn:    'saturn',
  Uranus:    'uranus',
  Neptune:   'neptune',
  Ascendant: 'ascendant',
};

const SHIMMER_ORDER: Record<string, number> = {
  sun: 0, moon: 1, mercury: 2, venus: 3, mars: 4,
  jupiter: 5, saturn: 6, uranus: 7, neptune: 8, ascendant: 9,
};

export default function PlanetImage({
  planet,
  glyph,
  size,
  glow = false,
}: {
  planet: string;        // e.g. "Sun", "Moon", "Ascendant"
  glyph: string;         // fallback unicode glyph
  size: number;
  glow?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  const slug = PLANET_SLUGS[planet];

  if (!slug || failed) {
    return (
      <span
        style={{
          fontSize: size * 0.65,
          color: '#d4af37',
          lineHeight: 1,
          textShadow: glow ? '0 0 18px rgba(212,175,55,0.8), 0 0 36px rgba(212,175,55,0.4)' : undefined,
        }}
      >
        {glyph}
      </span>
    );
  }

  const order = SHIMMER_ORDER[slug] ?? 0;
  const shimmerDelay = `${(order * 0.55).toFixed(2)}s`;

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
        // No overflow:hidden — it clips drop-shadow. Glow handled via container bg.
        ...(glow && {
          background: `radial-gradient(circle at 50% 55%, rgba(212,175,55,0.22) 0%, transparent 70%)`,
          borderRadius: '50%',
        }),
      }}
    >
      <img
        src={`/planets/${slug}.png`}
        alt={planet}
        width={size}
        height={size}
        style={{
          objectFit: 'contain',
          display: 'block',
          filter: glow
            ? `drop-shadow(0 0 ${Math.round(size / 4)}px rgba(212,175,55,0.95)) drop-shadow(0 0 ${Math.round(size / 2)}px rgba(212,175,55,0.4)) brightness(1.15)`
            : 'brightness(1.05)',
        }}
        onError={() => setFailed(true)}
      />
      <div
        className="zodiac-shimmer-overlay"
        style={{
          '--zs-delay': shimmerDelay,
          '--zs-dur': glow ? '4s' : '7s',
        } as React.CSSProperties}
      />
    </div>
  );
}
