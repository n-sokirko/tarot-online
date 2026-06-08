export const locales = ['ru', 'en', 'de', 'fr', 'es', 'pt', 'uk'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'ru';

export const LOCALE_LABELS: Record<Locale, string> = {
  ru: 'Русский',
  en: 'English',
  de: 'Deutsch',
  fr: 'Français',
  es: 'Español',
  pt: 'Português',
  uk: 'Українська',
};

export const LOCALE_FLAGS: Record<Locale, string> = {
  ru: '🇷🇺',
  en: '🇬🇧',
  de: '🇩🇪',
  fr: '🇫🇷',
  es: '🇪🇸',
  pt: '🇧🇷',
  uk: '🇺🇦',
};
