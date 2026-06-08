'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useSettings, ACCENT_PALETTES, FONT_SCALE } from '@/lib/settings-context';
import { locales, LOCALE_LABELS, LOCALE_FLAGS } from '@/lib/i18n-config';
import type { FontSize, AccentColor } from '@/lib/settings-context';

const FONT_OPTIONS: { value: FontSize; label: string; desc: string }[] = [
  { value: 'sm', label: 'Маленький',      desc: 'Compact' },
  { value: 'md', label: 'Обычный',        desc: 'Default' },
  { value: 'lg', label: 'Крупный',        desc: 'Easier to read' },
  { value: 'xl', label: 'Очень крупный',  desc: 'Maximum' },
];

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="font-sans text-xs uppercase tracking-widest" style={{ color: 'rgba(201,194,224,0.45)', letterSpacing: '0.22em' }}>
      {children}
    </h2>
  );
}

export default function SettingsPage() {
  const { settings, setFontSize, setAccentColor } = useSettings();
  const router = useRouter();
  const [currentLocale, setCurrentLocale] = useState<string>('ru');

  useEffect(() => {
    const m = document.cookie.match(/NEXT_LOCALE=([^;]+)/);
    setCurrentLocale(m?.[1] ?? 'ru');
  }, []);

  const switchLocale = (locale: string) => {
    document.cookie = `NEXT_LOCALE=${locale}; path=/; max-age=31536000; SameSite=Lax`;
    setCurrentLocale(locale);
    // Soft re-render instead of window.location.reload(): a hard reload inside the
    // Telegram Mini App WebView reloads the URL *without* the launch hash
    // (#tgWebAppData=…), which wipes window.Telegram.WebApp.initData and breaks
    // auto-login — the app then opens blank / with an error. router.refresh()
    // re-runs the server render (picking up the new NEXT_LOCALE cookie) while
    // keeping the Telegram SDK context alive.
    router.refresh();
  };

  return (
    <main className="min-h-screen flex flex-col items-center px-4 py-10">
      <motion.div
        className="w-full max-w-lg flex flex-col gap-8"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <header className="text-center flex flex-col gap-1">
          <p className="font-sans text-xs uppercase tracking-widest" style={{ color: 'var(--accent)', opacity: 0.6, letterSpacing: '0.25em' }}>
            ✦ Настройки · Settings ✦
          </p>
          <h1 className="font-serif text-3xl" style={{ color: 'var(--accent)' }}>
            Персонализация
          </h1>
        </header>

        {/* Language */}
        <section className="flex flex-col gap-3">
          <SectionTitle>Язык · Language</SectionTitle>
          <div className="grid grid-cols-2 gap-2">
            {(locales as readonly string[]).map((loc) => {
              const active = currentLocale === loc;
              const flag = LOCALE_FLAGS[loc as keyof typeof LOCALE_FLAGS] ?? '🌐';
              const label = LOCALE_LABELS[loc as keyof typeof LOCALE_LABELS] ?? loc;
              return (
                <motion.button
                  key={loc}
                  onClick={() => switchLocale(loc)}
                  className="flex items-center gap-3 p-3 rounded-2xl text-left"
                  style={{
                    background: active ? 'rgba(212,175,55,0.1)' : 'rgba(212,175,55,0.03)',
                    border: `1px solid ${active ? 'var(--accent)' : 'rgba(212,175,55,0.15)'}`,
                  }}
                  whileTap={{ scale: 0.97 }}
                >
                  <span className="text-lg">{flag}</span>
                  <div className="flex flex-col gap-0.5 min-w-0">
                    <span className="font-serif text-sm truncate" style={{ color: active ? 'var(--accent)' : 'rgba(201,194,224,0.85)' }}>
                      {label}
                    </span>
                    <span className="font-sans text-[10px] uppercase" style={{ color: 'rgba(201,194,224,0.35)', letterSpacing: '0.1em' }}>
                      {loc.toUpperCase()}
                    </span>
                  </div>
                  {active && <span className="ml-auto text-xs flex-shrink-0" style={{ color: 'var(--accent)' }}>✓</span>}
                </motion.button>
              );
            })}
          </div>
          <p className="font-sans text-xs" style={{ color: 'rgba(201,194,224,0.3)' }}>
            Язык определяется автоматически по настройкам браузера или Telegram при первом визите.
          </p>
        </section>

        {/* Font size */}
        <section className="flex flex-col gap-3">
          <SectionTitle>Размер текста · Text size</SectionTitle>
          <div className="grid grid-cols-2 gap-2">
            {FONT_OPTIONS.map((opt) => {
              const active = settings.fontSize === opt.value;
              return (
                <motion.button
                  key={opt.value}
                  onClick={() => setFontSize(opt.value)}
                  className="flex flex-col items-start gap-0.5 p-4 rounded-2xl text-left"
                  style={{
                    background: active ? 'rgba(212,175,55,0.1)' : 'rgba(212,175,55,0.03)',
                    border: `1px solid ${active ? 'var(--accent)' : 'rgba(212,175,55,0.15)'}`,
                  }}
                  whileTap={{ scale: 0.97 }}
                >
                  <span
                    className="font-serif"
                    style={{ fontSize: `${FONT_SCALE[opt.value] * 1.25}rem`, color: active ? 'var(--accent)' : 'rgba(201,194,224,0.8)' }}
                  >
                    Аа
                  </span>
                  <span className="font-sans text-sm font-medium" style={{ color: active ? 'var(--accent)' : 'rgba(201,194,224,0.85)' }}>
                    {opt.label}
                  </span>
                  <span className="font-sans text-xs" style={{ color: 'rgba(201,194,224,0.35)' }}>
                    {opt.desc}
                  </span>
                  {active && <span className="ml-auto text-xs" style={{ color: 'var(--accent)' }}>✓</span>}
                </motion.button>
              );
            })}
          </div>
        </section>

        {/* Accent color */}
        <section className="flex flex-col gap-3">
          <SectionTitle>Тема · Theme</SectionTitle>
          <div className="grid grid-cols-2 gap-2">
            {(Object.entries(ACCENT_PALETTES) as [AccentColor, typeof ACCENT_PALETTES[AccentColor]][]).map(([key, pal]) => {
              const active = settings.accentColor === key;
              return (
                <motion.button
                  key={key}
                  onClick={() => setAccentColor(key)}
                  className="flex items-center gap-3 p-4 rounded-2xl text-left"
                  style={{
                    background: active ? `${pal.primary}18` : 'rgba(212,175,55,0.03)',
                    border: `1px solid ${active ? pal.primary : 'rgba(212,175,55,0.15)'}`,
                  }}
                  whileTap={{ scale: 0.97 }}
                >
                  <div
                    className="rounded-full flex-shrink-0"
                    style={{
                      width: 30, height: 30,
                      background: `radial-gradient(circle at 35% 35%, ${pal.primary}, ${pal.primary}88)`,
                      boxShadow: active ? `0 0 12px ${pal.glow}` : 'none',
                    }}
                  />
                  <div className="flex flex-col gap-0.5">
                    <span className="font-serif text-sm" style={{ color: active ? pal.primary : 'rgba(201,194,224,0.85)' }}>
                      {pal.label}
                    </span>
                    <span className="font-sans text-xs" style={{ color: 'rgba(201,194,224,0.3)', fontVariantNumeric: 'tabular-nums' }}>
                      {pal.primary}
                    </span>
                  </div>
                  {active && <span className="ml-auto text-xs" style={{ color: pal.primary }}>✓</span>}
                </motion.button>
              );
            })}
          </div>
        </section>

        {/* Preview */}
        <section className="flex flex-col gap-3">
          <SectionTitle>Предпросмотр · Preview</SectionTitle>
          <div
            className="p-5 rounded-2xl flex flex-col gap-2"
            style={{ background: 'rgba(212,175,55,0.04)', border: '1px solid var(--accent-glow)' }}
          >
            <p className="font-sans text-xs uppercase tracking-widest" style={{ color: 'var(--accent)', letterSpacing: '0.2em' }}>
              ✦ Карта дня ✦
            </p>
            <p className="font-serif leading-relaxed" style={{ color: 'rgba(201,194,224,0.9)' }}>
              Звёзды складываются в узор, который говорит только с тобой.
            </p>
            <p className="font-sans text-xs" style={{ color: 'var(--accent)', opacity: 0.5 }}>
              The stars align in a pattern that speaks only to you.
            </p>
          </div>
        </section>
      </motion.div>
    </main>
  );
}
