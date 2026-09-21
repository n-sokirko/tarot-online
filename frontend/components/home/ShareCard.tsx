'use client';

import { useState } from 'react';
import type { DailyCardResponse } from '@/lib/api';
import { dateLine } from '@/lib/moon';

/**
 * The card of the day as something worth posting — the design's viral loop.
 * "Сохранить" renders a 1080×1920 story image on a canvas and downloads it;
 * "В сторис" hands the same image to the system share sheet (from there it goes
 * to Telegram or Instagram stories), falling back to a download where the
 * browser cannot share files.
 *
 * Card art is served from this origin (/cards/…), so the canvas stays untainted
 * and can be exported.
 */

interface ShareCardProps {
  locale: 'ru' | 'en';
  daily: DailyCardResponse | null;
  opened: boolean;
}

function firstSentence(text: string): string {
  const m = text.replace(/\s+/g, ' ').trim().match(/^(.{20,150}?[.!?…])(\s|$)/);
  return m ? m[1] : text.slice(0, 140);
}

/** next/font hashes family names, so read the real one off a rendered element. */
function fontFamilyOf(className: string): string {
  const probe = document.createElement('span');
  probe.className = className;
  probe.style.position = 'absolute';
  probe.style.visibility = 'hidden';
  document.body.appendChild(probe);
  const family = getComputedStyle(probe).fontFamily;
  probe.remove();
  return family;
}

function wrap(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(' ');
  const lines: string[] = [];
  let line = '';
  for (const w of words) {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = w;
    } else {
      line = test;
    }
  }
  if (line) lines.push(line);
  return lines;
}

async function renderStory(
  locale: 'ru' | 'en',
  daily: DailyCardResponse,
  name: string,
  orientation: string,
  quote: string,
): Promise<Blob> {
  await document.fonts.ready;
  const serif = fontFamilyOf('font-serif');
  const sans = fontFamilyOf('font-sans');
  const mono = fontFamilyOf('font-mono');

  const W = 1080;
  const H = 1920;
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d')!;

  // Background: the home screen's glows over obsidian.
  ctx.fillStyle = '#0B0A0F';
  ctx.fillRect(0, 0, W, H);
  for (const [x, y, r, color] of [
    [W * 0.84, -120, 1100, 'rgba(182,167,240,0.20)'],
    [0, H * 0.18, 900, 'rgba(224,178,108,0.12)'],
  ] as const) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, color);
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
  }

  ctx.textAlign = 'center';
  ctx.fillStyle = '#8E879B';
  ctx.font = `500 30px ${mono}`;
  ctx.fillText(
    `${locale === 'ru' ? 'КАРТА ДНЯ' : 'CARD OF THE DAY'} · ${dateLine(locale).toUpperCase()}`,
    W / 2, 230,
  );

  // The card.
  const cw = 560;
  const ch = cw * 1.5;
  const cx = (W - cw) / 2;
  const cy = 330;
  const img = new Image();
  img.src = daily.card.image_url;
  await img.decode().catch(() => undefined);
  ctx.save();
  ctx.beginPath();
  ctx.roundRect(cx, cy, cw, ch, 36);
  ctx.clip();
  ctx.fillStyle = '#1E1830';
  ctx.fillRect(cx, cy, cw, ch);
  if (img.complete && img.naturalWidth) {
    if (daily.is_reversed) {
      ctx.translate(cx + cw / 2, cy + ch / 2);
      ctx.rotate(Math.PI);
      ctx.drawImage(img, -cw / 2, -ch / 2, cw, ch);
    } else {
      ctx.drawImage(img, cx, cy, cw, ch);
    }
  }
  ctx.restore();
  ctx.strokeStyle = '#E0B26C';
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.roundRect(cx, cy, cw, ch, 36);
  ctx.stroke();

  ctx.fillStyle = '#F2EDE4';
  ctx.font = `76px ${serif}`;
  ctx.fillText(name, W / 2, cy + ch + 130);
  ctx.fillStyle = '#E0B26C';
  ctx.font = `500 30px ${mono}`;
  ctx.fillText(orientation.toUpperCase(), W / 2, cy + ch + 190);

  ctx.fillStyle = '#A49DAF';
  ctx.font = `40px ${sans}`;
  const lines = wrap(ctx, `«${quote}»`, W - 200);
  lines.slice(0, 4).forEach((l, i) => ctx.fillText(l, W / 2, cy + ch + 290 + i * 58));

  ctx.fillStyle = '#7E7890';
  ctx.font = `500 30px ${mono}`;
  ctx.fillText('sokirdon.com · @tarott_online_bot', W / 2, H - 110);

  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('export failed'))), 'image/png'));
}

export default function ShareCard({ locale, daily, opened }: ShareCardProps) {
  const [busy, setBusy] = useState<'story' | 'save' | null>(null);
  const [hover, setHover] = useState(false);

  if (!daily || !opened) return null;

  const card = daily.card;
  const name = locale === 'ru' ? card.name_ru : card.name_en;
  const orientation = daily.is_reversed
    ? (locale === 'ru' ? 'перевёрнутая' : 'reversed')
    : (locale === 'ru' ? 'прямая' : 'upright');
  const meaning = daily.is_reversed
    ? (locale === 'ru' ? card.reversed_meaning_ru : card.reversed_meaning_en)
    : (locale === 'ru' ? card.upright_meaning_ru : card.upright_meaning_en);
  const quote = firstSentence(meaning || '');
  const fileName = `karta-dnya-${daily.date}.png`;

  const download = (blob: Blob) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  };

  const run = async (kind: 'story' | 'save') => {
    setBusy(kind);
    try {
      const blob = await renderStory(locale, daily, name, orientation, quote);
      const file = new File([blob], fileName, { type: 'image/png' });
      if (kind === 'story' && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: name });
      } else {
        download(blob);
      }
    } catch {
      /* the person closed the share sheet, or export failed — nothing to undo */
    } finally {
      setBusy(null);
    }
  };

  return (
    <section style={{ padding: '26px 18px 0', perspective: 1000 }}>
      <div
        onPointerEnter={() => setHover(true)}
        onPointerLeave={() => setHover(false)}
        style={{
          borderRadius: 20,
          border: '1px solid rgba(224,178,108,.32)',
          background: 'linear-gradient(160deg,#1B1528,#0C0A11)',
          padding: 20,
          transition: 'transform var(--dur) var(--ease)',
          transform: hover ? 'rotateX(6deg) translateZ(calc(18px * var(--depth)))' : 'none',
        }}
      >
        <div className="flex" style={{ gap: 14 }}>
          <div
            className="relative shrink-0 overflow-hidden"
            style={{ width: 62, aspectRatio: '2 / 3', borderRadius: 9, border: '1px solid var(--accent)' }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={card.image_url}
              alt=""
              className="absolute inset-0 w-full h-full object-cover"
              style={{ transform: daily.is_reversed ? 'rotate(180deg)' : undefined }}
            />
          </div>
          <div className="min-w-0">
            <p className="font-serif" style={{ fontSize: 19 }}>{name}, {orientation}</p>
            <p style={{ fontSize: 13, lineHeight: 1.5, color: '#A49DAF', marginTop: 6 }}>«{quote}»</p>
          </div>
        </div>
        <div className="grid grid-cols-2" style={{ gap: 10, marginTop: 16 }}>
          <button
            type="button"
            onClick={() => run('story')}
            disabled={busy !== null}
            style={{
              background: 'var(--accent)',
              color: '#0B0A0F',
              fontWeight: 700,
              fontSize: 14,
              borderRadius: 999,
              minHeight: 44,
            }}
          >
            {busy === 'story' ? '…' : locale === 'ru' ? 'В сторис' : 'To stories'}
          </button>
          <button
            type="button"
            onClick={() => run('save')}
            disabled={busy !== null}
            className="transition-colors hover:border-[var(--accent)] hover:text-[var(--accent)]"
            style={{
              border: '1px solid rgba(255,255,255,.16)',
              fontSize: 14,
              borderRadius: 999,
              minHeight: 44,
            }}
          >
            {busy === 'save' ? '…' : locale === 'ru' ? 'Сохранить' : 'Save'}
          </button>
        </div>
      </div>
    </section>
  );
}
