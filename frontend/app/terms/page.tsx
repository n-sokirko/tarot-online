import type { Metadata } from 'next';
import { getLocale, getTranslations } from 'next-intl/server';
import LegalDocument from '@/components/legal/LegalDocument';
import { getLegalDoc, isLegalFallback } from '@/lib/legal';

export async function generateMetadata(): Promise<Metadata> {
  const doc = getLegalDoc('terms', await getLocale());
  return { title: `${doc.title} · Tarot Online` };
}

export default async function TermsPage() {
  const locale = await getLocale();
  const t = await getTranslations('legal');
  return (
    <LegalDocument
      doc={getLegalDoc('terms', locale)}
      notice={isLegalFallback(locale) ? t('translation_notice') : undefined}
      other={{ href: '/privacy', label: t('privacy') }}
    />
  );
}
