'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

const HomeIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
);

const RunesIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 3v18"/>
    <path d="M18 3v18"/>
    <path d="M6 8l12 8"/>
  </svg>
);

const PricingIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
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

  const activeColor = '#d4af37';
  const inactiveColor = 'rgba(201,194,224,0.35)';

  const isHome = pathname === '/';
  const isRunes = pathname?.startsWith('/runes') ?? false;
  const isPricing = pathname === '/pricing';
  const isProfile = pathname === '/login' || pathname === '/register' || pathname === '/account';

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
      <Link
        href="/"
        className="flex flex-col items-center gap-1"
        style={{ color: isHome ? activeColor : inactiveColor }}
      >
        <HomeIcon />
        <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Таро
        </span>
      </Link>

      <Link
        href="/runes"
        className="flex flex-col items-center gap-1"
        style={{ color: isRunes ? activeColor : inactiveColor }}
      >
        <RunesIcon />
        <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Руны
        </span>
      </Link>

      <Link
        href="/pricing"
        className="flex flex-col items-center gap-1"
        style={{ color: isPricing ? activeColor : inactiveColor }}
      >
        <PricingIcon />
        <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Premium
        </span>
      </Link>

      <Link
        href={user ? '/account' : '/login'}
        className="flex flex-col items-center gap-1"
        style={{ color: isProfile ? activeColor : inactiveColor }}
      >
        <PersonIcon />
        <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          {user ? 'Профиль' : 'Войти'}
        </span>
      </Link>
    </nav>
  );
}
