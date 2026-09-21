'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError, checkinRitual, getRitual, localToday, type RitualState } from './api';
import { getAccessToken } from './auth';

/**
 * The daily ritual behind the streak pill and the week grid.
 *
 * Signed-in people (everyone arriving from the Telegram Mini App) keep it on
 * the server, so it follows them across devices. An anonymous visitor has no
 * account to attach it to, so theirs lives in localStorage — the screen looks
 * the same either way.
 */

const STORAGE_KEY = 'tarot.ritual.days';

function readLocalDays(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((d) => typeof d === 'string') : [];
  } catch {
    return [];
  }
}

function writeLocalDays(days: string[]) {
  try {
    // A year is more than any streak worth showing.
    localStorage.setItem(STORAGE_KEY, JSON.stringify(days.slice(-400)));
  } catch { /* private mode / storage blocked — the ritual just won't persist */ }
}

function shift(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number);
  return localToday(new Date(y, m - 1, d + days));
}

/** Same shape the server returns, computed from a set of done days. */
export function computeRitual(done: Set<string>, today: string): RitualState {
  let cursor = done.has(today) ? today : shift(today, -1);
  let streak = 0;
  while (done.has(cursor)) {
    streak += 1;
    cursor = shift(cursor, -1);
  }
  const [y, m, d] = today.split('-').map(Number);
  const weekday = (new Date(y, m - 1, d).getDay() + 6) % 7; // 0 = Monday
  const monday = shift(today, -weekday);
  const week = Array.from({ length: 7 }, (_, i) => {
    const date = shift(monday, i);
    return {
      date,
      weekday: i,
      done: done.has(date),
      is_today: date === today,
      is_future: date > today,
    };
  });
  return { today, done_today: done.has(today), streak, week };
}

export function useRitual() {
  const [state, setState] = useState<RitualState>(() =>
    computeRitual(new Set(), localToday()));
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    const today = localToday();
    if (getAccessToken()) {
      setSignedIn(true);
      getRitual(today)
        .then(setState)
        .catch((err) => {
          // A stale token is not worth an error on the home screen — fall back
          // to the local copy rather than showing an empty grid.
          if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
            setSignedIn(false);
            setState(computeRitual(new Set(readLocalDays()), today));
          }
        });
    } else {
      setState(computeRitual(new Set(readLocalDays()), today));
    }
  }, []);

  /** Mark today as done. Called when the card of the day is opened. */
  const checkIn = useCallback(async () => {
    const today = localToday();
    if (signedIn) {
      try {
        setState(await checkinRitual(today));
        return;
      } catch { /* fall through to the local copy */ }
    }
    const days = readLocalDays();
    if (!days.includes(today)) days.push(today);
    writeLocalDays(days);
    setState(computeRitual(new Set(days), today));
  }, [signedIn]);

  return { ritual: state, checkIn };
}
