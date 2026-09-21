'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import {
  FreeSpreadIcon, NatalIcon, NumIcon, PersonIcon, PricingIcon, SettingsIcon, SparkleIcon,
} from './icons';
import type { NavLabels } from './nav-labels';

interface MoreMenuProps {
  open: boolean;
  onClose: () => void;
  labels: NavLabels;
}

/**
 * Everything that does not fit in the five tabs. A bottom sheet on phones
 * (opened from the "Ещё" tab or the ⋯ button), a panel under the header on
 * desktop.
 */
export default function MoreMenu({ open, onClose, labels: t }: MoreMenuProps) {
  const { user, logout } = useAuth();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = overflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  const items: [string, string, () => JSX.Element][] = [
    ['/table', t.freeSpread, FreeSpreadIcon],
    ['/natal', t.natal, NatalIcon],
    ['/numerology', t.numerology, NumIcon],
    ['/runes', t.runes, SparkleIcon],
    ['/pricing', t.premium, PricingIcon],
    ['/settings', t.settings, SettingsIcon],
  ];

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label={t.more}>
      <button
        type="button"
        aria-label="close"
        onClick={onClose}
        className="absolute inset-0 w-full h-full"
        style={{ background: 'rgba(5,4,8,.6)', backdropFilter: 'blur(4px)', cursor: 'default' }}
      />
      <div
        className="absolute left-0 right-0 bottom-0 md:bottom-auto md:left-auto md:right-6 md:top-[64px] md:w-[320px]"
        style={{
          borderRadius: '22px 22px 0 0',
          background: 'linear-gradient(180deg,#16131E,#0E0C14)',
          border: '1px solid rgba(255,255,255,.08)',
          boxShadow: '0 -20px 60px -20px #000',
          padding: '10px 14px calc(18px + env(safe-area-inset-bottom))',
          animation: 'sheetUp var(--dur) var(--ease)',
        }}
      >
        <div
          aria-hidden
          className="md:hidden mx-auto"
          style={{ width: 38, height: 4, borderRadius: 4, background: 'rgba(255,255,255,.16)', margin: '0 auto 12px' }}
        />
        <nav className="grid" style={{ gap: 2 }}>
          {items.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className="flex items-center transition-colors hover:bg-white/[.04]"
              style={{ gap: 14, minHeight: 48, padding: '0 12px', borderRadius: 12, fontSize: 15 }}
            >
              <span style={{ color: href === '/pricing' ? 'var(--accent)' : '#9A94A6' }}><Icon /></span>
              <span style={{ color: href === '/pricing' ? 'var(--accent)' : 'var(--ink)' }}>{label}</span>
            </Link>
          ))}
        </nav>

        <div style={{ height: 1, background: 'rgba(255,255,255,.07)', margin: '10px 4px' }} />

        {user ? (
          <div className="flex items-center" style={{ gap: 12, minHeight: 48, padding: '0 12px' }}>
            <span style={{ color: '#9A94A6' }}><PersonIcon /></span>
            <span className="flex-1 min-w-0 truncate" style={{ fontSize: 14, color: '#A49DAF' }}>
              {user.display_name || user.email.split('@')[0]}
            </span>
            <button
              type="button"
              onClick={() => { logout(); onClose(); }}
              style={{
                fontSize: 13, color: '#A49DAF', minHeight: 36, padding: '0 14px',
                borderRadius: 999, border: '1px solid rgba(255,255,255,.14)',
              }}
            >
              {t.logout}
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2" style={{ gap: 10, padding: '4px 4px 0' }}>
            <Link
              href="/login"
              onClick={onClose}
              className="flex items-center justify-center"
              style={{ minHeight: 44, borderRadius: 999, border: '1px solid rgba(255,255,255,.16)', fontSize: 14 }}
            >
              {t.login}
            </Link>
            <Link
              href="/register"
              onClick={onClose}
              className="flex items-center justify-center"
              style={{ minHeight: 44, borderRadius: 999, background: 'var(--accent)', color: '#0B0A0F', fontWeight: 700, fontSize: 14 }}
            >
              {t.register}
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
