'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import AmbientPlayer from '@/components/audio/AmbientPlayer';
import { useRitualContext } from '@/lib/ritual-context';
import type { Locale } from '@/lib/i18n-config';
import MoreMenu from './MoreMenu';
import { navLabels } from './nav-labels';

interface NavbarProps {
  locale: Locale;
}

/**
 * Obsidian header: wordmark, streak pill, ⋯ menu. On desktop the four main
 * sections sit in the middle; on phones they live in the tab bar instead.
 * The ambient player stays mounted here so music survives page changes.
 */
export default function Navbar({ locale }: NavbarProps) {
  const pathname = usePathname();
  const t = navLabels(locale);
  const { ritual } = useRitualContext();
  const [menuOpen, setMenuOpen] = useState(false);

  const active = (href: string) =>
    href === '/' ? pathname === '/' : !!pathname?.startsWith(href);

  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-[18px] md:px-8"
        style={{
          height: 56,
          background: 'rgba(11,10,15,.78)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderBottom: '1px solid rgba(255,255,255,.07)',
        }}
      >
        <Link href="/" className="font-serif flex items-center" style={{ gap: 8, fontSize: 16, letterSpacing: '.22em' }}>
          <span aria-hidden style={{ color: 'var(--accent)', fontSize: 13 }}>✦</span>
          TAROT
        </Link>

        <nav className="hidden md:flex items-center absolute left-1/2 -translate-x-1/2" style={{ gap: 28 }}>
          {([
            ['/', t.tarot],
            ['/daily', t.daily],
            ['/horoscope', t.horoscope],
            ['/history', t.journal],
          ] as const).map(([href, label]) => (
            <Link
              key={href}
              href={href}
              className="transition-colors hover:text-[var(--ink)]"
              style={{ fontSize: 14, color: active(href) ? 'var(--accent)' : '#8E879B' }}
            >
              {label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center" style={{ gap: 10 }}>
          <AmbientPlayer />
          {ritual.streak > 0 && (
            <span
              className="flex items-center"
              title={t.streak(ritual.streak)}
              style={{
                gap: 7,
                height: 28,
                padding: '0 11px',
                borderRadius: 999,
                border: '1px solid rgba(143,211,196,.28)',
                background: 'rgba(143,211,196,.07)',
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                color: 'var(--streak)',
                whiteSpace: 'nowrap',
              }}
            >
              <span
                aria-hidden
                style={{
                  width: 6, height: 6, borderRadius: '50%', background: 'var(--streak)',
                  animation: 'breathe 3.2s ease-in-out infinite',
                }}
              />
              {t.streak(ritual.streak)}
            </span>
          )}
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            aria-label={t.more}
            aria-expanded={menuOpen}
            className="flex items-center justify-center transition-colors hover:border-[var(--accent)] hover:text-[var(--accent)]"
            style={{
              width: 32, height: 32, borderRadius: '50%',
              border: '1px solid rgba(255,255,255,.12)', color: '#A49DAF', fontSize: 16, lineHeight: 1,
            }}
          >
            ⋯
          </button>
        </div>
      </header>
      <MoreMenu open={menuOpen} onClose={() => setMenuOpen(false)} labels={t} />
    </>
  );
}
