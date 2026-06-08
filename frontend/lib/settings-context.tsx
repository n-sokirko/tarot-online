'use client';

import { createContext, useContext, useEffect, useState, useCallback } from 'react';

export type FontSize = 'sm' | 'md' | 'lg' | 'xl';
export type AccentColor = 'gold' | 'violet' | 'rose' | 'teal';

export interface AppSettings {
  fontSize: FontSize;
  accentColor: AccentColor;
}

const DEFAULTS: AppSettings = { fontSize: 'md', accentColor: 'gold' };
const STORAGE_KEY = 'tarot_settings';

export const FONT_SCALE: Record<FontSize, number> = {
  sm: 0.875,
  md: 1,
  lg: 1.125,
  xl: 1.25,
};

export const ACCENT_PALETTES: Record<AccentColor, { primary: string; glow: string; label: string }> = {
  gold:   { primary: '#d4af37', glow: '#d4af3766', label: 'Золото' },
  violet: { primary: '#b87de8', glow: '#b87de866', label: 'Аметист' },
  rose:   { primary: '#e87daa', glow: '#e87daa66', label: 'Роза' },
  teal:   { primary: '#5ecfcf', glow: '#5ecfcf66', label: 'Опал' },
};

interface SettingsCtx {
  settings: AppSettings;
  setFontSize: (v: FontSize) => void;
  setAccentColor: (v: AccentColor) => void;
}

const Ctx = createContext<SettingsCtx>({
  settings: DEFAULTS,
  setFontSize: () => {},
  setAccentColor: () => {},
});

function applySettings(s: AppSettings) {
  const root = document.documentElement;
  root.style.setProperty('--font-scale', String(FONT_SCALE[s.fontSize]));
  const p = ACCENT_PALETTES[s.accentColor];
  root.style.setProperty('--accent', p.primary);
  root.style.setProperty('--accent-glow', p.glow);
}

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(DEFAULTS);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = { ...DEFAULTS, ...JSON.parse(raw) } as AppSettings;
        setSettings(parsed);
        applySettings(parsed);
      } else {
        applySettings(DEFAULTS);
      }
    } catch {
      applySettings(DEFAULTS);
    }
  }, []);

  const save = useCallback((next: AppSettings) => {
    setSettings(next);
    applySettings(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }, []);

  return (
    <Ctx.Provider value={{
      settings,
      setFontSize: (fontSize) => save({ ...settings, fontSize }),
      setAccentColor: (accentColor) => save({ ...settings, accentColor }),
    }}>
      {children}
    </Ctx.Provider>
  );
}

export function useSettings() {
  return useContext(Ctx);
}
