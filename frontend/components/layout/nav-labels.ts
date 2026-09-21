/** Navigation labels shared by the header, the tab bar and the "Ещё" menu. */

const LABELS = {
  ru: {
    tarot: 'Таро', runes: 'Руны', natal: 'Натальная карта',
    daily: 'Карта дня', numerology: 'Числа', horoscope: 'Гороскоп',
    journal: 'Дневник', freeSpread: 'Свой расклад',
    more: 'Ещё', premium: 'Premium', settings: 'Настройки',
    login: 'Войти', register: 'Регистрация', logout: 'Выйти',
    streak: (n: number) => `${n} ${plural(n, ['день', 'дня', 'дней'])}`,
  },
  en: {
    tarot: 'Tarot', runes: 'Runes', natal: 'Natal chart',
    daily: 'Card of the day', numerology: 'Numbers', horoscope: 'Horoscope',
    journal: 'Journal', freeSpread: 'Your own spread',
    more: 'More', premium: 'Premium', settings: 'Settings',
    login: 'Log in', register: 'Sign up', logout: 'Log out',
    streak: (n: number) => `${n} ${n === 1 ? 'day' : 'days'}`,
  },
  de: {
    tarot: 'Tarot', runes: 'Runen', natal: 'Geburtshoroskop',
    daily: 'Tageskarte', numerology: 'Zahlen', horoscope: 'Horoskop',
    journal: 'Tagebuch', freeSpread: 'Freie Legung',
    more: 'Mehr', premium: 'Premium', settings: 'Einstellungen',
    login: 'Anmelden', register: 'Registrieren', logout: 'Abmelden',
    streak: (n: number) => `${n} ${n === 1 ? 'Tag' : 'Tage'}`,
  },
  fr: {
    tarot: 'Tarot', runes: 'Runes', natal: 'Thème natal',
    daily: 'Carte du jour', numerology: 'Nombres', horoscope: 'Horoscope',
    journal: 'Journal', freeSpread: 'Tirage libre',
    more: 'Plus', premium: 'Premium', settings: 'Réglages',
    login: 'Connexion', register: 'Inscription', logout: 'Déconnexion',
    streak: (n: number) => `${n} ${n === 1 ? 'jour' : 'jours'}`,
  },
  es: {
    tarot: 'Tarot', runes: 'Runas', natal: 'Carta natal',
    daily: 'Carta del día', numerology: 'Números', horoscope: 'Horóscopo',
    journal: 'Diario', freeSpread: 'Tirada libre',
    more: 'Más', premium: 'Premium', settings: 'Ajustes',
    login: 'Entrar', register: 'Registrarse', logout: 'Salir',
    streak: (n: number) => `${n} ${n === 1 ? 'día' : 'días'}`,
  },
  pt: {
    tarot: 'Tarô', runes: 'Runas', natal: 'Mapa natal',
    daily: 'Carta do dia', numerology: 'Números', horoscope: 'Horóscopo',
    journal: 'Diário', freeSpread: 'Tiragem livre',
    more: 'Mais', premium: 'Premium', settings: 'Definições',
    login: 'Entrar', register: 'Registar', logout: 'Sair',
    streak: (n: number) => `${n} ${n === 1 ? 'dia' : 'dias'}`,
  },
  uk: {
    tarot: 'Таро', runes: 'Руни', natal: 'Натальна карта',
    daily: 'Карта дня', numerology: 'Числа', horoscope: 'Гороскоп',
    journal: 'Щоденник', freeSpread: 'Свій розклад',
    more: 'Ще', premium: 'Premium', settings: 'Налаштування',
    login: 'Увійти', register: 'Реєстрація', logout: 'Вийти',
    streak: (n: number) => `${n} ${plural(n, ['день', 'дні', 'днів'])}`,
  },
};

/** Russian/Ukrainian plural: 1 день, 2 дня, 5 дней. */
function plural(n: number, [one, few, many]: [string, string, string]): string {
  const m10 = n % 10;
  const m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}

export type NavLabels = (typeof LABELS)['ru'];

export function navLabels(locale: string): NavLabels {
  return (LABELS as Record<string, NavLabels>)[locale] ?? LABELS.en;
}
