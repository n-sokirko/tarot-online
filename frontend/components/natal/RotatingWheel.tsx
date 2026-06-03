'use client';

import { useState } from 'react';

/**
 * A faint, very slowly rotating zodiac wheel used as a decorative background.
 * Reads /public/zodiac-wheel.png; renders nothing if the image is missing.
 */
export default function RotatingWheel({ opacity = 0.14 }: { opacity?: number }) {
  const [failed, setFailed] = useState(false);
  if (failed) return null;

  return (
    <div
      className="absolute inset-0 flex items-center justify-center overflow-hidden pointer-events-none"
      style={{ zIndex: 0 }}
      aria-hidden
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/zodiac-wheel.png"
        alt=""
        onError={() => setFailed(true)}
        style={{
          width: 'min(130vw, 920px)',
          maxWidth: 'none',
          opacity,
          animation: 'slow-spin 160s linear infinite',
          maskImage: 'radial-gradient(circle, #000 55%, transparent 78%)',
          WebkitMaskImage: 'radial-gradient(circle, #000 55%, transparent 78%)',
        }}
      />
    </div>
  );
}
