import type {
  BillingMe,
  CheckoutPayload,
  Interpretation,
  NatalChart,
  NatalInterpretation,
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
  return request<NatalChart>('/api/v1/natal/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getNatalChart(id: number | string): Promise<NatalChart> {
  return request<NatalChart>(`/api/v1/natal/${id}/`);
}

export async function interpretNatalChart(id: number | string): Promise<NatalInterpretation> {
  return request<NatalInterpretation>(`/api/v1/natal/${id}/interpret/`, {
    method: 'POST',
    body: JSON.stringify({}),
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
