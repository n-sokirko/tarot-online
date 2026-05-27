'use client';

import { useCallback } from 'react';

type Locale = 'ru' | 'en';

interface LocaleSwitcherProps {
  currentLocale: Locale;
}

export default function LocaleSwitcher({ currentLocale }: LocaleSwitcherProps) {
  const switchTo = useCallback((locale: Locale) => {
    document.cookie = `NEXT_LOCALE=${locale}; path=/; max-age=31536000; SameSite=Lax`;
    window.location.reload();
  }, []);

  return (
    <div
      className="flex items-center gap-1 font-sans text-xs tracking-widest"
      style={{ color: 'rgba(201,194,224,0.5)', letterSpacing: '0.1em' }}
    >
      <button
        onClick={() => switchTo('ru')}
        className="transition-colors"
        style={{
          color: currentLocale === 'ru' ? '#d4af37' : 'rgba(201,194,224,0.4)',
          fontWeight: currentLocale === 'ru' ? 600 : 400,
        }}
      >
        RU
      </button>
      <span style={{ color: 'rgba(212,175,55,0.3)' }}>|</span>
      <button
        onClick={() => switchTo('en')}
        className="transition-colors"
        style={{
          color: currentLocale === 'en' ? '#d4af37' : 'rgba(201,194,224,0.4)',
          fontWeight: currentLocale === 'en' ? 600 : 400,
        }}
      >
        EN
      </button>
    </div>
  );
}
