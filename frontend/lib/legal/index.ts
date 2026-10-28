import { LEGAL_CONFIG } from './config';
import { privacyEn } from './privacy.en';
import { privacyRu } from './privacy.ru';
import { termsEn } from './terms.en';
import { termsRu } from './terms.ru';
import type { LegalBlock, LegalDoc, LegalKind } from './types';

export type { LegalBlock, LegalDoc, LegalKind } from './types';

const DOCS: Record<LegalKind, Record<'ru' | 'en', LegalDoc>> = {
  terms: { ru: termsRu, en: termsEn },
  privacy: { ru: privacyRu, en: privacyEn },
};

/** The two wordings we maintain. Every other UI language reads the English text. */
export function legalLanguage(locale: string): 'ru' | 'en' {
  return locale === 'ru' ? 'ru' : 'en';
}

/** True when the visitor's language has no translation of the legal text. */
export function isLegalFallback(locale: string): boolean {
  return locale !== 'ru' && locale !== 'en';
}

const FALLBACKS = {
  ru: {
    operator: 'будет указан после регистрации (самозанятость или ИП)',
    contacts: 'контакты поддержки будут добавлены',
  },
  en: {
    operator: 'to be named once registered (self-employed or sole proprietor)',
    contacts: 'support contacts will be added',
  },
} as const;

function formatDate(iso: string, lang: 'ru' | 'en'): string {
  const d = new Date(`${iso}T00:00:00Z`);
  const formatted = new Intl.DateTimeFormat(lang === 'ru' ? 'ru-RU' : 'en-GB', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  }).format(d);
  // Russian ends the date with "г." and the sentence adds its own full stop: "г..".
  return lang === 'ru' ? `${formatted.replace(/\s*г\.$/, '')} года` : formatted;
}

export function legalContacts(lang: 'ru' | 'en'): string {
  const parts: string[] = [];
  if (LEGAL_CONFIG.supportTelegram) parts.push(`Telegram ${LEGAL_CONFIG.supportTelegram}`);
  if (LEGAL_CONFIG.supportEmail) parts.push(`e-mail ${LEGAL_CONFIG.supportEmail}`);
  return parts.length ? parts.join(', ') : FALLBACKS[lang].contacts;
}

/** Replace the {{TOKENS}} that come from LEGAL_CONFIG. */
export function fill(text: string, lang: 'ru' | 'en'): string {
  return text
    .replaceAll('{{DATE}}', formatDate(LEGAL_CONFIG.effectiveDate, lang))
    .replaceAll('{{OPERATOR}}', LEGAL_CONFIG.operatorName || FALLBACKS[lang].operator)
    .replaceAll('{{CONTACTS}}', legalContacts(lang));
}

function fillBlock(block: LegalBlock, lang: 'ru' | 'en'): LegalBlock {
  if ('p' in block) return { p: fill(block.p, lang) };
  if ('ul' in block) return { ul: block.ul.map((s) => fill(s, lang)) };
  return {
    table: {
      head: block.table.head.map((s) => fill(s, lang)),
      rows: block.table.rows.map((r) => r.map((s) => fill(s, lang))),
    },
  };
}

/** The document for a visitor's locale, with operator, contacts and date filled in. */
export function getLegalDoc(kind: LegalKind, locale: string): LegalDoc {
  const lang = legalLanguage(locale);
  const doc = DOCS[kind][lang];
  return {
    title: doc.title,
    intro: fill(doc.intro, lang),
    sections: doc.sections.map((s) => ({
      heading: s.heading,
      blocks: s.blocks.map((b) => fillBlock(b, lang)),
    })),
  };
}
