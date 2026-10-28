/**
 * The facts the legal pages cannot invent. Fill these in when they exist; until
 * then the pages print a plain "will be added" line instead of a blank, so no
 * placeholder in square brackets is ever shown to a visitor.
 *
 * operatorName: who controls the personal data (full name, or the self-employed /
 *   sole-proprietor name once registered). Belarusian data-protection law expects
 *   people to be able to tell who processes their data.
 * supportTelegram: the dedicated support account, e.g. '@tarot_support'.
 * supportEmail: optional.
 */
export const LEGAL_CONFIG = {
  /** Date the current wording takes effect (ISO). Bump it when the text changes. */
  effectiveDate: '2026-10-28',
  /** Bump with every change that users must accept again. */
  version: '2026-10-28',
  operatorName: '',
  supportTelegram: '',
  supportEmail: '',
} as const;
