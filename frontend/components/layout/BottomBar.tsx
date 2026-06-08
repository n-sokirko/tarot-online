'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale } from 'next-intl';
import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';

const LABELS = {
  ru: {
    tarot: 'Таро', runes: 'Руны', natal: 'Карта',
    daily: 'Карта дня', numerology: 'Числа', horoscope: 'Гороскоп',
    journal: 'Дневник',
    more: 'Ещё', premium: 'Premium', settings: 'Настройки',
    profile: 'Профиль', login: 'Войти',
  },
  en: {
    tarot: 'Tarot', runes: 'Runes', natal: 'Natal',
    daily: 'Card of the day', numerology: 'Numbers', horoscope: 'Horoscope',
    journal: 'Journal',
    more: 'More', premium: 'Premium', settings: 'Settings',
    profile: 'Profile', login: 'Log in',
  },
  de: {
    tarot: 'Tarot', runes: 'Runen', natal: 'Natal',
    daily: 'Tageskarte', numerology: 'Zahlen', horoscope: 'Horoskop',
    journal: 'Tagebuch',
    more: 'Mehr', premium: 'Premium', settings: 'Einstellungen',
    profile: 'Profil', login: 'Anmelden',
  },
  fr: {
    tarot: 'Tarot', runes: 'Runes', natal: 'Natal',
    daily: 'Carte du jour', numerology: 'Nombres', horoscope: 'Horoscope',
    journal: 'Journal',
    more: 'Plus', premium: 'Premium', settings: 'Réglages',
    profile: 'Profil', login: 'Connexion',
  },
  es: {
    tarot: 'Tarot', runes: 'Runas', natal: 'Natal',
    daily: 'Carta del día', numerology: 'Números', horoscope: 'Horóscopo',
    journal: 'Diario',
    more: 'Más', premium: 'Premium', settings: 'Ajustes',
    profile: 'Perfil', login: 'Entrar',
  },
  pt: {
    tarot: 'Tarô', runes: 'Runas', natal: 'Natal',
    daily: 'Carta do dia', numerology: 'Números', horoscope: 'Horóscopo',
    journal: 'Diário',
    more: 'Mais', premium: 'Premium', settings: 'Definições',
    profile: 'Perfil', login: 'Entrar',
  },
  uk: {
    tarot: 'Таро', runes: 'Руни', natal: 'Карта',
    daily: 'Карта дня', numerology: 'Числа', horoscope: 'Гороскоп',
    journal: 'Щоденник',
    more: 'Ще', premium: 'Premium', settings: 'Налаштування',
    profile: 'Профіль', login: 'Увійти',
  },
} as const;

const HomeIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
);
const NatalIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/>
    <line x1="12" y1="3" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="21"/>
    <line x1="3" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="21" y2="12"/>
  </svg>
);
const SparkleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3v18M3 12h18M5.5 5.5l13 13M18.5 5.5l-13 13"/>
  </svg>
);
const DailyIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="5" y="4" width="14" height="17" rx="2"/>
    <path d="M9 9h6M9 13h6M9 17h4"/>
  </svg>
);
const NumIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <text x="12" y="16" textAnchor="middle" fontSize="13" fontFamily="serif" fill="currentColor" stroke="none">7</text>
    <circle cx="12" cy="12" r="9"/>
  </svg>
);
const PricingIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
  </svg>
);
const ZodiacIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="9"/>
    <path d="M12 3a9 9 0 000 18M7 6l10 12M17 6L7 18"/>
  </svg>
);
const JournalIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 4a2 2 0 0 1 2-2h12a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6a2 2 0 0 1-2-2z"/>
    <path d="M8 2v20M12 7h4M12 11h4"/>
  </svg>
);
const SettingsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
  </svg>
);
const PersonIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
);

export default function BottomBar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const locale = useLocale();
  const l = LABELS[locale as keyof typeof LABELS] ?? LABELS.en;
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement | null>(null);

  // Close on outside tap.
  useEffect(() => {
    const onDown = (e: MouseEvent | TouchEvent) => {
      if (!moreRef.current) return;
      if (!moreRef.current.contains(e.target as Node)) setMoreOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('touchstart', onDown);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('touchstart', onDown);
    };
  }, []);

  // Close on route change.
  useEffect(() => { setMoreOpen(false); }, [pathname]);

  const activeColor = '#d4af37';
  const inactiveColor = 'rgba(201,194,224,0.35)';

  const isHome = pathname === '/';
  const isNatal = pathname?.startsWith('/natal') ?? false;
  const isDaily = pathname?.startsWith('/daily') ?? false;
  const isNumerology = pathname?.startsWith('/numerology') ?? false;
  const isHoroscope = pathname?.startsWith('/horoscope') ?? false;
  const isPricing = pathname === '/pricing';
  const isProfile = pathname === '/login' || pathname === '/register' || pathname === '/account';
  const isHistory = pathname?.startsWith('/history') ?? false;
  const isSettings = pathname === '/settings';
  const isMoreActive = isDaily || isNumerology || isHistory || isPricing || isSettings;

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 flex md:hidden items-center justify-around"
      style={{
        height: '60px',
        background: 'rgba(11,11,31,0.92)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderTop: '1px solid rgba(212,175,55,0.12)',
      }}
    >
      <Link href="/" className="flex flex-col items-center gap-1" style={{ color: isHome ? activeColor : inactiveColor }}>
        <HomeIcon />
        <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{l.tarot}</span>
      </Link>

      <Link href="/horoscope" className="flex flex-col items-center gap-1" style={{ color: isHoroscope ? activeColor : inactiveColor }}>
        <ZodiacIcon />
        <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{l.horoscope}</span>
      </Link>

      <Link href="/natal" className="flex flex-col items-center gap-1" style={{ color: isNatal ? activeColor : inactiveColor }}>
        <NatalIcon />
        <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{l.natal}</span>
      </Link>

      {/* More — popup menu */}
      <div ref={moreRef} className="relative flex flex-col items-center">
        <button
          type="button"
          onClick={() => setMoreOpen((v) => !v)}
          className="flex flex-col items-center gap-1"
          style={{ color: isMoreActive ? activeColor : inactiveColor }}
        >
          <SparkleIcon />
          <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{l.more}</span>
        </button>
        <AnimatePresence>
          {moreOpen && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.18 }}
              className="absolute bottom-[64px] right-1/2 translate-x-1/2 w-44 rounded-2xl py-2 flex flex-col"
              style={{
                background: 'rgba(11,11,31,0.97)',
                border: '1px solid rgba(212,175,55,0.25)',
                boxShadow: '0 6px 24px rgba(0,0,0,0.5)',
              }}
            >
              <Link
                href="/daily"
                className="flex items-center gap-3 px-4 py-2.5"
                style={{ color: isDaily ? activeColor : 'rgba(201,194,224,0.85)' }}
              >
                <DailyIcon />
                <span className="font-sans text-sm">{l.daily}</span>
              </Link>
              <Link
                href="/numerology"
                className="flex items-center gap-3 px-4 py-2.5"
                style={{ color: isNumerology ? activeColor : 'rgba(201,194,224,0.85)' }}
              >
                <NumIcon />
                <span className="font-sans text-sm">{l.numerology}</span>
              </Link>
              <Link
                href="/history"
                className="flex items-center gap-3 px-4 py-2.5"
                style={{ color: isHistory ? activeColor : 'rgba(201,194,224,0.85)' }}
              >
                <JournalIcon />
                <span className="font-sans text-sm">{l.journal}</span>
              </Link>
              <Link
                href="/settings"
                className="flex items-center gap-3 px-4 py-2.5"
                style={{ color: isSettings ? activeColor : 'rgba(201,194,224,0.85)' }}
              >
                <SettingsIcon />
                <span className="font-sans text-sm">{l.settings}</span>
              </Link>
              <div style={{ height: 1, background: 'rgba(212,175,55,0.12)', margin: '4px 12px' }} />
              <Link
                href="/pricing"
                className="flex items-center gap-3 px-4 py-2.5"
                style={{ color: isPricing ? activeColor : 'rgba(212,175,55,0.8)' }}
              >
                <PricingIcon />
                <span className="font-sans text-sm">{l.premium}</span>
              </Link>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <Link
        href={user ? '/account' : '/login'}
        className="flex flex-col items-center gap-1"
        style={{ color: isProfile ? activeColor : inactiveColor }}
      >
        <PersonIcon />
        <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          {user ? l.profile : l.login}
        </span>
      </Link>
    </nav>
  );
}
