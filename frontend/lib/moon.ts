/**
 * Moon phase for the home screen's date line ("21 сентября · убывающая луна").
 *
 * Computed here rather than fetched: it is pure arithmetic on the synodic
 * month, the same for every visitor, and the screen should not wait on a
 * request just to label the date. Accurate to within a few hours, which is
 * plenty for naming one of eight phases.
 */

const SYNODIC_MONTH = 29.53058867; // days
// A known new moon: 2000-01-06 18:14 UTC.
const KNOWN_NEW_MOON = Date.UTC(2000, 0, 6, 18, 14);
const DAY_MS = 86_400_000;

/** Age of the moon in days, 0 ≤ age < 29.53. */
export function moonAge(date: Date = new Date()): number {
  const days = (date.getTime() - KNOWN_NEW_MOON) / DAY_MS;
  const age = days % SYNODIC_MONTH;
  return age < 0 ? age + SYNODIC_MONTH : age;
}

const NAMES = {
  ru: [
    'новолуние',
    'растущий серп',
    'первая четверть',
    'растущая луна',
    'полнолуние',
    'убывающая луна',
    'последняя четверть',
    'убывающий серп',
  ],
  en: [
    'new moon',
    'waxing crescent',
    'first quarter',
    'waxing gibbous',
    'full moon',
    'waning gibbous',
    'last quarter',
    'waning crescent',
  ],
} as const;

/** One of the eight conventional phases, centred on the principal ones. */
export function moonPhaseName(locale: 'ru' | 'en', date: Date = new Date()): string {
  const eighth = SYNODIC_MONTH / 8;
  // Shift by half a slot so "full moon" covers the days around the full moon
  // rather than starting exactly on it.
  const index = Math.floor((moonAge(date) + eighth / 2) / eighth) % 8;
  return NAMES[locale][index];
}

/** "21 сентября · убывающая луна" */
export function dateLine(locale: 'ru' | 'en', date: Date = new Date()): string {
  const day = new Intl.DateTimeFormat(locale === 'ru' ? 'ru-RU' : 'en-GB', {
    day: 'numeric',
    month: 'long',
  }).format(date);
  return `${day} · ${moonPhaseName(locale, date)}`;
}
