'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { ApiError, getBillingMe } from '@/lib/api';
import { getAccessToken } from '@/lib/auth';
import type { BillingMe } from '@/lib/types';

interface PremiumGateProps {
  requires: string;
  locale?: 'ru' | 'en';
  fallback?: ReactNode;
  children: ReactNode;
}

const labels = {
  ru: {
    title: 'Premium-функция',
    body: 'Эта возможность доступна по подписке или с кредитами.',
    cta: 'Открыть тарифы',
    login: 'Войти, чтобы продолжить',
  },
  en: {
    title: 'Premium feature',
    body: 'This is available with a subscription or credits.',
    cta: 'Open pricing',
    login: 'Sign in to continue',
  },
} as const;

/**
 * Hides children behind a soft paywall. Resolves the user's entitlements
 * lazily on mount; anonymous users always see the locked state.
 */
export default function PremiumGate({ requires, locale = 'ru', fallback, children }: PremiumGateProps) {
  const t = labels[locale];
  const [me, setMe] = useState<BillingMe | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [needsLogin, setNeedsLogin] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) {
      setNeedsLogin(true);
      setLoaded(true);
      return;
    }
    getBillingMe()
      .then(setMe)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) setNeedsLogin(true);
      })
      .finally(() => setLoaded(true));
  }, []);

  if (!loaded) return null;

  const unlocked = !!me && me.entitlements.includes(requires);
  if (unlocked) return <>{children}</>;

  if (fallback) return <>{fallback}</>;

  return (
    <div
      className="rounded-2xl px-6 py-8 flex flex-col items-center text-center gap-3 max-w-md mx-auto"
      style={{
        background: 'linear-gradient(180deg, rgba(28,24,64,0.6), rgba(11,11,31,0.6))',
        border: '1px solid rgba(212,175,55,0.25)',
      }}
    >
      <span
        className="text-[10px] tracking-widest uppercase"
        style={{ color: '#d4af37', letterSpacing: '0.25em' }}
      >
        ✦ {t.title}
      </span>
      <p className="font-serif text-base" style={{ color: 'rgba(201,194,224,0.85)' }}>
        {t.body}
      </p>
      <a
        href={needsLogin ? '/login' : '/pricing'}
        className="mt-2 px-6 py-2.5 rounded-full text-xs tracking-widest uppercase"
        style={{
          background: 'linear-gradient(135deg, rgba(212,175,55,0.2), rgba(212,175,55,0.05))',
          border: '1px solid #d4af37',
          color: '#d4af37',
          letterSpacing: '0.18em',
        }}
      >
        {needsLogin ? t.login : t.cta}
      </a>
    </div>
  );
}
