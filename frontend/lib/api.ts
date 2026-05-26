import type { ReadingResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function createReading(locale: string): Promise<ReadingResponse> {
  const res = await fetch(`${API_BASE}/api/v1/readings/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: '', locale, spread_slug: 'three-card' }),
  });
  if (!res.ok) throw new Error('Failed to create reading');
  return res.json() as Promise<ReadingResponse>;
}
