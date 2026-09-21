'use client';

import Link from 'next/link';

export default function PremiumStrip({ locale }: { locale: 'ru' | 'en' }) {
  return (
    <section style={{ padding: '26px 18px 0' }}>
      <Link
        href="/pricing"
        className="flex items-center"
        style={{
          gap: 14,
          borderRadius: 18,
          border: '1px solid rgba(255,255,255,.10)',
          background: 'rgba(255,255,255,.03)',
          padding: 16,
          minHeight: 48,
        }}
      >
        <span aria-hidden style={{ color: 'var(--accent)', fontSize: 22 }}>✦</span>
        <span className="flex-1 min-w-0">
          <span className="block" style={{ fontSize: '14.5px', fontWeight: 700 }}>
            {locale === 'ru' ? 'Premium — без лимитов' : 'Premium — no limits'}
          </span>
          <span className="block" style={{ fontSize: '12.5px', color: '#9A94A6', marginTop: 2 }}>
            {locale === 'ru' ? 'Оплата Telegram Stars, без карты' : 'Pay with Telegram Stars, no card needed'}
          </span>
        </span>
        <span aria-hidden style={{ color: 'var(--accent)' }}>→</span>
      </Link>
    </section>
  );
}
