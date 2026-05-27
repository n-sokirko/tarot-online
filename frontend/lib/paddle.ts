'use client';

/**
 * Thin wrapper around Paddle.js (loaded from the CDN on demand).
 *
 * We don't pull paddle as an npm dependency — the official SDK is just a
 * thin wrapper around the same `Paddle.Checkout.open()` call, and loading
 * from their CDN keeps our bundle small and our integration version-locked
 * to whatever Paddle ships.
 */

declare global {
  interface Window {
    Paddle?: {
      Environment: { set: (env: 'sandbox' | 'production') => void };
      Initialize: (opts: { token: string; eventCallback?: (e: unknown) => void }) => void;
      Checkout: {
        open: (opts: PaddleCheckoutOptions) => void;
      };
    };
  }
}

export interface PaddleCheckoutOptions {
  items: { priceId: string; quantity?: number }[];
  customer?: { email?: string };
  customData?: Record<string, string>;
  settings?: {
    theme?: 'dark' | 'light';
    locale?: string;
    successUrl?: string;
  };
}

const PADDLE_SCRIPT_URL = 'https://cdn.paddle.com/paddle/v2/paddle.js';
let scriptPromise: Promise<void> | null = null;
let initializedEnv: string | null = null;

function loadScript(): Promise<void> {
  if (typeof window === 'undefined') return Promise.reject(new Error('SSR'));
  if (window.Paddle) return Promise.resolve();
  if (scriptPromise) return scriptPromise;
  scriptPromise = new Promise<void>((resolve, reject) => {
    const el = document.createElement('script');
    el.src = PADDLE_SCRIPT_URL;
    el.async = true;
    el.onload = () => resolve();
    el.onerror = () => reject(new Error('Failed to load Paddle.js'));
    document.head.appendChild(el);
  });
  return scriptPromise;
}

export async function ensurePaddle(env: 'sandbox' | 'production', token: string): Promise<NonNullable<Window['Paddle']>> {
  await loadScript();
  const paddle = window.Paddle!;
  // Re-initialize if env changes or first time
  if (initializedEnv !== env) {
    paddle.Environment.set(env);
    paddle.Initialize({ token });
    initializedEnv = env;
  }
  return paddle;
}

export async function openCheckout(opts: {
  env: 'sandbox' | 'production';
  token: string;
  priceId: string;
  email?: string;
  customData: Record<string, string>;
  locale?: string;
}) {
  const paddle = await ensurePaddle(opts.env, opts.token);
  paddle.Checkout.open({
    items: [{ priceId: opts.priceId, quantity: 1 }],
    customer: opts.email ? { email: opts.email } : undefined,
    customData: opts.customData,
    settings: {
      theme: 'dark',
      locale: opts.locale ?? 'en',
      successUrl: typeof window !== 'undefined'
        ? `${window.location.origin}/account?upgrade=success`
        : undefined,
    },
  });
}
