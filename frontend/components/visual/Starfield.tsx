'use client';

/**
 * Starfield — a decorative cosmic background layer.
 *
 * Renders twinkling stars + a couple of slowly rotating glow orbs, all on pure
 * CSS keyframes (no per-frame JS). Star positions are deterministic (seeded by
 * `seed`) so server and client render identical markup — no hydration drift.
 *
 * Drop it as the first child of a `position: relative` container and keep the
 * real content above it (e.g. wrap content in `relative z-10`). It is purely
 * decorative and ignores pointer events.
 */

import type { CSSProperties } from 'react';

function seededRandom(seedStr: string) {
  let h = 1779033703 ^ seedStr.length;
  for (let i = 0; i < seedStr.length; i++) {
    h = Math.imul(h ^ seedStr.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  let a = h >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export default function Starfield({
  seed = 'tarot',
  count = 48,
  orbs = true,
}: {
  seed?: string;
  count?: number;
  orbs?: boolean;
}) {
  const rng = seededRandom(seed);
  const stars = Array.from({ length: count }, () => ({
    top: +(rng() * 100).toFixed(2),
    left: +(rng() * 100).toFixed(2),
    size: +(rng() * 1.6 + 0.6).toFixed(2),
    dur: +(rng() * 3.5 + 2).toFixed(2),
    delay: +(rng() * 5).toFixed(2),
    min: +(rng() * 0.15 + 0.08).toFixed(2),
    gold: rng() > 0.78, // a few warm golden stars
  }));

  return (
    <div
      aria-hidden
      className="absolute inset-0 overflow-hidden pointer-events-none"
      style={{ zIndex: 0 }}
    >
      {/* Rotating glow orbs */}
      {orbs && (
        <>
          <div
            className="absolute rounded-full"
            style={{
              top: '-10%', left: '-8%', width: '46vw', height: '46vw', maxWidth: 520, maxHeight: 520,
              background: 'radial-gradient(circle, rgba(212,175,55,0.10) 0%, transparent 65%)',
              animation: 'slow-spin 80s linear infinite, glow-pulse 9s ease-in-out infinite',
            }}
          />
          <div
            className="absolute rounded-full"
            style={{
              bottom: '-14%', right: '-10%', width: '52vw', height: '52vw', maxWidth: 600, maxHeight: 600,
              background: 'radial-gradient(circle, rgba(150,120,210,0.10) 0%, transparent 65%)',
              animation: 'slow-spin 110s linear infinite reverse, glow-pulse 11s ease-in-out infinite',
            }}
          />
        </>
      )}

      {/* Twinkling stars */}
      {stars.map((s, i) => (
        <span
          key={i}
          className="absolute rounded-full"
          style={{
            top: `${s.top}%`,
            left: `${s.left}%`,
            width: s.size,
            height: s.size,
            background: s.gold ? 'rgba(212,175,55,0.9)' : 'rgba(255,255,255,0.9)',
            boxShadow: s.gold ? '0 0 4px rgba(212,175,55,0.7)' : '0 0 3px rgba(255,255,255,0.5)',
            '--tw-min': s.min,
            '--tw-max': 0.9,
            animation: `star-twinkle ${s.dur}s ease-in-out ${s.delay}s infinite`,
          } as CSSProperties}
        />
      ))}
    </div>
  );
}
