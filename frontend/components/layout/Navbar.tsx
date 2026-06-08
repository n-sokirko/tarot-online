'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import AmbientPlayer from '@/components/audio/AmbientPlayer';
import type { Locale } from '@/lib/i18n-config';

interface NavbarProps {
  locale: Locale;
}

const NAV = {
  ru: { tarot: 'Таро', daily: 'Карта дня', horoscope: 'Гороскоп', natal: 'Карта', numerology: 'Числа', history: 'Дневник', pricing: 'Premium', settings: 'Настройки', login: 'Войти', register: 'Регистрация', logout: 'Выйти' },
  en: { tarot: 'Tarot', daily: 'Daily', horoscope: 'Horoscope', natal: 'Natal', numerology: 'Numbers', history: 'Journal', pricing: 'Premium', settings: 'Settings', login: 'Log in', register: 'Register', logout: 'Log out' },
  de: { tarot: 'Tarot', daily: 'Tageskarte', horoscope: 'Horoskop', natal: 'Natal', numerology: 'Zahlen', history: 'Tagebuch', pricing: 'Premium', settings: 'Einstellungen', login: 'Anmelden', register: 'Registrieren', logout: 'Abmelden' },
  fr: { tarot: 'Tarot', daily: 'Carte du jour', horoscope: 'Horoscope', natal: 'Natal', numerology: 'Nombres', history: 'Journal', pricing: 'Premium', settings: 'Réglages', login: 'Connexion', register: 'Inscription', logout: 'Déconnexion' },
  es: { tarot: 'Tarot', daily: 'Carta del día', horoscope: 'Horóscopo', natal: 'Natal', numerology: 'Números', history: 'Diario', pricing: 'Premium', settings: 'Ajustes', login: 'Entrar', register: 'Registrarse', logout: 'Salir' },
  pt: { tarot: 'Tarô', daily: 'Carta do dia', horoscope: 'Horóscopo', natal: 'Natal', numerology: 'Números', history: 'Diário', pricing: 'Premium', settings: 'Definições', login: 'Entrar', register: 'Registar', logout: 'Sair' },
  uk: { tarot: 'Таро', daily: 'Карта дня', horoscope: 'Гороскоп', natal: 'Карта', numerology: 'Числа', history: 'Щоденник', pricing: 'Premium', settings: 'Налаштування', login: 'Увійти', register: 'Реєстрація', logout: 'Вийти' },
} as const;

function GearIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
    </svg>
  );
}

export default function Navbar({ locale }: NavbarProps) {
  const { user, isLoading, logout } = useAuth();
  const pathname = usePathname();
  const t = (NAV as unknown as Record<string, typeof NAV.en>)[locale] ?? NAV.en;

  const linkColor = (href: string) =>
    pathname === href || (href !== '/' && pathname?.startsWith(href))
      ? '#d4af37'
      : 'rgba(201,194,224,0.6)';

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

      {/* Center nav — desktop only */}
      <nav className="hidden md:flex items-center gap-5 absolute left-1/2 -translate-x-1/2">
        {([
          ['/', t.tarot],
          ['/daily', t.daily],
          ['/horoscope', t.horoscope],
          ['/natal', t.natal],
          ['/numerology', t.numerology],
          ['/history', t.history],
        ] as const).map(([href, label]) => (
          <Link
            key={href}
            href={href}
            className="text-xs font-sans tracking-widest uppercase transition-colors"
            style={{ color: linkColor(href), letterSpacing: '0.18em' }}
          >
            {label}
          </Link>
        ))}
        <Link
          href="/pricing"
          className="text-xs font-sans tracking-widest uppercase transition-colors"
          style={{ color: linkColor('/pricing') === 'rgba(201,194,224,0.6)' ? '#d4af37' : '#d4af37', letterSpacing: '0.18em' }}
        >
          {t.pricing}
        </Link>
      </nav>

      {/* Right side */}
      <div className="flex items-center gap-3 md:gap-4">
        <AmbientPlayer />

        {/* Settings — desktop */}
        <Link
          href="/settings"
          className="hidden md:flex items-center gap-1.5 text-xs font-sans tracking-widest uppercase transition-colors"
          style={{
            color: pathname === '/settings' ? '#d4af37' : 'rgba(201,194,224,0.45)',
            letterSpacing: '0.12em',
          }}
          title={t.settings}
        >
          <GearIcon />
          <span>{t.settings}</span>
        </Link>

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
                  className="text-xs font-sans tracking-widest uppercase px-3 py-1.5 rounded-full"
                  style={{
                    color: 'rgba(201,194,224,0.5)',
                    border: '1px solid rgba(212,175,55,0.2)',
                    letterSpacing: '0.1em',
                  }}
                >
                  {t.logout}
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="text-xs font-sans tracking-widest uppercase px-3 py-1.5 rounded-full"
                  style={{ color: 'rgba(201,194,224,0.6)', border: '1px solid rgba(212,175,55,0.25)', letterSpacing: '0.1em' }}
                >
                  {t.login}
                </Link>
                <Link
                  href="/register"
                  className="hidden md:block text-xs font-sans tracking-widest uppercase px-3 py-1.5 rounded-full"
                  style={{ background: 'rgba(212,175,55,0.1)', border: '1px solid #d4af37', color: '#d4af37', letterSpacing: '0.1em' }}
                >
                  {t.register}
                </Link>
              </div>
            )}
          </>
        )}
      </div>
    </header>
  );
}
