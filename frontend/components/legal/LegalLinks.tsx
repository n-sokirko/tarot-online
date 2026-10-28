'use client';

import Link from 'next/link';
import { useTranslations } from 'next-intl';

const LINK_STYLE = { color: 'rgba(224,178,108,0.85)', textDecoration: 'underline', textUnderlineOffset: 3 } as const;

/** "<prefix> Terms <and> Privacy Policy", each a link, in the visitor's language. */
function Links({ prefix }: { prefix: string }) {
  const t = useTranslations('legal');
  return (
    <>
      {prefix}{' '}
      <Link href="/terms" target="_blank" style={LINK_STYLE}>{t('terms')}</Link>
      {' '}{t('accept_and')}{' '}
      <Link href="/privacy" target="_blank" style={LINK_STYLE}>{t('privacy')}</Link>
    </>
  );
}

/** The required checkbox on the registration form. */
export function AcceptTerms({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  const t = useTranslations('legal');
  return (
    <label className="flex items-start gap-3 text-xs leading-relaxed cursor-pointer"
           style={{ color: 'rgba(242,237,228,0.65)' }}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 h-4 w-4 shrink-0"
        style={{ accentColor: '#E0B26C' }}
      />
      <span><Links prefix={t('accept_prefix')} /></span>
    </label>
  );
}

/** A one-line notice where there is no checkbox: continuing is the acceptance. */
export function TermsNotice() {
  const t = useTranslations('legal');
  return (
    <p className="text-xs text-center leading-relaxed" style={{ color: 'rgba(242,237,228,0.4)' }}>
      <Links prefix={t('continue_notice')} />
    </p>
  );
}

/** Two quiet links, for a footer or a settings page. */
export function LegalFooterLinks() {
  const t = useTranslations('legal');
  return (
    <nav className="flex flex-wrap justify-center gap-x-5 gap-y-1 text-xs" aria-label={t('footer')}>
      <Link href="/terms" style={LINK_STYLE}>{t('terms')}</Link>
      <Link href="/privacy" style={LINK_STYLE}>{t('privacy')}</Link>
    </nav>
  );
}
