import { getRequestConfig } from 'next-intl/server';
import { cookies, headers } from 'next/headers';
import { locales, defaultLocale, type Locale } from '@/lib/i18n-config';

function detectFromAcceptLanguage(acceptLang: string): Locale {
  const langs = acceptLang.split(',').map((l) => l.split(';')[0].trim().toLowerCase());
  for (const lang of langs) {
    if (lang.startsWith('ru')) return 'ru';
    if (lang.startsWith('uk')) return 'uk';
    if (lang.startsWith('en')) return 'en';
    if (lang.startsWith('de')) return 'de';
    if (lang.startsWith('fr')) return 'fr';
    if (lang.startsWith('es')) return 'es';
    if (lang.startsWith('pt')) return 'pt';
  }
  return defaultLocale;
}

export default getRequestConfig(async () => {
  const cookieStore = await cookies();
  const cookieLocale = cookieStore.get('NEXT_LOCALE')?.value;

  let locale: Locale;
  if (cookieLocale && (locales as readonly string[]).includes(cookieLocale)) {
    locale = cookieLocale as Locale;
  } else {
    const headersList = await headers();
    const acceptLang = headersList.get('accept-language') ?? '';
    locale = detectFromAcceptLanguage(acceptLang);
  }

  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default,
  };
});
