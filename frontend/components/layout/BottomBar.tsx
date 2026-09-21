'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale } from 'next-intl';
import { useEffect, useState } from 'react';
import { DailyIcon, HomeIcon, JournalIcon, SparkleIcon, ZodiacIcon } from './icons';
import MoreMenu from './MoreMenu';
import { navLabels } from './nav-labels';

/** Phone tab bar: four sections and "Ещё" for the rest. Hidden on desktop. */
export default function BottomBar() {
  const pathname = usePathname();
  const t = navLabels(useLocale());
  const [moreOpen, setMoreOpen] = useState(false);

  useEffect(() => setMoreOpen(false), [pathname]);

  const tabs: [string, string, () => JSX.Element][] = [
    ['/', t.tarot, HomeIcon],
    ['/daily', t.daily, DailyIcon],
    ['/horoscope', t.horoscope, ZodiacIcon],
    ['/history', t.journal, JournalIcon],
  ];
  const isActive = (href: string) => (href === '/' ? pathname === '/' : !!pathname?.startsWith(href));
  const moreActive = !tabs.some(([href]) => isActive(href));

  const tabStyle = (on: boolean): React.CSSProperties => ({
    color: on ? 'var(--accent)' : '#7E7890',
    minHeight: 48,
    gap: 4,
  });
  const labelStyle: React.CSSProperties = { fontSize: 10.5, fontWeight: 600, letterSpacing: '.02em' };

  return (
    <>
      <nav
        className="fixed bottom-0 left-0 right-0 z-40 grid grid-cols-5 md:hidden"
        style={{
          padding: '6px 6px calc(6px + env(safe-area-inset-bottom))',
          background: 'rgba(11,10,15,.86)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderTop: '1px solid rgba(255,255,255,.07)',
        }}
      >
        {tabs.map(([href, label, Icon]) => (
          <Link
            key={href}
            href={href}
            aria-current={isActive(href) ? 'page' : undefined}
            className="flex flex-col items-center justify-center min-w-0"
            style={tabStyle(isActive(href))}
          >
            <Icon />
            <span className="truncate max-w-full" style={labelStyle}>{label}</span>
          </Link>
        ))}
        <button
          type="button"
          onClick={() => setMoreOpen(true)}
          aria-expanded={moreOpen}
          className="flex flex-col items-center justify-center min-w-0"
          style={tabStyle(moreActive || moreOpen)}
        >
          <SparkleIcon />
          <span style={labelStyle}>{t.more}</span>
        </button>
      </nav>
      <MoreMenu open={moreOpen} onClose={() => setMoreOpen(false)} labels={t} />
    </>
  );
}
