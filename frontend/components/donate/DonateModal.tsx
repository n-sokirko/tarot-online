'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { ApiError, startTelegramDonation } from '@/lib/api';
import { getAccessToken } from '@/lib/auth';

type TgWebApp = {
  openInvoice?: (url: string, cb: (status: string) => void) => void;
  openTelegramLink?: (url: string) => void;
  initData?: string;
};

function getTgWebApp(): TgWebApp | undefined {
  if (typeof window === 'undefined') return undefined;
  return (window as unknown as { Telegram?: { WebApp?: TgWebApp } }).Telegram?.WebApp;
}

const PRESETS = [25, 50, 100, 250, 500];

const COPY = {
  ru: {
    title: 'Поддержать проект',
    subtitle: 'Tarot Online живёт благодаря вам. Подари немного звёзд ⭐',
    custom: 'Своя сумма',
    custom_placeholder: 'Сколько звёзд?',
    donate: 'Подарить',
    donating: 'Открываю оплату…',
    thanks: '✨ Спасибо за поддержку! Твой дар согревает проект.',
    cancelled: 'Оплата отменена.',
    error: 'Не удалось открыть оплату. Попробуй ещё раз.',
    login_needed: 'Войди, чтобы поддержать проект.',
    close: 'Закрыть',
    stars: 'звёзд',
  },
  en: {
    title: 'Support the project',
    subtitle: 'Tarot Online lives thanks to you. Send a few stars ⭐',
    custom: 'Custom amount',
    custom_placeholder: 'How many stars?',
    donate: 'Send',
    donating: 'Opening payment…',
    thanks: '✨ Thank you for your support! Your gift warms the project.',
    cancelled: 'Payment cancelled.',
    error: 'Failed to open payment. Try again.',
    login_needed: 'Sign in to support the project.',
    close: 'Close',
    stars: 'stars',
  },
} as const;

export default function DonateModal({
  open,
  onClose,
  locale,
  botUsername,
}: {
  open: boolean;
  onClose: () => void;
  locale: 'ru' | 'en';
  botUsername?: string;
}) {
  const t = COPY[locale];
  const router = useRouter();
  const [amount, setAmount] = useState<number>(100);
  const [custom, setCustom] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null);

  useEffect(() => {
    if (!open) {
      setBusy(false);
      setMsg(null);
      setCustom('');
      setAmount(100);
    }
  }, [open]);

  const effectiveStars = custom.trim() ? Math.floor(Number(custom)) : amount;

  const handleDonate = useCallback(async () => {
    setMsg(null);
    const stars = effectiveStars;
    if (!stars || stars < 1 || !Number.isFinite(stars)) {
      setMsg({ kind: 'err', text: t.error });
      return;
    }
    if (!getAccessToken()) {
      router.push('/login?next=/pricing');
      return;
    }

    const tg = getTgWebApp();
    const insideMiniApp = !!tg?.initData;
    setBusy(true);
    try {
      if (insideMiniApp && tg?.openInvoice) {
        const payload = await startTelegramDonation(stars);
        tg.openInvoice(payload.invoice_link, (status: string) => {
          setBusy(false);
          if (status === 'paid') setMsg({ kind: 'ok', text: t.thanks });
          else if (status === 'cancelled') setMsg({ kind: 'err', text: t.cancelled });
          else if (status === 'failed') setMsg({ kind: 'err', text: t.error });
        });
      } else if (botUsername) {
        // Browser fallback: deep-link the bot, which sends the Stars invoice.
        const url = `https://t.me/${botUsername}?start=donate_${stars}`;
        if (insideMiniApp && tg?.openTelegramLink) tg.openTelegramLink(url);
        else window.open(url, '_blank', 'noopener,noreferrer');
        setBusy(false);
      } else {
        setBusy(false);
        setMsg({ kind: 'err', text: t.error });
      }
    } catch (e) {
      setBusy(false);
      setMsg({ kind: 'err', text: e instanceof ApiError ? t.error : t.error });
    }
  }, [effectiveStars, botUsername, router, t]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center px-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{ background: 'rgba(5,5,15,0.75)', backdropFilter: 'blur(6px)' }}
          onClick={onClose}
        >
          <motion.div
            className="w-full max-w-sm rounded-3xl p-6 flex flex-col gap-5"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 26 }}
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'linear-gradient(165deg, rgba(28,24,64,0.95), rgba(11,11,31,0.97))',
              border: '1px solid rgba(212,175,55,0.3)',
              boxShadow: '0 12px 48px rgba(0,0,0,0.6)',
            }}
          >
            <header className="text-center flex flex-col gap-1.5">
              <span style={{ fontSize: '2rem', lineHeight: 1 }}>⭐</span>
              <h2 className="font-serif text-2xl" style={{ color: '#d4af37' }}>{t.title}</h2>
              <p className="font-sans text-xs" style={{ color: 'rgba(201,194,224,0.65)' }}>
                {t.subtitle}
              </p>
            </header>

            {/* Preset amounts */}
            <div className="grid grid-cols-3 gap-2">
              {PRESETS.map((p) => {
                const active = !custom.trim() && amount === p;
                return (
                  <button
                    key={p}
                    onClick={() => { setAmount(p); setCustom(''); }}
                    className="py-3 rounded-xl font-serif text-sm transition-colors"
                    style={{
                      background: active ? 'rgba(212,175,55,0.18)' : 'rgba(212,175,55,0.05)',
                      border: `1px solid ${active ? '#d4af37' : 'rgba(212,175,55,0.2)'}`,
                      color: active ? '#d4af37' : 'rgba(201,194,224,0.8)',
                    }}
                  >
                    {p} ⭐
                  </button>
                );
              })}
              {/* Custom */}
              <input
                type="number"
                inputMode="numeric"
                min={1}
                value={custom}
                onChange={(e) => setCustom(e.target.value)}
                placeholder={t.custom_placeholder}
                className="py-3 px-2 rounded-xl font-serif text-sm text-center bg-transparent outline-none col-span-3"
                style={{
                  border: `1px solid ${custom.trim() ? '#d4af37' : 'rgba(212,175,55,0.2)'}`,
                  color: 'rgba(201,194,224,0.9)',
                  background: 'rgba(212,175,55,0.04)',
                }}
              />
            </div>

            {msg && (
              <p
                className="text-center text-xs font-sans"
                style={{ color: msg.kind === 'ok' ? '#d4af37' : '#ff8a8a' }}
              >
                {msg.text}
              </p>
            )}

            <button
              onClick={() => void handleDonate()}
              disabled={busy}
              className="w-full py-3 rounded-full font-serif text-sm tracking-widest uppercase flex items-center justify-center gap-2"
              style={{
                background: 'linear-gradient(135deg, rgba(212,175,55,0.25), rgba(212,175,55,0.08))',
                border: '1px solid #d4af37',
                color: '#d4af37',
                letterSpacing: '0.12em',
                opacity: busy ? 0.6 : 1,
              }}
            >
              {busy ? t.donating : `✦ ${t.donate} ${effectiveStars > 0 ? `${effectiveStars} ⭐` : ''}`}
            </button>

            <button
              onClick={onClose}
              className="text-[0.7rem] font-sans uppercase tracking-widest mx-auto"
              style={{ color: 'rgba(201,194,224,0.45)', letterSpacing: '0.2em' }}
            >
              {t.close}
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
