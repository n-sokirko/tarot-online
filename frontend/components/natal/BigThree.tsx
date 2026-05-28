'use client';

import { motion } from 'framer-motion';
import type { NatalPlanet } from '@/lib/types';

interface BigThreeProps {
  planets: NatalPlanet[];
  ascendant: number | null;
  isPremium: boolean;
  locale: 'ru' | 'en';
}

const PLANET_MEANINGS: Record<string, { ru: string; en: string }> = {
  Sun: {
    ru: 'Ваша суть, воля и жизненная сила',
    en: 'Your core identity and life force',
  },
  Moon: {
    ru: 'Ваши эмоции, инстинкты и внутренний мир',
    en: 'Your emotions, instincts, and inner world',
  },
};

const ASC_MEANING = {
  ru: 'Ваша маска для мира и первое впечатление',
  en: 'Your outward mask and first impression',
};

const LABELS = {
  ru: {
    asc: 'Асцендент',
    degree: 'градус',
    house: 'дом',
    retrograde: 'ретроградный',
    unknown_time: 'Добавьте время рождения, чтобы узнать Асцендент',
    upgrade: 'Premium открывает все 10 планет и дома',
    upgrade_cta: 'Открыть Premium',
  },
  en: {
    asc: 'Ascendant',
    degree: 'degree',
    house: 'house',
    retrograde: 'retrograde',
    unknown_time: 'Add birth time to discover your Ascendant',
    upgrade: 'Premium unlocks all 10 planets and houses',
    upgrade_cta: 'Unlock Premium',
  },
} as const;

interface CardData {
  glyph: string;
  name: string;
  sign: string;
  signEmoji: string;
  degree: string;
  meaning: string;
  retrograde: boolean;
  house: number;
}

function PlanetCard({ card, locale, delay }: { card: CardData; locale: 'ru' | 'en'; delay: number }) {
  const t = LABELS[locale];
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="flex flex-col items-center text-center rounded-2xl p-6"
      style={{
        background: 'linear-gradient(180deg, rgba(28,24,64,0.7) 0%, rgba(11,11,31,0.7) 100%)',
        border: '1px solid rgba(212,175,55,0.25)',
        boxShadow: '0 0 30px rgba(212,175,55,0.06)',
        minWidth: '140px',
        flex: '1 1 140px',
      }}
    >
      {/* Planet glyph */}
      <div
        className="text-4xl mb-2"
        style={{ color: '#d4af37', textShadow: '0 0 20px rgba(212,175,55,0.3)' }}
      >
        {card.glyph}
      </div>

      {/* Planet name */}
      <div
        className="text-[10px] tracking-widest uppercase mb-1"
        style={{ color: 'rgba(212,175,55,0.7)', letterSpacing: '0.22em' }}
      >
        {card.name}
      </div>

      {/* Sign */}
      <div className="font-serif text-base mb-0.5" style={{ color: 'rgba(201,194,224,0.9)' }}>
        {card.signEmoji} {card.sign}
      </div>

      {/* Degree */}
      <div className="text-xs mb-3" style={{ color: 'rgba(201,194,224,0.45)' }}>
        {card.degree}°{card.retrograde && <span className="ml-1 text-[10px]">{t.retrograde} ℞</span>}
        {card.house > 0 && <span className="ml-1">· {card.house} {t.house}</span>}
      </div>

      {/* Meaning */}
      <p className="font-serif text-xs italic leading-relaxed" style={{ color: 'rgba(201,194,224,0.6)' }}>
        {card.meaning}
      </p>
    </motion.div>
  );
}

export default function BigThree({ planets, ascendant, isPremium, locale }: BigThreeProps) {
  const t = LABELS[locale];

  const sun = planets.find((p) => p.name === 'Sun');
  const moon = planets.find((p) => p.name === 'Moon');

  const cards: CardData[] = [];

  if (sun) {
    cards.push({
      glyph: sun.glyph,
      name: locale === 'ru' ? 'Солнце' : 'Sun',
      sign: sun.sign,
      signEmoji: sun.emoji,
      degree: sun.position.toFixed(1),
      meaning: PLANET_MEANINGS.Sun[locale],
      retrograde: sun.retrograde,
      house: sun.house,
    });
  }

  if (moon) {
    cards.push({
      glyph: moon.glyph,
      name: locale === 'ru' ? 'Луна' : 'Moon',
      sign: moon.sign,
      signEmoji: moon.emoji,
      degree: moon.position.toFixed(1),
      meaning: PLANET_MEANINGS.Moon[locale],
      retrograde: moon.retrograde,
      house: moon.house,
    });
  }

  // Ascendant card
  if (ascendant !== null) {
    const ascSignIndex = Math.floor(((ascendant % 360) + 360) % 360 / 30);
    const ascSigns = [
      'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
    ];
    const ascEmojis = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];
    const ascSign = ascSigns[ascSignIndex] ?? 'Aries';
    const ascEmoji = ascEmojis[ascSignIndex] ?? '♈';
    const ascDegree = (ascendant % 30).toFixed(1);

    cards.push({
      glyph: '↑',
      name: t.asc,
      sign: ascSign,
      signEmoji: ascEmoji,
      degree: ascDegree,
      meaning: ASC_MEANING[locale],
      retrograde: false,
      house: 1,
    });
  }

  return (
    <div className="w-full">
      {/* Cards row */}
      <div className="flex flex-wrap gap-4 justify-center">
        {cards.map((card, i) => (
          <PlanetCard key={card.name} card={card} locale={locale} delay={i * 0.12} />
        ))}

        {ascendant === null && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.24 }}
            className="flex flex-col items-center justify-center text-center rounded-2xl p-6"
            style={{
              background: 'rgba(11,11,31,0.4)',
              border: '1px dashed rgba(212,175,55,0.2)',
              minWidth: '140px',
              flex: '1 1 140px',
            }}
          >
            <div className="text-3xl mb-2" style={{ color: 'rgba(212,175,55,0.3)' }}>↑</div>
            <div
              className="text-[10px] tracking-widest uppercase mb-2"
              style={{ color: 'rgba(212,175,55,0.4)', letterSpacing: '0.22em' }}
            >
              {t.asc}
            </div>
            <p className="font-serif text-xs italic" style={{ color: 'rgba(201,194,224,0.4)' }}>
              {t.unknown_time}
            </p>
          </motion.div>
        )}
      </div>

      {/* Upgrade CTA for free users */}
      {!isPremium && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-6 flex flex-col items-center gap-3 text-center"
        >
          <p className="text-sm font-serif" style={{ color: 'rgba(201,194,224,0.55)' }}>
            {t.upgrade}
          </p>
          <a
            href="/pricing"
            className="px-6 py-2.5 rounded-full text-xs tracking-widest uppercase"
            style={{
              background: 'linear-gradient(135deg, rgba(212,175,55,0.2), rgba(212,175,55,0.05))',
              border: '1px solid #d4af37',
              color: '#d4af37',
              letterSpacing: '0.18em',
            }}
          >
            ✦ {t.upgrade_cta}
          </a>
        </motion.div>
      )}
    </div>
  );
}
