'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ApiError,
  forgetTarologist,
  getTarologist,
  updateTarologist,
  type PersonaKey,
  type PersonaMeta,
  type TarologistSettings as Settings,
} from '@/lib/api';
import { getAccessToken } from '@/lib/auth';

/** One line in each voice, on the same reading, so the choice is felt, not read about. */
const SAMPLE: Record<'ru' | 'en', Record<PersonaKey, string>> = {
  ru: {
    classic: 'Скорее нет: Луна в прошлом говорит о тумане, а Пятёрка Кубков — о том, что он сейчас занят своей потерей.',
    mira: 'Анечка, снова про Диму, и я понимаю почему. Звезда впереди — это момент, когда тебе станет спокойно, напишет он или нет.',
    val: 'Так. Опять Дима. Луна, наша карта-сталкер, третий раз за месяц. Ждать у телефона? Нет.',
    val18: 'Так, блять, опять Дима. Луна, сука, третий раз за месяц — это уже преследование. Звезда — охуенная карта, и она про тебя.',
    agata: 'Луна легла в прошлое: та дорога шла по отражениям. Звезда восходит впереди, и вода снова станет прозрачной.',
  },
  en: {
    classic: 'Probably not: the Moon in the past speaks of fog, and the Five of Cups says he is busy with his own loss.',
    mira: 'Anna, Dima again, and I get why. The Star ahead is the moment you feel calm, whether he texts or not.',
    val: 'Right. Dima again. The Moon, our stalker card, third time this month. Wait by the phone? No.',
    val18: 'Damn it, Dima again. The Moon, third bloody time this month. The Star is a fucking great card, and it is about you.',
    agata: 'The Moon lay in the past: that road ran over reflections. The Star rises ahead, and the water will clear.',
  },
};

/** Free users see Val 18+ bleeped: the teaser that sells the uncensored voice. */
function bleep(s: string) {
  return s.replace(/(блять|сука|охуенная|bloody|fucking|damn)/gi, (w) => w[0] + '*'.repeat(w.length - 1));
}

const L = {
  ru: {
    title: 'Мой таролог',
    lead: 'Выбери, кто будет делать тебе расклады. Таролог помнит прошлые расклады и подстраивается под тебя.',
    login: 'Войди, чтобы таролог запоминал тебя.',
    premium: 'Premium',
    openPremium: 'Открыть в Premium',
    adultTitle: 'Режим 18+ без цензуры',
    adultText: 'Вэл будет материться в раскладах. Подтверди, что тебе есть 18 лет.',
    adultYes: 'Мне есть 18, включить',
    cancel: 'Отмена',
    mirror: 'Подстраиваться под мою манеру письма',
    mirrorHint: 'Пишешь с эмодзи и строчными — ответ будет таким же.',
    remember: 'Помнить мои расклады',
    rememberHint: 'Таролог вспомнит прошлые расклады, если они связаны с вопросом.',
    dossier: 'Что таролог знает обо мне',
    dossierEmpty: 'Пока пусто. Таролог дополнит досье сам после следующих раскладов.',
    dossierPremium: 'Досье ведётся в Premium.',
    forget: 'Стереть всё',
    forgetConfirm: 'Стереть досье и память о прошлых раскладах? Сами расклады останутся.',
    error: 'Не получилось сохранить. Попробуй ещё раз.',
  },
  en: {
    title: 'My tarot reader',
    lead: 'Choose who reads for you. Your reader remembers past readings and adapts to you.',
    login: 'Sign in so your reader can remember you.',
    premium: 'Premium',
    openPremium: 'Unlock with Premium',
    adultTitle: 'Uncensored 18+ mode',
    adultText: 'Val will swear in readings. Confirm you are 18 or older.',
    adultYes: "I'm 18+, turn it on",
    cancel: 'Cancel',
    mirror: 'Match my writing style',
    mirrorHint: 'Write with emoji and lowercase — the answer will too.',
    remember: 'Remember my readings',
    rememberHint: 'Your reader recalls past readings when they relate to the question.',
    dossier: 'What my reader knows about me',
    dossierEmpty: 'Empty for now. Your reader fills it in after your next readings.',
    dossierPremium: 'The dossier is kept with Premium.',
    forget: 'Erase everything',
    forgetConfirm: 'Erase the dossier and the memory of past readings? The readings themselves stay.',
    error: "Couldn't save. Try again.",
  },
} as const;

const card = (active: boolean): React.CSSProperties => ({
  background: active ? 'rgba(224,178,108,0.1)' : 'rgba(224,178,108,0.03)',
  border: `1px solid ${active ? 'var(--accent)' : 'rgba(224,178,108,0.15)'}`,
});

function Toggle({ on, label, hint, locked, onChange }: {
  on: boolean; label: string; hint: string; locked?: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className="flex items-start gap-3 p-4 rounded-2xl text-left w-full"
      style={card(on)}
    >
      <span className="flex flex-col gap-1 min-w-0 flex-1">
        <span className="font-sans text-sm" style={{ color: 'rgba(242,237,228,0.9)' }}>
          {label} {locked && <span style={{ color: 'var(--accent)', fontSize: 11 }}>· Premium</span>}
        </span>
        <span className="font-sans text-xs" style={{ color: 'rgba(242,237,228,0.4)' }}>{hint}</span>
      </span>
      <span
        aria-hidden
        className="flex-shrink-0 rounded-full relative"
        style={{ width: 40, height: 24, marginTop: 2, background: on ? 'var(--accent)' : 'rgba(255,255,255,0.12)', transition: 'background .2s' }}
      >
        <span
          className="absolute rounded-full"
          style={{ width: 18, height: 18, top: 3, left: on ? 19 : 3, background: on ? '#0B0A0F' : 'rgba(242,237,228,0.7)', transition: 'left .2s' }}
        />
      </span>
    </button>
  );
}

export default function TarologistSettings({ locale }: { locale: 'ru' | 'en' }) {
  const t = L[locale];
  const [data, setData] = useState<Settings | null>(null);
  const [signedIn, setSignedIn] = useState(true);
  const [askAdult, setAskAdult] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needPremium, setNeedPremium] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) { setSignedIn(false); return; }
    getTarologist().then(setData).catch(() => setSignedIn(false));
  }, []);

  const save = useCallback(async (patch: Parameters<typeof updateTarologist>[0]) => {
    setError(null);
    setNeedPremium(false);
    try {
      setData(await updateTarologist(patch));
      return true;
    } catch (e) {
      if (e instanceof ApiError && e.status === 402) setNeedPremium(true);
      else setError(t.error);
      return false;
    }
  }, [t.error]);

  const pick = (p: PersonaMeta) => {
    if (!data) return;
    if (p.premium && !data.premium) { setNeedPremium(true); return; }
    if (p.adult && !data.adult_confirmed) { setAskAdult(true); return; }
    void save({ persona: p.key });
  };

  const removeFact = (i: number) => {
    if (!data) return;
    void save({ dossier: data.dossier.filter((_, j) => j !== i) });
  };

  const forget = async () => {
    if (!window.confirm(t.forgetConfirm)) return;
    try { setData(await forgetTarologist()); } catch { setError(t.error); }
  };

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-sans text-xs uppercase tracking-widest" style={{ color: 'rgba(242,237,228,0.45)', letterSpacing: '0.22em' }}>
        {t.title}
      </h2>
      <p className="font-sans text-sm" style={{ color: 'rgba(242,237,228,0.55)', lineHeight: 1.5 }}>{t.lead}</p>

      {!signedIn && <p className="font-sans text-sm" style={{ color: 'var(--accent)' }}>{t.login}</p>}

      {data && (
        <>
          <div className="flex flex-col gap-2">
            {data.personas.map((p) => {
              const active = data.persona === p.key;
              const locked = p.premium && !data.premium;
              const sample = SAMPLE[locale][p.key];
              const shown = p.adult && (locked || !data.adult_confirmed) ? bleep(sample) : sample;
              return (
                <button
                  key={p.key}
                  type="button"
                  onClick={() => pick(p)}
                  className="flex flex-col gap-1.5 p-4 rounded-2xl text-left"
                  style={card(active)}
                  aria-pressed={active}
                >
                  <span className="flex items-baseline gap-2 w-full">
                    <span className="font-serif text-base" style={{ color: active ? 'var(--accent)' : 'rgba(242,237,228,0.9)' }}>
                      {locale === 'ru' ? p.name_ru : p.name_en}
                    </span>
                    <span className="font-sans text-xs" style={{ color: 'rgba(242,237,228,0.4)' }}>
                      {locale === 'ru' ? p.tagline_ru : p.tagline_en}
                    </span>
                    <span className="ml-auto font-sans text-[11px] flex-shrink-0" style={{ color: 'var(--accent)' }}>
                      {active ? '✓' : locked ? `🔒 ${t.premium}` : ''}
                    </span>
                  </span>
                  <span className="font-serif text-[13px] italic" style={{ color: 'rgba(242,237,228,0.6)', lineHeight: 1.5 }}>
                    «{shown}»
                  </span>
                </button>
              );
            })}
          </div>

          {needPremium && (
            <Link
              href="/pricing"
              className="text-center font-sans text-sm font-semibold rounded-full"
              style={{ background: 'var(--accent)', color: '#0B0A0F', padding: '12px 18px' }}
            >
              {t.openPremium}
            </Link>
          )}

          {askAdult && (
            <div className="p-4 rounded-2xl flex flex-col gap-3" style={{ border: '1px solid var(--accent)', background: 'rgba(224,178,108,0.06)' }}>
              <p className="font-serif text-base" style={{ color: 'var(--accent)' }}>{t.adultTitle}</p>
              <p className="font-sans text-sm" style={{ color: 'rgba(242,237,228,0.7)' }}>{t.adultText}</p>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="flex-1 rounded-full font-sans text-sm font-semibold"
                  style={{ background: 'var(--accent)', color: '#0B0A0F', padding: '11px 14px' }}
                  onClick={async () => { if (await save({ persona: 'val18', adult_confirm: true })) setAskAdult(false); }}
                >
                  {t.adultYes}
                </button>
                <button
                  type="button"
                  className="rounded-full font-sans text-sm"
                  style={{ border: '1px solid rgba(255,255,255,0.15)', color: 'rgba(242,237,228,0.6)', padding: '11px 14px' }}
                  onClick={() => setAskAdult(false)}
                >
                  {t.cancel}
                </button>
              </div>
            </div>
          )}

          <Toggle
            on={data.mirror_style}
            label={t.mirror}
            hint={t.mirrorHint}
            locked={!data.premium}
            onChange={(v) => { if (v && !data.premium) { setNeedPremium(true); return; } void save({ mirror_style: v }); }}
          />
          <Toggle on={data.remember} label={t.remember} hint={t.rememberHint} onChange={(v) => void save({ remember: v })} />

          <div className="p-4 rounded-2xl flex flex-col gap-1" style={card(false)}>
            <p className="font-serif text-base" style={{ color: 'rgba(242,237,228,0.9)' }}>{t.dossier}</p>
            {!data.premium && <p className="font-sans text-xs" style={{ color: 'var(--accent)' }}>{t.dossierPremium}</p>}
            {data.premium && data.dossier.length === 0 && (
              <p className="font-sans text-xs" style={{ color: 'rgba(242,237,228,0.4)' }}>{t.dossierEmpty}</p>
            )}
            {data.dossier.map((fact, i) => (
              <div key={`${i}-${fact}`} className="flex items-start gap-3 py-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span className="font-sans text-sm flex-1" style={{ color: 'rgba(242,237,228,0.8)', lineHeight: 1.5 }}>{fact}</span>
                <button
                  type="button"
                  aria-label={locale === 'ru' ? 'Удалить' : 'Remove'}
                  onClick={() => removeFact(i)}
                  className="flex-shrink-0 text-base"
                  style={{ color: 'rgba(242,237,228,0.35)', minWidth: 28, minHeight: 28 }}
                >
                  ×
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={forget}
              className="self-start mt-2 font-sans text-xs underline"
              style={{ color: 'rgba(242,237,228,0.45)' }}
            >
              {t.forget}
            </button>
          </div>
        </>
      )}

      {error && <p role="alert" className="font-sans text-sm" style={{ color: '#E7A48B' }}>{error}</p>}
    </section>
  );
}
