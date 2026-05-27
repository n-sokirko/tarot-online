import type { Metadata } from 'next';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, getLocale } from 'next-intl/server';
import { Cormorant_Garamond, Inter } from 'next/font/google';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from '@/lib/auth-context';
import Navbar from '@/components/layout/Navbar';
import BottomBar from '@/components/layout/BottomBar';
import type { Locale } from '@/i18n';
import './globals.css';

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? '';

const cormorant = Cormorant_Garamond({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500', '600', '700'],
  style: ['normal', 'italic'],
  variable: '--font-cormorant',
  display: 'swap',
});

const inter = Inter({
  subsets: ['latin', 'cyrillic'],
  variable: '--font-inter',
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
      className={`${cormorant.variable} ${inter.variable}`}
    >
      <body className="min-h-screen bg-midnight text-mist font-sans antialiased">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <AuthProvider>
              <Navbar locale={locale} />
              <div style={{ paddingTop: '56px', paddingBottom: '60px' }} className="md:pb-0">
                {children}
              </div>
              <BottomBar />
            </AuthProvider>
          </GoogleOAuthProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
