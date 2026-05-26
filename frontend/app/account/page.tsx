'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';
import { getBillingMe } from '@/lib/api';
import { getAccessToken } from '@/lib/auth';
import type { BillingMe } from '@/lib/types';

const LOCALE = 'ru' as const;

const t = {
  ru: {
    title: 'Профиль',
    plan: 'Тариф',
    credits: 'Кредиты',
    entitlements: 'Доступные функции',
    next_charge: 'Следующее списание',
    no_subscription: 'Нет активной подписки',
    upgrade: 'Перейти к тарифам',
    logout: 'Выйти',
    loading: 'Загрузка...',
    none: 'нет',
    upgrade_success: 'Спасибо! Подписка активируется в течение минуты.',
    tier_free: 'Бесплатный',
    tier_premium: 'Premium',
  },
  en: {
    title: 'Profile',
    plan: 'Plan',
    credits: 'Credits',
    entitlements: 'Available features',
    next_charge: 'Next charge',
    no_subscription: 'No active subscription',
    upgrade: 'Open pricing',
    logout: 'Log out',
    loading: 'Loading...',
    none: 'none',
    upgrade_success: 'Thank you! Subscription activates within a minute.',
    tier_free: 'Free',
    tier_premium: 'Premium',
  },
}[LOCALE];

export default function AccountPage() {
  const router = useRouter();
  const params = useSearchParams();
  const { user, isLoading, logout } = useAuth();
  const [me, setMe] = useState<BillingMe | null>(null);
  const upgradeJustHappened = params.get('upgrade') === 'success';

  useEffect(() => {
    if (isLoading) return;
    if (!user || !getAccessToken()) {
      router.replace('/login?next=/account');
      return;
    }
    getBillingMe().then(setMe).catch(() => undefined);
  }, [user, isLoading, router]);

  return (
    <main
      className="min-h-screen px-4 py-12 md:py-20"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}
    >
      <div className="max-w-xl mx-auto">
        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="font-serif text-2xl md:text-3xl mb-8 text-center"
          style={{ color: '#d4af37', letterSpacing: '0.05em' }}
        >
          ✦ {t.title}
        </motion.h1>

        {upgradeJustHappened && (
          <p
            className="mb-6 text-center font-serif text-sm rounded-full px-4 py-2"
            style={{
              background: 'rgba(212,175,55,0.1)',
              border: '1px solid rgba(212,175,55,0.3)',
              color: '#d4af37',
            }}
          >
            {t.upgrade_success}
          </p>
        )}

        <div
          className="rounded-2xl p-6 space-y-5"
          style={{
            background: 'linear-gradient(180deg, rgba(28,24,64,0.7), rgba(11,11,31,0.6))',
            border: '1px solid rgba(212,175,55,0.18)',
          }}
        >
          <Row label={user?.email ?? ''} value="" muted />
          {!me ? (
            <p className="font-serif text-sm" style={{ color: 'rgba(201,194,224,0.5)' }}>
              {t.loading}
            </p>
          ) : (
            <>
              <Row
                label={t.plan}
                value={me.tier === 'premium' ? t.tier_premium : t.tier_free}
              />
              <Row label={t.credits} value={String(me.credits)} />
              <Row
                label={t.entitlements}
                value={me.entitlements.length ? me.entitlements.join(', ') : t.none}
              />
              {me.subscription ? (
                <Row
                  label={t.next_charge}
                  value={
                    me.subscription.current_period_end
                      ? new Date(me.subscription.current_period_end).toLocaleDateString(LOCALE)
                      : '—'
                  }
                />
              ) : (
                <p
                  className="font-serif text-sm italic"
                  style={{ color: 'rgba(201,194,224,0.5)' }}
                >
                  {t.no_subscription}
                </p>
              )}
            </>
          )}
        </div>

        <div className="flex flex-col items-center gap-3 mt-8">
          <a
            href="/pricing"
            className="px-6 py-2.5 rounded-full text-xs tracking-widest uppercase"
            style={{
              background: 'linear-gradient(135deg, rgba(212,175,55,0.2), rgba(212,175,55,0.05))',
              border: '1px solid #d4af37',
              color: '#d4af37',
              letterSpacing: '0.18em',
            }}
          >
            {t.upgrade}
          </a>
          <button
            onClick={() => { logout(); router.push('/'); }}
            className="text-xs tracking-widest uppercase opacity-70"
            style={{ color: 'rgba(201,194,224,0.6)', letterSpacing: '0.18em' }}
          >
            {t.logout}
          </button>
        </div>
      </div>
    </main>
  );
}

function Row({ label, value, muted }: { label: string; value: string; muted?: boolean }) {
  return (
    <div className="flex justify-between items-baseline gap-4">
      <span
        className="font-serif text-sm tracking-wide"
        style={{ color: muted ? 'rgba(201,194,224,0.45)' : 'rgba(201,194,224,0.65)' }}
      >
        {label}
      </span>
      <span
        className="font-serif text-sm text-right"
        style={{ color: 'rgba(201,194,224,0.9)' }}
      >
        {value}
      </span>
    </div>
  );
}
