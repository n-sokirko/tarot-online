'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useLocale } from 'next-intl';
import { listNatalCharts } from '@/lib/api';
import { getAccessToken } from '@/lib/auth';
import type { NatalChart } from '@/lib/types';

const SIGNS_RU: Record<string, string> = {
  Aries:'Овен', Taurus:'Телец', Gemini:'Близнецы', Cancer:'Рак',
  Leo:'Лев', Virgo:'Дева', Libra:'Весы', Scorpio:'Скорпион',
  Sagittarius:'Стрелец', Capricorn:'Козерог', Aquarius:'Водолей', Pisces:'Рыбы',
};

const T = {
  ru: {
    title: 'Мои натальные карты',
    subtitle: 'История сохранённых карт',
    empty: 'Натальных карт пока нет',
    empty_hint: 'Рассчитай свою первую карту',
    calculate: 'Рассчитать карту',
    login_required: 'Войдите, чтобы увидеть сохранённые карты',
    login: 'Войти',
    sun: 'Солнце', moon: 'Луна', asc: 'ASC',
    open: 'Открыть',
  },
  en: {
    title: 'My Natal Charts',
    subtitle: 'Saved charts history',
    empty: 'No natal charts yet',
    empty_hint: 'Calculate your first chart',
    calculate: 'Calculate chart',
    login_required: 'Sign in to see saved charts',
    login: 'Sign in',
    sun: 'Sun', moon: 'Moon', asc: 'ASC',
    open: 'Open',
  },
  de: {
    title: 'Meine Geburtshoroskope',
    subtitle: 'Verlauf gespeicherter Horoskope',
    empty: 'Noch keine Geburtshoroskope',
    empty_hint: 'Berechne dein erstes Horoskop',
    calculate: 'Horoskop berechnen',
    login_required: 'Melde dich an, um gespeicherte Horoskope zu sehen',
    login: 'Anmelden',
    sun: 'Sonne', moon: 'Mond', asc: 'ASZ',
    open: 'Öffnen',
  },
  fr: {
    title: 'Mes thèmes natals',
    subtitle: 'Historique des thèmes enregistrés',
    empty: 'Aucun thème natal pour l’instant',
    empty_hint: 'Calcule ton premier thème',
    calculate: 'Calculer le thème',
    login_required: 'Connecte-toi pour voir les thèmes enregistrés',
    login: 'Connexion',
    sun: 'Soleil', moon: 'Lune', asc: 'ASC',
    open: 'Ouvrir',
  },
  es: {
    title: 'Mis cartas natales',
    subtitle: 'Historial de cartas guardadas',
    empty: 'Aún no hay cartas natales',
    empty_hint: 'Calcula tu primera carta',
    calculate: 'Calcular carta',
    login_required: 'Inicia sesión para ver las cartas guardadas',
    login: 'Entrar',
    sun: 'Sol', moon: 'Luna', asc: 'ASC',
    open: 'Abrir',
  },
  pt: {
    title: 'Os meus mapas natais',
    subtitle: 'Histórico de mapas guardados',
    empty: 'Ainda não há mapas natais',
    empty_hint: 'Calcula o teu primeiro mapa',
    calculate: 'Calcular mapa',
    login_required: 'Inicia sessão para ver os mapas guardados',
    login: 'Entrar',
    sun: 'Sol', moon: 'Lua', asc: 'ASC',
    open: 'Abrir',
  },
  uk: {
    title: 'Мої натальні карти',
    subtitle: 'Історія збережених карт',
    empty: 'Натальних карт поки немає',
    empty_hint: 'Розрахуй свою першу карту',
    calculate: 'Розрахувати карту',
    login_required: 'Увійдіть, щоб побачити збережені карти',
    login: 'Увійти',
    sun: 'Сонце', moon: 'Місяць', asc: 'ASC',
    open: 'Відкрити',
  },
} as const;

function ChartCard({ chart, locale }: { chart: NatalChart; locale: 'ru' | 'en' }) {
  const t = T[locale] ?? T.en;
  const sun = chart.planets.find((p) => p.name === 'Sun');
  const moon = chart.planets.find((p) => p.name === 'Moon');

  const signName = (sign: string) =>
    locale === 'ru' ? (SIGNS_RU[sign] ?? sign) : sign;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl p-5 flex flex-col gap-3"
      style={{
        background: 'rgba(28,24,64,0.6)',
        border: '1px solid rgba(212,175,55,0.15)',
      }}
    >
      {/* Name & date */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-serif text-base" style={{ color: '#d4af37' }}>
            {chart.birth_name || chart.birth_city}
          </p>
          <p className="font-sans text-xs mt-0.5" style={{ color: 'rgba(201,194,224,0.45)' }}>
            {chart.birth_date}{chart.birth_time ? ` · ${chart.birth_time}` : ''} · {chart.birth_city}
          </p>
        </div>
        <Link
          href={`/natal?chart=${chart.id}`}
          className="px-3 py-1.5 rounded-full text-[10px] font-sans uppercase tracking-wider flex-shrink-0"
          style={{ border: '1px solid rgba(212,175,55,0.3)', color: 'rgba(212,175,55,0.7)', letterSpacing: '0.12em' }}
        >
          {t.open}
        </Link>
      </div>

      {/* Big 3 chips */}
      <div className="flex flex-wrap gap-2">
        {sun && (
          <span className="px-2.5 py-1 rounded-full text-xs font-sans" style={{ background: 'rgba(212,175,55,0.08)', color: 'rgba(212,175,55,0.85)', border: '1px solid rgba(212,175,55,0.2)' }}>
            ☉ {signName(sun.sign)}
          </span>
        )}
        {moon && (
          <span className="px-2.5 py-1 rounded-full text-xs font-sans" style={{ background: 'rgba(180,140,220,0.08)', color: 'rgba(180,140,220,0.85)', border: '1px solid rgba(180,140,220,0.2)' }}>
            ☽ {signName(moon.sign)}
          </span>
        )}
        {chart.ascendant !== null && (
          <span className="px-2.5 py-1 rounded-full text-xs font-sans" style={{ background: 'rgba(80,180,180,0.08)', color: 'rgba(80,200,200,0.85)', border: '1px solid rgba(80,180,180,0.2)' }}>
            ↑ {t.asc} {chart.ascendant.toFixed(0)}°
          </span>
        )}
      </div>
    </motion.div>
  );
}

export default function NatalHistoryPage() {
  const locale = useLocale() as 'ru' | 'en';
  const t = T[locale] ?? T.en;
  const [charts, setCharts] = useState<NatalChart[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    setIsLoggedIn(!!token);
    if (!token) { setLoading(false); return; }
    listNatalCharts()
      .then(setCharts)
      .catch(() => setCharts([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen px-4 py-12">
      <div className="max-w-2xl mx-auto flex flex-col gap-8">
        <header className="text-center flex flex-col gap-2">
          <p className="font-sans text-xs uppercase tracking-widest" style={{ color: 'rgba(212,175,55,0.55)', letterSpacing: '0.25em' }}>
            ✦ {t.subtitle} ✦
          </p>
          <h1 className="font-serif text-3xl" style={{ color: '#d4af37' }}>{t.title}</h1>
        </header>

        {!isLoggedIn ? (
          <div className="text-center flex flex-col gap-4 py-12">
            <p className="font-serif text-sm" style={{ color: 'rgba(201,194,224,0.6)' }}>{t.login_required}</p>
            <Link href="/login?next=/natal/history" className="px-6 py-2.5 rounded-full text-xs font-sans uppercase tracking-widest mx-auto"
              style={{ background: 'rgba(212,175,55,0.1)', border: '1px solid #d4af37', color: '#d4af37', letterSpacing: '0.18em' }}>
              {t.login}
            </Link>
          </div>
        ) : loading ? (
          <div className="text-center py-16">
            <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 1.5, repeat: Infinity }}
              className="font-serif text-sm" style={{ color: 'rgba(212,175,55,0.6)' }}>
              ✦ ...
            </motion.div>
          </div>
        ) : charts.length === 0 ? (
          <div className="text-center flex flex-col gap-4 py-12">
            <p className="font-serif text-sm" style={{ color: 'rgba(201,194,224,0.55)' }}>{t.empty}</p>
            <p className="font-sans text-xs" style={{ color: 'rgba(201,194,224,0.35)' }}>{t.empty_hint}</p>
            <Link href="/natal" className="px-6 py-2.5 rounded-full text-xs font-sans uppercase tracking-widest mx-auto"
              style={{ background: 'rgba(212,175,55,0.1)', border: '1px solid #d4af37', color: '#d4af37', letterSpacing: '0.18em' }}>
              ✦ {t.calculate}
            </Link>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {charts.map((chart) => (
              <ChartCard key={chart.id} chart={chart} locale={locale} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
