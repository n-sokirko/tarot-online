/**
 * Telegram Mini App haptics. Inside Telegram the phone gives a short tick on
 * a card pick and a "success" buzz on the reveal; in a normal browser these
 * calls do nothing.
 */
type Impact = 'light' | 'medium' | 'heavy' | 'rigid' | 'soft';
type Notice = 'error' | 'success' | 'warning';

interface HapticFeedback {
  impactOccurred?: (style: Impact) => void;
  notificationOccurred?: (type: Notice) => void;
  selectionChanged?: () => void;
}

function haptic(): HapticFeedback | undefined {
  if (typeof window === 'undefined') return undefined;
  return (window as unknown as { Telegram?: { WebApp?: { HapticFeedback?: HapticFeedback } } })
    .Telegram?.WebApp?.HapticFeedback;
}

export function tapImpact(style: Impact = 'light'): void {
  try { haptic()?.impactOccurred?.(style); } catch { /* old Telegram client */ }
}

export function notify(type: Notice = 'success'): void {
  try { haptic()?.notificationOccurred?.(type); } catch { /* old Telegram client */ }
}

export function selectionTick(): void {
  try { haptic()?.selectionChanged?.(); } catch { /* old Telegram client */ }
}
