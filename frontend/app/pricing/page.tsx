'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ApiError, listPlans, startCheckout } from '@/lib/api';
import { getAccessToken } from '@/lib/auth';
import { useAuth } from '@/lib/auth-context';
import { openCheckout } from '@/lib/paddle';
import type { Plan, PlansResponse } from '@/lib/types';

const LOCALE = 'ru' as const;

type PricingCopy = {
  title: string; subtitle: string;
  free_features: string[]; premium_features: string[]; credits_features: string[];
  cta_free: string; cta_premium: string; cta_credits: string; cta_login: string;
  monthly: string; one_time: string; badge_recommended: string;
  footnote: string; not_configured: string; error: string;
};

const t: PricingCopy = ({
  ru: {
    title: 'Тарифы',
    subtitle: 'Выбери, что подходит. Платежи через Paddle — любая карта, любая валюта.',
    free_features: ['3 расклада Таро в день', 'Базовые описания карт', 'Без AI-интерпретации'],
    premium_features: [
      '50 AI-интерпретаций в месяц',
      'Расклад Кельтского креста',
      'Расклады на рунах',
      'Безлимитная история',
    ],
    credits_features: ['Не сгорают', 'Подходят для глубинных раскладов', 'Натальная карта (скоро)'],
    cta_free: 'Текущий тариф',
    cta_premium: 'Оформить Premium',
    cta_credits: 'Купить кредиты',
    cta_login: 'Войти и оформить',
    monthly: '/мес',
    one_time: 'разово',
    badge_recommended: 'Рекомендуем',
    footnote: 'Платежи обрабатывает Paddle (merchant of record). Налоги и комиссии включены.',
    not_configured: 'Этот тариф ещё не настроен в Paddle. Свяжись с автором.',
    error: 'Не удалось открыть оплату. Попробуй ещё раз.',
  },
  en: {
    title: 'Pricing',
    subtitle: 'Choose what fits. Payments via Paddle — any card, any currency.',
    free_features: ['3 tarot readings per day', 'Base card descriptions', 'No AI interpretation'],
    premium_features: [
      '50 AI interpretations / month',
      'Celtic Cross spread',
      'Rune casts',
      'Unlimited history',
    ],
    credits_features: ['Never expire', 'Good for deep readings', 'Natal chart (soon)'],
    cta_free: 'Current plan',
    cta_premium: 'Subscribe to Premium',
    cta_credits: 'Buy credits',
    cta_login: 'Sign in to checkout',
    monthly: '/mo',
    one_time: 'one-time',
    badge_recommended: 'Recommended',
    footnote: 'Payments handled by Paddle (merchant of record). Taxes & fees included.',
    not_configured: 'This plan is not yet configured in Paddle. Contact the maintainer.',
    error: 'Failed to open checkout. Try again.',
  },
})[LOCALE];

function formatPrice(cents: number, locale: 'ru' | 'en') {
  const dollars = cents / 100;
  if (locale === 'ru') {
    return `$${dollars.toFixed(dollars % 1 === 0 ? 0 : 2)}`;
  }
  return `$${dollars.toFixed(dollars % 1 === 0 ? 0 : 2)}`;
}

export default function PricingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [data, setData] = useState<PlansResponse | null>(null);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    listPlans().then(setData).catch(() => setErrorMsg(t.error));
  }, []);

  const handlePurchase = async (plan: Plan) => {
    setErrorMsg(null);
    if (!getAccessToken()) {
      router.push('/login?next=/pricing');
      return;
    }
    setPurchasing(plan.slug);
    try {
      const payload = await startCheckout(plan.slug);
      await openCheckout({
        env: payload.paddle_env,
        token: payload.paddle_client_token,
        priceId: payload.price_id,
        email: payload.customer_email,
        customData: payload.custom_data,
        locale: LOCALE,
      });
    } catch (e) {
      if (e instanceof ApiError && e.status === 503) {
        setErrorMsg(t.not_configured);
      } else {
        setErrorMsg(t.error);
      }
    } finally {
      setPurchasing(null);
    }
  };

  return (
    <main
      className="min-h-screen px-4 py-12 md:py-20"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}
    >
      <div className="max-w-5xl mx-auto">
        <motion.header
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1
            className="font-serif text-3xl md:text-4xl mb-3"
            style={{ color: '#d4af37', letterSpacing: '0.05em' }}
          >
            ✦ {t.title}
          </h1>
          <p className="font-serif text-sm md:text-base max-w-xl mx-auto" style={{ color: 'rgba(201,194,224,0.7)' }}>
            {t.subtitle}
          </p>
        </motion.header>

        {errorMsg && (
          <p className="text-center text-sm mb-6" style={{ color: '#ff8888' }}>
            {errorMsg}
          </p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {data?.plans.map((plan, idx) => (
            <PlanCard
              key={plan.slug}
              plan={plan}
              recommended={plan.slug === 'premium-monthly'}
              loading={purchasing === plan.slug}
              onPurchase={() => handlePurchase(plan)}
              locale={LOCALE}
              t={t}
              user={!!user}
              index={idx}
            />
          ))}
        </div>

        <p
          className="mt-10 text-center text-[10px] tracking-widest uppercase"
          style={{ color: 'rgba(201,194,224,0.4)', letterSpacing: '0.18em' }}
        >
          {t.footnote}
        </p>
      </div>
    </main>
  );
}

function PlanCard({
  plan,
  recommended,
  loading,
  onPurchase,
  locale,
  t,
  user,
  index,
}: {
  plan: Plan;
  recommended: boolean;
  loading: boolean;
  onPurchase: () => void;
  locale: 'ru' | 'en';
  t: PricingCopy;
  user: boolean;
  index: number;
}) {
  const name = locale === 'ru' ? plan.name_ru : plan.name_en;
  const description = locale === 'ru' ? plan.description_ru : plan.description_en;

  let features: string[] = [];
  let cta = t.cta_premium;
  let priceLabel = '';

  if (plan.kind === 'free') {
    features = t.free_features;
    cta = t.cta_free;
    priceLabel = locale === 'ru' ? 'бесплатно' : 'free';
  } else if (plan.kind === 'subscription') {
    features = t.premium_features;
    cta = user ? t.cta_premium : t.cta_login;
    priceLabel = `${formatPrice(plan.price_usd_cents, locale)} ${t.monthly}`;
  } else {
    features = t.credits_features;
    cta = user ? t.cta_credits : t.cta_login;
    priceLabel = `${formatPrice(plan.price_usd_cents, locale)} · ${t.one_time}`;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.5 }}
      className="rounded-2xl p-6 flex flex-col relative overflow-hidden"
      style={{
        background: recommended
          ? 'linear-gradient(180deg, rgba(212,175,55,0.12), rgba(28,24,64,0.4))'
          : 'linear-gradient(180deg, rgba(28,24,64,0.6), rgba(11,11,31,0.6))',
        border: `1px solid ${recommended ? '#d4af37' : 'rgba(212,175,55,0.18)'}`,
        boxShadow: recommended ? '0 0 32px rgba(212,175,55,0.18)' : 'none',
      }}
    >
      {recommended && (
        <span
          className="absolute top-4 right-4 text-[9px] tracking-widest uppercase px-2 py-1 rounded-full"
          style={{
            background: 'rgba(212,175,55,0.2)',
            color: '#d4af37',
            letterSpacing: '0.18em',
            border: '1px solid rgba(212,175,55,0.4)',
          }}
        >
          {t.badge_recommended}
        </span>
      )}

      <h2 className="font-serif text-xl mb-2" style={{ color: '#d4af37' }}>
        {name}
      </h2>
      <div className="font-serif text-2xl mb-4" style={{ color: 'rgba(201,194,224,0.95)' }}>
        {priceLabel}
      </div>
      <p className="font-serif text-sm mb-5" style={{ color: 'rgba(201,194,224,0.65)' }}>
        {description}
      </p>

      <ul className="flex-1 space-y-2 mb-6">
        {features.map((f) => (
          <li key={f} className="font-serif text-sm flex items-start gap-2" style={{ color: 'rgba(201,194,224,0.85)' }}>
            <span style={{ color: '#d4af37', marginTop: '0.15em' }}>✦</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <button
        disabled={plan.kind === 'free' || loading}
        onClick={onPurchase}
        className="w-full px-4 py-2.5 rounded-full text-xs tracking-widest uppercase transition-all"
        style={{
          background: plan.kind === 'free'
            ? 'rgba(201,194,224,0.05)'
            : 'linear-gradient(135deg, rgba(212,175,55,0.2), rgba(212,175,55,0.05))',
          border: plan.kind === 'free'
            ? '1px solid rgba(201,194,224,0.15)'
            : '1px solid #d4af37',
          color: plan.kind === 'free' ? 'rgba(201,194,224,0.45)' : '#d4af37',
          letterSpacing: '0.18em',
          opacity: loading ? 0.5 : 1,
          cursor: plan.kind === 'free' || loading ? 'default' : 'pointer',
        }}
      >
        {loading ? '...' : cta}
      </button>
    </motion.div>
  );
}
