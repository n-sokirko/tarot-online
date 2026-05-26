import { getRequestConfig } from 'next-intl/server';
import { cookies } from 'next/headers';

export const locales = ['ru', 'en'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'ru';

export default getRequestConfig(async () => {
  const cookieStore = await cookies();
  const raw = cookieStore.get('NEXT_LOCALE')?.value ?? defaultLocale;
  const locale = (['ru', 'en'].includes(raw) ? raw : defaultLocale) as Locale;
  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default,
  };
});
