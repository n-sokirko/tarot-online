'use client';

/**
 * TelegramInit — silently initialises the Telegram Mini App.
 *
 * When the page is opened inside a Telegram WebView:
 *  1. Calls tg.ready() so Telegram hides the loading indicator.
 *  2. Calls tg.expand() to request full-screen height.
 *  3. Sets the header / background colour to match the app theme.
 *  4. If the user has no JWT yet, sends initData to the backend and logs in
 *     automatically — no form, no password, just Telegram identity.
 *
 * Outside Telegram (normal browser) this component does nothing.
 */

import { useEffect, useRef } from 'react';
import { saveTokens } from '@/lib/auth';
import { useAuth } from '@/lib/auth-context';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// Minimal type declarations for the Telegram WebApp JS SDK
declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData: string;
        initDataUnsafe: Record<string, unknown>;
        colorScheme: 'light' | 'dark';
        ready: () => void;
        expand: () => void;
        close: () => void;
        setHeaderColor: (color: string) => void;
        setBackgroundColor: (color: string) => void;
      };
    };
  }
}

export default function TelegramInit() {
  const { refetch } = useAuth();
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const tg = window.Telegram?.WebApp;
    if (!tg?.initData) return; // not running inside Telegram — do nothing

    // Tell Telegram the app is ready (hides the native loading spinner)
    tg.ready();
    // Expand to full available height
    tg.expand();
    // Match the dark mystical theme
    try {
      tg.setHeaderColor('#0b0b1f');
      tg.setBackgroundColor('#0b0b1f');
    } catch {
      // Older Telegram clients may not support colour customisation — ignore
    }

    // Auto-login: only if no token stored yet
    const stored = localStorage.getItem('tarot_access');
    if (stored) return;

    fetch(`${API_BASE}/api/v1/auth/telegram-webapp/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ init_data: tg.initData }),
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data: { access: string; refresh: string }) => {
        if (data?.access && data?.refresh) {
          saveTokens(data.access, data.refresh);
          // Refresh the auth context so Navbar / routes reflect the logged-in state
          return refetch();
        }
      })
      .catch(() => {
        // Silent failure — user can still log in manually via the login page
      });
  }, [refetch]);

  return null;
}
