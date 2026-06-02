'use client';

/**
 * AmbientPlayer — a procedural mystical drone generated live with the Web Audio
 * API (no audio file). A low detuned pad (C2 · G2 · C3) through a slowly sweeping
 * low-pass filter and a generated reverb tail → a calm, mysterious atmosphere.
 *
 * Off by default (browsers block autoplay and silence is the polite default).
 * A small floating toggle starts/stops it on a user gesture; the choice is
 * remembered in localStorage.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

const STORAGE_KEY = 'tarot_ambient';

export default function AmbientPlayer() {
  const [on, setOn] = useState(false);
  const ctxRef = useRef<AudioContext | null>(null);
  const masterRef = useRef<GainNode | null>(null);
  const oscRef = useRef<OscillatorNode[]>([]);

  const buildImpulse = (ctx: AudioContext) => {
    const len = Math.floor(ctx.sampleRate * 2.6);
    const buf = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const data = buf.getChannelData(ch);
      for (let i = 0; i < len; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2.5);
      }
    }
    return buf;
  };

  const start = useCallback(() => {
    if (ctxRef.current) return;
    const Ctor: typeof AudioContext | undefined =
      window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctor) return;
    const ctx = new Ctor();
    ctxRef.current = ctx;

    const master = ctx.createGain();
    master.gain.value = 0;
    master.connect(ctx.destination);
    masterRef.current = master;

    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 600;
    lp.Q.value = 0.7;
    lp.connect(master);

    const reverb = ctx.createConvolver();
    reverb.buffer = buildImpulse(ctx);
    const wet = ctx.createGain();
    wet.gain.value = 0.55;
    lp.connect(reverb);
    reverb.connect(wet);
    wet.connect(master);

    // Drone voices — a low fifth + octave for a mystical pad.
    [65.41, 98.0, 130.81].forEach((f, i) => {
      const o = ctx.createOscillator();
      o.type = i === 2 ? 'sine' : 'triangle';
      o.frequency.value = f;
      o.detune.value = (i - 1) * 6;
      const g = ctx.createGain();
      g.gain.value = i === 2 ? 0.16 : 0.45;
      o.connect(g);
      g.connect(lp);
      o.start();
      oscRef.current.push(o);
    });

    // Very slow LFO sweeps the filter cutoff → gentle living movement.
    const lfo = ctx.createOscillator();
    lfo.frequency.value = 0.05;
    const lfoGain = ctx.createGain();
    lfoGain.gain.value = 220;
    lfo.connect(lfoGain);
    lfoGain.connect(lp.frequency);
    lfo.start();
    oscRef.current.push(lfo);

    master.gain.linearRampToValueAtTime(0.06, ctx.currentTime + 3);
  }, []);

  const stop = useCallback(() => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    masterRef.current?.gain.linearRampToValueAtTime(0, ctx.currentTime + 1.2);
    const oscs = oscRef.current;
    oscRef.current = [];
    setTimeout(() => {
      oscs.forEach((o) => { try { o.stop(); } catch { /* already stopped */ } });
      ctx.close().catch(() => {});
      ctxRef.current = null;
      masterRef.current = null;
    }, 1300);
  }, []);

  const toggle = useCallback(() => {
    setOn((prev) => {
      const next = !prev;
      if (next) start(); else stop();
      try { localStorage.setItem(STORAGE_KEY, next ? 'on' : 'off'); } catch { /* ignore */ }
      return next;
    });
  }, [start, stop]);

  useEffect(() => () => { stop(); }, [stop]);

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={on ? 'Выключить фоновую музыку' : 'Включить фоновую музыку'}
      aria-pressed={on}
      className="fixed z-40 flex items-center justify-center rounded-full transition-colors"
      style={{
        left: 14,
        bottom: 74,
        width: 40,
        height: 40,
        background: on ? 'rgba(212,175,55,0.18)' : 'rgba(11,11,31,0.7)',
        border: `1px solid ${on ? '#d4af37' : 'rgba(212,175,55,0.3)'}`,
        backdropFilter: 'blur(8px)',
        color: on ? '#d4af37' : 'rgba(201,194,224,0.6)',
      }}
    >
      {on ? (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M11 5 6 9H2v6h4l5 4z" />
          <path d="M15.5 8.5a5 5 0 0 1 0 7" />
          <path d="M18.5 5.5a9 9 0 0 1 0 13" />
        </svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M11 5 6 9H2v6h4l5 4z" />
          <line x1="22" y1="9" x2="16" y2="15" />
          <line x1="16" y1="9" x2="22" y2="15" />
        </svg>
      )}
    </button>
  );
}
