'use client';

/**
 * ZodiacConstellation — an animated, lightweight SVG visual for a zodiac sign.
 *
 * Three layers, all pure SVG + CSS keyframes (no per-frame JS, no heavy GIFs):
 *   1. a drifting, twinkling starfield (deterministic positions → SSR-stable)
 *   2. the sign's constellation — stars joined by faint lines that draw in
 *   3. the large sign glyph with a soft pulsing halo
 *
 * Positions for the starfield are generated from a seed derived from the sign
 * slug, so the server and client render identical markup (no hydration drift).
 */

import type { CSSProperties } from 'react';
import ZodiacImage from './ZodiacImage';

type Pt = [number, number];
interface Pattern {
  points: Pt[];
  edges: [number, number][];
}

// Simplified, evocative star patterns in a 0–100 viewBox (not astronomically exact).
const CONSTELLATIONS: Record<string, Pattern> = {
  aries: { points: [[18, 62], [42, 46], [68, 40], [85, 54]], edges: [[0, 1], [1, 2], [2, 3]] },
  taurus: { points: [[50, 62], [35, 46], [18, 30], [66, 45], [84, 27]], edges: [[0, 1], [1, 2], [0, 3], [3, 4]] },
  gemini: { points: [[30, 20], [33, 50], [36, 80], [66, 22], [69, 50], [72, 80]], edges: [[0, 1], [1, 2], [3, 4], [4, 5], [0, 3], [2, 5]] },
  cancer: { points: [[50, 26], [48, 52], [28, 74], [70, 70]], edges: [[0, 1], [1, 2], [1, 3]] },
  leo: { points: [[80, 30], [62, 24], [48, 34], [44, 50], [56, 64], [80, 62]], edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]] },
  virgo: { points: [[16, 40], [38, 50], [58, 44], [74, 60], [88, 54]], edges: [[0, 1], [1, 2], [2, 3], [3, 4]] },
  libra: { points: [[50, 28], [26, 54], [74, 54], [18, 72], [82, 72]], edges: [[0, 1], [0, 2], [1, 3], [2, 4]] },
  scorpio: { points: [[16, 30], [28, 42], [42, 50], [56, 52], [70, 48], [80, 60], [72, 74], [56, 78]], edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7]] },
  sagittarius: { points: [[24, 56], [40, 40], [56, 34], [72, 46], [56, 62], [40, 62]], edges: [[0, 1], [1, 2], [2, 3], [1, 5], [2, 4]] },
  capricorn: { points: [[24, 40], [80, 32], [54, 74]], edges: [[0, 1], [1, 2], [2, 0]] },
  aquarius: { points: [[16, 42], [34, 56], [50, 42], [66, 56], [84, 42]], edges: [[0, 1], [1, 2], [2, 3], [3, 4]] },
  pisces: { points: [[18, 28], [38, 48], [58, 56], [80, 42], [54, 76]], edges: [[0, 1], [1, 2], [2, 3], [2, 4]] },
};

// Tiny deterministic PRNG (mulberry32) seeded from the sign slug.
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

export default function ZodiacConstellation({
  sign,
  symbol,
  accent,
}: {
  sign: string;
  symbol: string;
  accent: string;
}) {
  const pat = CONSTELLATIONS[sign] ?? CONSTELLATIONS.aries;

  // Deterministic starfield dots.
  const rng = seededRandom(sign);
  const stars = Array.from({ length: 26 }, () => ({
    cx: +(rng() * 100).toFixed(2),
    cy: +(rng() * 100).toFixed(2),
    r: +(rng() * 0.7 + 0.25).toFixed(2),
    dur: +(rng() * 3 + 2.2).toFixed(2),
    delay: +(rng() * 4).toFixed(2),
    min: +(rng() * 0.2 + 0.1).toFixed(2),
  }));

  return (
    <div
      className="relative w-full mx-auto"
      style={{ maxWidth: 320, height: 180 }}
      aria-hidden
    >
      {/* Drifting starfield + constellation */}
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid meet"
        className="absolute inset-0 w-full h-full"
        style={{ overflow: 'visible' }}
      >
        <g style={{ animation: 'cosmic-drift 14s ease-in-out infinite alternate' }}>
          {stars.map((s, i) => (
            <circle
              key={i}
              cx={s.cx}
              cy={s.cy}
              r={s.r}
              fill="rgba(255,255,255,0.85)"
              style={{
                '--tw-min': s.min,
                '--tw-max': 0.9,
                animation: `star-twinkle ${s.dur}s ease-in-out ${s.delay}s infinite`,
              } as CSSProperties}
            />
          ))}
        </g>

        {/* Constellation lines (draw in, staggered) */}
        {pat.edges.map(([a, b], i) => {
          const p1 = pat.points[a];
          const p2 = pat.points[b];
          return (
            <line
              key={`e${i}`}
              x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]}
              stroke={accent}
              strokeWidth={0.5}
              strokeLinecap="round"
              pathLength={100}
              style={{
                strokeDasharray: 100,
                opacity: 0.55,
                animation: `constellation-draw 1.1s ease-out ${0.15 * i + 0.2}s both`,
              }}
            />
          );
        })}

        {/* Constellation stars (glowing nodes) */}
        {pat.points.map((p, i) => (
          <g key={`n${i}`}>
            <circle cx={p[0]} cy={p[1]} r={2.6} fill={accent} opacity={0.18} />
            <circle
              cx={p[0]} cy={p[1]} r={1.3}
              fill={accent}
              style={{
                '--tw-min': 0.55,
                '--tw-max': 1,
                filter: `drop-shadow(0 0 3px ${accent})`,
                animation: `star-twinkle ${2.4 + (i % 4) * 0.5}s ease-in-out ${i * 0.3}s infinite`,
              } as CSSProperties}
            />
          </g>
        ))}
      </svg>

      {/* Glyph + halo */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div
          className="absolute rounded-full"
          style={{
            width: 110,
            height: 110,
            background: `radial-gradient(circle, ${accent}33 0%, transparent 68%)`,
            animation: 'glyph-halo 5s ease-in-out infinite',
          }}
        />
        <ZodiacImage sign={sign} symbol={symbol} size={80} accent={accent} glow />
      </div>
    </div>
  );
}
