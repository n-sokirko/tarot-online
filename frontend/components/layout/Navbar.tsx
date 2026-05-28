'use client';

import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import LocaleSwitcher from './LocaleSwitcher';
import type { Locale } from '@/i18n';

interface NavbarProps {
  locale: Locale;
}

export default function Navbar({ locale }: NavbarProps) {
  const { user, isLoading, logout } = useAuth();

  return (
    <header
      className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 md:px-8"
      style={{
        height: '56px',
        background: 'rgba(11,11,31,0.85)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(212,175,55,0.12)',
      }}
    >
      {/* Logo */}
      <Link
        href="/"
        className="font-serif text-base md:text-lg tracking-widest flex items-center gap-2"
        style={{ color: '#d4af37', letterSpacing: '0.2em' }}
      >
        <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>✦</span>
        TAROT
      </Link>

      {/* Center nav (desktop only) */}
      <nav className="hidden md:flex items-center gap-6 absolute left-1/2 -translate-x-1/2">
        <Link
          href="/"
          className="text-xs font-sans tracking-widest uppercase"
          style={{ color: 'rgba(201,194,224,0.6)', letterSpacing: '0.18em' }}
        >
          {locale === 'ru' ? 'Таро' : 'Tarot'}
        </Link>
        <Link
          href="/runes"
          className="text-xs font-sans tracking-widest uppercase"
          style={{ color: 'rgba(201,194,224,0.6)', letterSpacing: '0.18em' }}
        >
          {locale === 'ru' ? 'Руны' : 'Runes'}
        </Link>
        <Link
          href="/natal"
          className="text-xs font-sans tracking-widest uppercase"
          style={{ color: 'rgba(201,194,224,0.6)', letterSpacing: '0.18em' }}
        >
          {locale === 'ru' ? 'Карта' : 'Natal'}
        </Link>
        <Link
          href="/pricing"
          className="text-xs font-sans tracking-widest uppercase"
          style={{ color: '#d4af37', letterSpacing: '0.18em' }}
        >
          Premium
        </Link>
      </nav>

      {/* Right side */}
      <div className="flex items-center gap-4 md:gap-6">
        <LocaleSwitcher currentLocale={locale} />

        {!isLoading && (
          <>
            {user ? (
              <div className="flex items-center gap-3">
                <span
                  className="hidden md:block text-xs font-sans"
                  style={{ color: 'rgba(201,194,224,0.5)' }}
                >
                  {user.display_name || user.email.split('@')[0]}
                </span>
                <button
                  onClick={logout}
                  className="text-xs font-sans tracking-widest uppercase px-3 py-1.5 rounded-full transition-colors"
                  style={{
                    color: 'rgba(201,194,224,0.5)',
                    border: '1px solid rgba(212,175,55,0.2)',
                    letterSpacing: '0.1em',
                  }}
                >
                  {locale === 'ru' ? 'Выйти' : 'Log out'}
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="text-xs font-sans tracking-widest uppercase px-3 py-1.5 rounded-full transition-all"
                  style={{
                    color: 'rgba(201,194,224,0.6)',
                    border: '1px solid rgba(212,175,55,0.25)',
                    letterSpacing: '0.1em',
                  }}
                >
                  {locale === 'ru' ? 'Войти' : 'Log in'}
                </Link>
                <Link
                  href="/register"
                  className="text-xs font-sans tracking-widest uppercase px-3 py-1.5 rounded-full transition-all"
                  style={{
                    background: 'rgba(212,175,55,0.1)',
                    border: '1px solid #d4af37',
                    color: '#d4af37',
                    letterSpacing: '0.1em',
                  }}
                >
                  {locale === 'ru' ? 'Регистрация' : 'Register'}
                </Link>
              </div>
            )}
          </>
        )}
      </div>
    </header>
  );
}
