import type { Metadata } from 'next';
import Script from 'next/script';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, getLocale } from 'next-intl/server';
import { JetBrains_Mono, Manrope, Prata } from 'next/font/google';
import { AuthProvider } from '@/lib/auth-context';
import { SettingsProvider } from '@/lib/settings-context';
import Navbar from '@/components/layout/Navbar';
import BottomBar from '@/components/layout/BottomBar';
import TelegramInit from '@/components/telegram/TelegramInit';
import { RitualProvider } from '@/lib/ritual-context';
import type { Locale } from '@/lib/i18n-config';
import './globals.css';

// Design system "Обсидиан" (design_handoff_tarot_redesign): Prata for headings,
// card names and quotes; Manrope for interface text; JetBrains Mono for labels,
// counters and card numbers. next/font self-hosts them, so no request goes to
// Google at runtime. All three ship Cyrillic.
const prata = Prata({
  subsets: ['latin', 'cyrillic'],
  weight: '400',
  variable: '--font-prata',
  display: 'swap',
});

const manrope = Manrope({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-manrope',
  display: 'swap',
});

const mono = JetBrains_Mono({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Tarot Online',
  description: 'Mystical online tarot readings — ask, shuffle, draw, reflect.',
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const messages = await getMessages();
  const locale = (await getLocale()) as Locale;

  return (
    <html
      lang={locale}
      className={`${prata.variable} ${manrope.variable} ${mono.variable}`}
    >
      <head>
        {/* Telegram Mini App SDK — must load before hydration so
            window.Telegram.WebApp exists when TelegramInit / openInvoice run.
            Without this, auto-login and the native Stars sheet never fire. */}
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
      </head>
      <body className="min-h-screen bg-midnight text-mist font-sans antialiased">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <AuthProvider>
            <SettingsProvider>
            {/* Initialises Telegram WebApp and auto-logs-in Mini App users */}
            <TelegramInit />
            <RitualProvider>
            <Navbar locale={locale} />
            <div className="pt-14 pb-[92px] md:pb-0">
              {children}
            </div>
            <BottomBar />
            </RitualProvider>
            </SettingsProvider>
          </AuthProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
