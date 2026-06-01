'use client';

/**
 * SpeakButton — reads a block of text aloud for low-vision / hands-free users.
 *
 * Uses the browser's built-in Web Speech API (window.speechSynthesis): free,
 * offline, no backend, with native RU/EN voices. The text is stripped of
 * markdown and split into sentence-sized chunks before speaking — this avoids
 * the well-known Chrome bug where a single long utterance cuts off after ~15s.
 *
 * Renders nothing if the browser has no speech synthesis support.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

function stripMarkdown(md: string): string {
  return md
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/^[#>\s]*/gm, '')
    .replace(/[*_~#✦✧★☆]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function chunkText(text: string): string[] {
  const parts = text.match(/[^.!?…\n]+[.!?…]*\s*/g) ?? [text];
  const chunks: string[] = [];
  let buf = '';
  for (const p of parts) {
    if ((buf + p).length > 220) {
      if (buf.trim()) chunks.push(buf.trim());
      buf = p;
    } else {
      buf += p;
    }
  }
  if (buf.trim()) chunks.push(buf.trim());
  return chunks;
}

const COPY = {
  ru: { listen: 'Озвучить', stop: 'Стоп' },
  en: { listen: 'Listen', stop: 'Stop' },
} as const;

export default function SpeakButton({
  text,
  lang,
}: {
  text: string;
  lang: 'ru' | 'en';
}) {
  const [supported, setSupported] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const cancelledRef = useRef(false);
  const t = COPY[lang];

  useEffect(() => {
    const ok = typeof window !== 'undefined' && 'speechSynthesis' in window;
    setSupported(ok);
    if (ok) {
      // Warm the voice list (some browsers populate it lazily).
      window.speechSynthesis.getVoices();
      const noop = () => {};
      window.speechSynthesis.onvoiceschanged = noop;
    }
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const pickVoice = useCallback((code: 'ru' | 'en') => {
    const voices = window.speechSynthesis.getVoices();
    const prefix = code === 'ru' ? 'ru' : 'en';
    return voices.find((v) => v.lang.toLowerCase().startsWith(prefix)) ?? null;
  }, []);

  const stop = useCallback(() => {
    cancelledRef.current = true;
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  const speak = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    cancelledRef.current = false;

    const chunks = chunkText(stripMarkdown(text));
    if (chunks.length === 0) return;

    const langCode = lang === 'ru' ? 'ru-RU' : 'en-US';
    const voice = pickVoice(lang);
    setSpeaking(true);

    chunks.forEach((chunk, idx) => {
      const u = new SpeechSynthesisUtterance(chunk);
      u.lang = langCode;
      if (voice) u.voice = voice;
      u.rate = 0.96;
      u.pitch = 1;
      if (idx === chunks.length - 1) {
        u.onend = () => { if (!cancelledRef.current) setSpeaking(false); };
        u.onerror = () => setSpeaking(false);
      }
      window.speechSynthesis.speak(u);
    });
  }, [supported, text, lang, pickVoice]);

  if (!supported) return null;

  return (
    <button
      type="button"
      onClick={speaking ? stop : speak}
      aria-label={speaking ? t.stop : t.listen}
      aria-pressed={speaking}
      className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full font-sans text-xs uppercase tracking-widest transition-colors"
      style={{
        border: '1px solid rgba(212,175,55,0.4)',
        background: speaking ? 'rgba(212,175,55,0.16)' : 'rgba(212,175,55,0.05)',
        color: '#d4af37',
        letterSpacing: '0.12em',
      }}
    >
      {speaking ? (
        // Animated equalizer bars
        <span className="inline-flex items-end gap-[2px]" style={{ height: 12 }} aria-hidden>
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              style={{
                width: 2,
                height: 12,
                background: '#d4af37',
                transformOrigin: 'bottom',
                animation: `speak-bar ${0.6 + i * 0.18}s ease-in-out ${i * 0.12}s infinite`,
              }}
            />
          ))}
        </span>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
          <path d="M15.5 8.5a5 5 0 010 7" />
          <path d="M18.5 5.5a9 9 0 010 13" />
        </svg>
      )}
      {speaking ? t.stop : t.listen}
    </button>
  );
}
