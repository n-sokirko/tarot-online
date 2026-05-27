'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { createRuneCast } from '@/lib/api';
import type { RuneLayout } from '@/lib/types';

const LOCALE = 'ru' as const;

const t = {
  ru: {
    title: 'Бросок рун',
    subtitle: 'Старший Футарк. 24 знака, каждый — слово древнее любого языка.',
    question_placeholder: 'Что хочешь спросить у рун? (можно оставить пустым)',
    layouts: {
      single: { title: 'Одна руна', desc: 'Знак на день' },
      three: { title: 'Три руны', desc: 'Что есть · Что нужно · Куда смотреть' },
      five: { title: 'Пятиричный крест', desc: 'Глубокий разбор' },
    },
    cast: 'Бросить',
    casting: 'Достаём руны...',
    free: 'Бесплатно',
    premium: 'Premium',
  },
  en: {
    title: 'Cast the runes',
    subtitle: 'Elder Futhark. 24 marks, each a word older than any language.',
    question_placeholder: 'What do you want to ask the runes? (optional)',
    layouts: {
      single: { title: 'Single rune', desc: 'A sign for the day' },
      three: { title: 'Three runes', desc: 'What is · What is needed · Where to look' },
      five: { title: 'Five-rune cross', desc: 'Deep cast' },
    },
    cast: 'Cast',
    casting: 'Drawing the runes...',
    free: 'Free',
    premium: 'Premium',
  },
}[LOCALE];

const LAYOUTS: { id: RuneLayout; tier: 'free' | 'premium' }[] = [
  { id: 'single', tier: 'free' },
  { id: 'three', tier: 'free' },
  { id: 'five', tier: 'premium' },
];

export default function RunesPage() {
  const router = useRouter();
  const [selected, setSelected] = useState<RuneLayout>('three');
  const [question, setQuestion] = useState('');
  const [casting, setCasting] = useState(false);

  const handleCast = async () => {
    setCasting(true);
    try {
      const cast = await createRuneCast(selected, LOCALE, question.trim());
      router.push(`/runes/cast/${cast.id}`);
    } catch {
      setCasting(false);
    }
  };

  return (
    <main
      className="min-h-screen px-4 py-12 md:py-16"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}
    >
      <div className="max-w-3xl mx-auto">
        <motion.header
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <h1
            className="font-serif text-3xl md:text-4xl mb-3"
            style={{ color: '#d4af37', letterSpacing: '0.08em' }}
          >
            ᛟ {t.title}
          </h1>
          <p className="font-serif text-sm md:text-base max-w-xl mx-auto" style={{ color: 'rgba(201,194,224,0.7)' }}>
            {t.subtitle}
          </p>
        </motion.header>

        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={t.question_placeholder}
          className="w-full font-serif text-sm md:text-base p-4 rounded-2xl resize-none mb-8 outline-none"
          rows={3}
          style={{
            background: 'rgba(11,11,31,0.6)',
            border: '1px solid rgba(212,175,55,0.18)',
            color: 'rgba(201,194,224,0.95)',
          }}
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
          {LAYOUTS.map(({ id, tier }) => {
            const layoutT = t.layouts[id];
            const isSelected = selected === id;
            return (
              <button
                key={id}
                onClick={() => setSelected(id)}
                className="text-left rounded-2xl p-5 transition-all"
                style={{
                  background: isSelected
                    ? 'linear-gradient(180deg, rgba(212,175,55,0.12), rgba(28,24,64,0.4))'
                    : 'linear-gradient(180deg, rgba(28,24,64,0.6), rgba(11,11,31,0.6))',
                  border: `1px solid ${isSelected ? '#d4af37' : 'rgba(212,175,55,0.18)'}`,
                  boxShadow: isSelected ? '0 0 24px rgba(212,175,55,0.15)' : 'none',
                }}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-serif text-base" style={{ color: '#d4af37' }}>
                    {layoutT.title}
                  </h3>
                  <span
                    className="text-[9px] tracking-widest uppercase px-2 py-0.5 rounded-full"
                    style={{
                      background: tier === 'premium' ? 'rgba(212,175,55,0.15)' : 'rgba(201,194,224,0.08)',
                      color: tier === 'premium' ? '#d4af37' : 'rgba(201,194,224,0.55)',
                      letterSpacing: '0.18em',
                      border: tier === 'premium' ? '1px solid rgba(212,175,55,0.35)' : '1px solid transparent',
                    }}
                  >
                    {tier === 'premium' ? t.premium : t.free}
                  </span>
                </div>
                <p className="font-serif text-xs" style={{ color: 'rgba(201,194,224,0.7)' }}>
                  {layoutT.desc}
                </p>
              </button>
            );
          })}
        </div>

        <div className="flex justify-center">
          <motion.button
            onClick={handleCast}
            disabled={casting}
            whileHover={!casting ? { scale: 1.03 } : undefined}
            whileTap={!casting ? { scale: 0.97 } : undefined}
            className="px-10 py-3 rounded-full text-xs tracking-widest uppercase"
            style={{
              background: 'linear-gradient(135deg, rgba(212,175,55,0.25), rgba(212,175,55,0.05))',
              border: '1px solid #d4af37',
              color: '#d4af37',
              letterSpacing: '0.22em',
              boxShadow: '0 0 24px rgba(212,175,55,0.15)',
              opacity: casting ? 0.5 : 1,
            }}
          >
            {casting ? t.casting : `ᛉ ${t.cast}`}
          </motion.button>
        </div>
      </div>
    </main>
  );
}
