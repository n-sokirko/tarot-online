'use client';

import { useState } from 'react';

/**
 * A faint, very slowly rotating zodiac wheel fixed to the centre of the viewport
 * (stays centred while scrolling) and sitting behind all page content (z-index
 * below the transparent page mains). Renders nothing if the image is missing.
 */
export default function RotatingWheel({ opacity = 0.16 }: { opacity?: number }) {
  const [failed, setFailed] = useState(false);
  if (failed) return null;

  return (
    <div
      className="fixed inset-0 flex items-center justify-center overflow-hidden pointer-events-none"
      style={{ zIndex: -1 }}
      aria-hidden
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/zodiac-wheel.png"
        alt=""
        onError={() => setFailed(true)}
        style={{
          width: 'min(140vmin, 1100px)',
          height: 'auto',
          maxWidth: 'none',
          opacity,
          animation: 'slow-spin 200s linear infinite',
          maskImage: 'radial-gradient(circle, #000 58%, transparent 80%)',
          WebkitMaskImage: 'radial-gradient(circle, #000 58%, transparent 80%)',
        }}
      />
    </div>
  );
}
