'use client';

import { createContext, useContext } from 'react';
import type { RitualState } from './api';
import { computeRitual, useRitual } from './use-ritual';
import { localToday } from './api';

/**
 * One ritual state for the whole app. The streak pill lives in the header and
 * the week grid on the home screen; if each owned its own copy, opening the
 * card of the day would tick the grid while the header kept showing yesterday's
 * streak.
 */

interface RitualContextValue {
  ritual: RitualState;
  checkIn: () => Promise<void>;
}

const RitualContext = createContext<RitualContextValue>({
  ritual: computeRitual(new Set(), localToday()),
  checkIn: async () => {},
});

export function RitualProvider({ children }: { children: React.ReactNode }) {
  const value = useRitual();
  return <RitualContext.Provider value={value}>{children}</RitualContext.Provider>;
}

export function useRitualContext() {
  return useContext(RitualContext);
}
