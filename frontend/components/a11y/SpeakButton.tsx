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

// Voice name hints — prefer a deep male voice, avoid obviously female ones.
const MALE_HINTS = [
  'male', 'dmitr', 'yuri', 'pavel', 'maxim', 'artyom', 'aleksandr',
  'david', 'daniel', 'alex', 'george', 'arthur', 'fred', 'guy', 'aaron', 'mark', 'james',
];
const FEMALE_HINTS = [
  'female', 'milena', 'katya', 'irina', 'svetlana', 'tatyana', 'elena', 'alyona',
  'samantha', 'victoria', 'zira', 'aria', 'jenny', 'susan', 'hazel', 'karen',
];

export default function SpeakButton({
  text,
  lang,
  autoPlay = false,
}: {
  text: string;
  lang: 'ru' | 'en';
  /** Start narrating automatically once (e.g. right after AI generation). */
  autoPlay?: boolean;
}) {
  const [supported, setSupported] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const cancelledRef = useRef(false);
  const autoRan = useRef(false);
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
    const langVoices = voices.filter((v) => v.lang.toLowerCase().startsWith(prefix));
    if (langVoices.length === 0) return null;
    // Score voices: prefer high-quality network voices (Google/Neural/Online),
    // then male timbre, penalise obviously female ones. Highest score wins.
    const QUALITY = ['google', 'natural', 'neural', 'online', 'premium', 'enhanced'];
    const score = (raw: string) => {
      const n = raw.toLowerCase();
      let s = 0;
      if (QUALITY.some((h) => n.includes(h))) s += 3;
      if (MALE_HINTS.some((h) => n.includes(h))) s += 2;
      if (FEMALE_HINTS.some((h) => n.includes(h))) s -= 3;
      return s;
    };
    return [...langVoices].sort((a, b) => score(b.name) - score(a.name))[0];
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
      u.rate = 0.92;    // slightly slower = calmer
      u.pitch = 0.9;    // gently lowered — deep but natural (0.7 sounded robotic)
      if (idx === chunks.length - 1) {
        u.onend = () => { if (!cancelledRef.current) setSpeaking(false); };
        u.onerror = () => setSpeaking(false);
      }
      window.speechSynthesis.speak(u);
    });
  }, [supported, text, lang, pickVoice]);

  // Auto-narrate once when requested (e.g. right after AI generation).
  // A short delay lets the OS voice list finish loading so the bass voice is picked.
  useEffect(() => {
    if (!autoPlay || !supported || autoRan.current || !text.trim()) return;
    autoRan.current = true;
    const id = setTimeout(() => speak(), 400);
    return () => clearTimeout(id);
  }, [autoPlay, supported, text, speak]);

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
