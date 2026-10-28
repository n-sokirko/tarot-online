import type { Metadata } from 'next';
import { getLocale, getTranslations } from 'next-intl/server';
import LegalDocument from '@/components/legal/LegalDocument';
import { getLegalDoc, isLegalFallback } from '@/lib/legal';

export async function generateMetadata(): Promise<Metadata> {
  const doc = getLegalDoc('privacy', await getLocale());
  return { title: `${doc.title} · Tarot Online` };
}

export default async function PrivacyPage() {
  const locale = await getLocale();
  const t = await getTranslations('legal');
  return (
    <LegalDocument
      doc={getLegalDoc('privacy', locale)}
      notice={isLegalFallback(locale) ? t('translation_notice') : undefined}
      other={{ href: '/terms', label: t('terms') }}
    />
  );
}
