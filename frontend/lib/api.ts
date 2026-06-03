import type {
  BillingMe,
  CheckoutPayload,
  Interpretation,
  NatalChart,
  NatalInterpretation,
  NumerologyReading,
  NumerologyInterpretation,
  DailyHoroscope,
  HoroscopeAIReading,
  ZodiacSign,
  PlansResponse,
  ReadingResponse,
  Rune,
  RuneCastResponse,
  RuneLayout,
  TelegramCheckoutPayload,
  TelegramInvoicePayload,
} from './types';
import { getAuthHeader } from './auth';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public status: number, public payload: unknown) {
    super(`API error ${status}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    let payload: unknown = null;
    try { payload = await res.json(); } catch { /* not JSON */ }
    throw new ApiError(res.status, payload);
  }
  return res.json() as Promise<T>;
}

// ---- Daily Card ----

export interface DailyCardResponse {
  date: string;
  card: import('./types').TarotCard;
  is_reversed: boolean;
}

export async function getDailyCard(): Promise<DailyCardResponse> {
  return request<DailyCardResponse>('/api/v1/cards/daily/');
}

// ---- Tarot readings ----

export async function createReading(
  locale: string,
  spreadSlug: string = 'three-card',
  question: string = '',
): Promise<ReadingResponse> {
  return request<ReadingResponse>('/api/v1/readings/', {
    method: 'POST',
    body: JSON.stringify({ question, locale, spread_slug: spreadSlug }),
  });
}

export async function getReading(id: number | string): Promise<ReadingResponse> {
  return request<ReadingResponse>(`/api/v1/readings/${id}/`);
}

export async function interpretReading(id: number | string, question?: string): Promise<Interpretation> {
  return request<Interpretation>(`/api/v1/readings/${id}/interpret/`, {
    method: 'POST',
    body: JSON.stringify({ question: question ?? '' }),
  });
}

/**
 * Live (SSE) interpretation — streams the AI text token-by-token.
 * Calls onDelta for each chunk, onDone with the final Interpretation.
 * Throws ApiError on non-2xx (402/429/400) before the stream starts.
 */
export async function interpretReadingStream(
  id: number | string,
  question: string,
  handlers: {
    onDelta: (text: string) => void;
    onDone: (interp: Interpretation) => void;
    onError: (detail: string) => void;
  },
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/readings/${id}/interpret-stream/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify({ question }),
  });
  if (!res.ok || !res.body) {
    let payload: unknown = null;
    try { payload = await res.json(); } catch { /* not JSON */ }
    throw new ApiError(res.status, payload);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep: number;
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, sep).trim();
      buffer = buffer.slice(sep + 2);
      if (!rawEvent.startsWith('data:')) continue;
      try {
        const evt = JSON.parse(rawEvent.slice(5).trim());
        if (evt.type === 'delta') handlers.onDelta(evt.text);
        else if (evt.type === 'done') handlers.onDone(evt.interpretation);
        else if (evt.type === 'error') handlers.onError(evt.detail ?? 'error');
      } catch { /* ignore partial */ }
    }
  }
}

// ---- Runes ----

export async function listRunes(): Promise<{ runes: Rune[] }> {
  return request<{ runes: Rune[] }>('/api/v1/runes/');
}

export async function createRuneCast(
  layout: RuneLayout,
  locale: string,
  question: string = '',
): Promise<RuneCastResponse> {
  return request<RuneCastResponse>('/api/v1/runes/casts/', {
    method: 'POST',
    body: JSON.stringify({ layout, locale, question }),
  });
}

export async function getRuneCast(id: number | string): Promise<RuneCastResponse> {
  return request<RuneCastResponse>(`/api/v1/runes/casts/${id}/`);
}

export async function interpretRuneCast(id: number | string, question?: string): Promise<Interpretation> {
  return request<Interpretation>(`/api/v1/runes/casts/${id}/interpret/`, {
    method: 'POST',
    body: JSON.stringify({ question: question ?? '' }),
  });
}

// ---- Natal Chart ----

export async function createNatalChart(data: {
  birth_name: string;
  birth_date: string;
  birth_time?: string;
  birth_city: string;
  locale: string;
}): Promise<NatalChart> {
  return request<NatalChart>('/api/v1/natal/charts/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getNatalChart(id: number | string): Promise<NatalChart> {
  return request<NatalChart>(`/api/v1/natal/charts/${id}/`);
}

export async function interpretNatalChart(id: number | string): Promise<NatalInterpretation> {
  return request<NatalInterpretation>(`/api/v1/natal/charts/${id}/interpret/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

// ---- Numerology ----

export async function createNumerologyReading(data: {
  full_name: string;
  birth_date: string;
  locale: string;
}): Promise<NumerologyReading> {
  return request<NumerologyReading>('/api/v1/numerology/readings/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function interpretNumerology(id: number | string): Promise<NumerologyInterpretation> {
  return request<NumerologyInterpretation>(`/api/v1/numerology/readings/${id}/interpret/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

// ---- Horoscope ----

export async function listZodiacSigns(locale: string): Promise<{ signs: ZodiacSign[] }> {
  return request<{ signs: ZodiacSign[] }>(`/api/v1/horoscope/signs/?locale=${locale}`);
}

export async function getDailyHoroscope(sign: string, locale: string): Promise<DailyHoroscope> {
  return request<DailyHoroscope>(`/api/v1/horoscope/${sign}/?locale=${locale}`);
}

export async function interpretHoroscope(sign: string, locale: string): Promise<HoroscopeAIReading> {
  return request<HoroscopeAIReading>(`/api/v1/horoscope/${sign}/interpret/`, {
    method: 'POST',
    body: JSON.stringify({ locale }),
  });
}

// ---- Billing ----

export async function listPlans(): Promise<PlansResponse> {
  return request<PlansResponse>('/api/v1/billing/plans/');
}

export async function getBillingMe(): Promise<BillingMe> {
  return request<BillingMe>('/api/v1/billing/me/');
}

export async function startCheckout(planSlug: string): Promise<CheckoutPayload> {
  return request<CheckoutPayload>('/api/v1/billing/checkout/', {
    method: 'POST',
    body: JSON.stringify({ plan_slug: planSlug }),
  });
}

export async function startTelegramCheckout(planSlug: string): Promise<TelegramCheckoutPayload> {
  return request<TelegramCheckoutPayload>('/api/v1/billing/checkout/telegram/', {
    method: 'POST',
    body: JSON.stringify({ plan_slug: planSlug }),
  });
}

export async function startTelegramInvoice(planSlug: string): Promise<TelegramInvoicePayload> {
  return request<TelegramInvoicePayload>('/api/v1/billing/checkout/telegram-invoice/', {
    method: 'POST',
    body: JSON.stringify({ plan_slug: planSlug }),
  });
}

export interface TelegramDonationPayload {
  invoice_link: string;
  stars: number;
}

export async function startTelegramDonation(stars: number): Promise<TelegramDonationPayload> {
  return request<TelegramDonationPayload>('/api/v1/billing/donate/telegram-invoice/', {
    method: 'POST',
    body: JSON.stringify({ stars }),
  });
}
