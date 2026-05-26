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

const HistoryIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
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
  const disabledColor = 'rgba(201,194,224,0.18)';

  const isHome = pathname === '/';
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
          Расклад
        </span>
      </Link>

      {/* History — disabled for now */}
      <div
        className="flex flex-col items-center gap-1 cursor-not-allowed"
        style={{ color: disabledColor }}
      >
        <HistoryIcon />
        <span style={{ fontSize: '0.55rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          История
        </span>
      </div>

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
