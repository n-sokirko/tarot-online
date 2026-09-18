'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import CardBack from './CardBack';
import CardFace from './CardFace';
import CardDetailModal from './CardDetailModal';
import { drawOntoTable, saveTableLayout } from '@/lib/api';
import type { DrawnCard } from '@/lib/types';

interface FreeTableProps {
  readingId: number;
  locale: 'ru' | 'en';
  initialCards: DrawnCard[];
  maxCards?: number;
  onCardsChange?: (cards: DrawnCard[]) => void;
}

const DEFAULT_MAX = 12;
// Card width as a share of the table's width. Keeps the layout identical on a
// phone and a desktop, which matters because x/y are stored as fractions.
const CARD_W = 0.2;
const CARD_ASPECT = 3 / 2; // height / width
const SAVE_DEBOUNCE_MS = 700;

const labels = {
  ru: {
    deck: 'Колода',
    hint: 'Перетащи карту из колоды на стол — или просто коснись колоды.',
    hintPlaced: 'Перетаскивай карты или нажми на карту, а потом на место — она туда переедет.',
    hintPicked: 'Теперь нажми на стол там, где ей место.',
    flip: 'Перевернуть',
    full: 'Больше карт на стол не помещается.',
    error: 'Не получилось вытянуть карту. Попробуй ещё раз.',
    empty: 'Стол пока пуст.',
  },
  en: {
    deck: 'Deck',
    hint: 'Drag a card from the deck onto the table — or just tap the deck.',
    hintPlaced: 'Drag the cards, or tap a card and then tap a spot to send it there.',
    hintPicked: 'Now tap the table where it belongs.',
    flip: 'Turn over',
    full: 'The table is full.',
    error: "Couldn't draw a card. Try again.",
    empty: 'The table is empty for now.',
  },
} as const;

/** Viewport coordinates of the pointer that ended a drag.
 *
 *  framer-motion's `info.point` is relative to the document, while the table's
 *  own box comes from getBoundingClientRect(), which is relative to the
 *  viewport. Mixing the two only agrees at scroll position zero — on a phone,
 *  where the page is always scrolled a little, every dropped card would land
 *  against an edge. The native event carries the client coordinates we need.
 */
function pointerPoint(
  event: MouseEvent | TouchEvent | PointerEvent,
  info: { point: { x: number; y: number } },
): { x: number; y: number } {
  const e = event as PointerEvent;
  if (typeof e?.clientX === 'number' && typeof e?.clientY === 'number') {
    return { x: e.clientX, y: e.clientY };
  }
  const touch = (event as TouchEvent)?.changedTouches?.[0];
  if (touch) return { x: touch.clientX, y: touch.clientY };
  return { x: info.point.x - window.scrollX, y: info.point.y - window.scrollY };
}

/** Where the n-th tapped card lands: rows of three, top to bottom. Only a
 *  starting arrangement — the person drags them wherever they want afterwards. */
function tapSpot(n: number): { x: number; y: number } {
  const perRow = 3;
  const col = n % perRow;
  const row = Math.floor(n / perRow);
  return {
    x: 0.22 + col * 0.28,
    y: Math.min(0.88, 0.18 + row * 0.24),
  };
}

/** A free surface: pull cards out of the deck and arrange them however you want. */
export default function FreeTable({
  readingId,
  locale,
  initialCards,
  maxCards = DEFAULT_MAX,
  onCardsChange,
}: FreeTableProps) {
  const t = labels[locale] ?? labels.en;
  const surfaceRef = useRef<HTMLDivElement>(null);
  const [cards, setCards] = useState<DrawnCard[]>(initialCards);
  const [drawing, setDrawing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openCard, setOpenCard] = useState<number | null>(null);
  // Tap-to-move: pick a card up, then tap where it should go. Dragging is the
  // nicer gesture, but it is also the one that fails quietly on a stubborn
  // touch device — this path needs nothing but two taps.
  const [picked, setPicked] = useState<number | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    onCardsChange?.(cards);
  }, [cards, onCardsChange]);

  // Positions are saved after the person stops moving things, not on every
  // pointer frame — dragging a card would otherwise fire a request per pixel.
  const scheduleSave = useCallback((next: DrawnCard[]) => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      saveTableLayout(
        readingId,
        next.map((c) => ({
          position_index: c.position_index,
          x: c.x,
          y: c.y,
          is_reversed: c.is_reversed,
        })),
      ).catch(() => {/* layout is cosmetic — a failed save must not break the table */});
    }, SAVE_DEBOUNCE_MS);
  }, [readingId]);

  useEffect(() => () => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
  }, []);

  /** Viewport point → fraction of the surface, clamped so a card stays on the table. */
  const toFraction = useCallback((clientX: number, clientY: number) => {
    const box = surfaceRef.current?.getBoundingClientRect();
    if (!box) return { x: 0.5, y: 0.5 };
    return {
      x: Math.min(1, Math.max(0, (clientX - box.left) / box.width)),
      y: Math.min(1, Math.max(0, (clientY - box.top) / box.height)),
    };
  }, []);

  const draw = useCallback(async (x: number, y: number) => {
    if (drawing || cards.length >= maxCards) return;
    setDrawing(true);
    setError(null);
    try {
      const drawn = await drawOntoTable(readingId, x, y);
      setCards((prev) => [...prev, drawn]);
    } catch {
      setError(t.error);
    } finally {
      setDrawing(false);
    }
  }, [drawing, cards.length, maxCards, readingId, t.error]);

  const moveCard = useCallback((index: number, clientX: number, clientY: number) => {
    const { x, y } = toFraction(clientX, clientY);
    setCards((prev) => {
      const next = prev.map((c) =>
        c.position_index === index ? { ...c, x, y } : c);
      scheduleSave(next);
      return next;
    });
  }, [toFraction, scheduleSave]);

  const flipCard = useCallback((index: number) => {
    setCards((prev) => {
      const next = prev.map((c) =>
        c.position_index === index ? { ...c, is_reversed: !c.is_reversed } : c);
      scheduleSave(next);
      return next;
    });
  }, [scheduleSave]);

  const isFull = cards.length >= maxCards;
  const opened = openCard === null
    ? null
    : cards.find((c) => c.position_index === openCard) ?? null;

  return (
    <div className="w-full flex flex-col gap-4">
      {/* The table surface. Aspect ratio is fixed so stored fractions map to the
          same arrangement on any screen. */}
      <div
        ref={surfaceRef}
        className="relative w-full rounded-2xl overflow-hidden"
        style={{
          aspectRatio: '3 / 4',
          background:
            'radial-gradient(ellipse at 50% 35%, rgba(42,30,68,0.75), rgba(14,10,26,0.9))',
          border: picked === null
            ? '1px solid rgba(212,175,55,0.22)'
            : '1px solid rgba(212,175,55,0.55)',
          touchAction: 'none',
        }}
        onClick={(e) => {
          if (picked === null) return;
          // Only a tap on the surface itself counts as "put it here" — a tap
          // that landed on a card is that card's own business.
          if (e.target !== e.currentTarget) return;
          moveCard(picked, e.clientX, e.clientY);
          setPicked(null);
        }}
      >
        {cards.length === 0 && (
          <p
            className="absolute inset-0 flex items-center justify-center px-8 text-center text-sm font-serif italic"
            style={{ color: 'rgba(201,194,224,0.4)' }}
          >
            {t.empty}
          </p>
        )}

        {cards.map((c) => (
          // Two elements on purpose. The wrapper owns the placement — left/top
          // plus the translate that centres the card on its point — and the
          // inner one owns the drag. Put both on the same element and
          // framer-motion's drag transform overwrites the centring one, so the
          // card silently shifts by half its size the first time it is moved.
          <div
            key={c.position_index}
            className="absolute"
            style={{
              left: `${c.x * 100}%`,
              top: `${c.y * 100}%`,
              width: `${CARD_W * 100}%`,
              transform: 'translate(-50%, -50%)',
              zIndex: 10 + c.position_index,
            }}
          >
            <motion.div
              drag
              dragMomentum={false}
              // The resting place is the wrapper's left/top; the drag transform
              // has to go back to zero once the new spot is stored, or the two
              // offsets add up on every move.
              dragSnapToOrigin
              onDragEnd={(event, info) => {
                const p = pointerPoint(event, info);
                moveCard(c.position_index, p.x, p.y);
              }}
              onClick={() => setPicked((p) => (p === c.position_index ? null : c.position_index))}
              className="cursor-grab active:cursor-grabbing"
              style={{
                touchAction: 'none',
                outline: picked === c.position_index
                  ? '2px solid rgba(212,175,55,0.85)' : 'none',
                outlineOffset: 2,
                borderRadius: 8,
              }}
            >
              <div style={{ aspectRatio: `1 / ${CARD_ASPECT}` }}>
                <CardFace
                  card={c.card}
                  isReversed={c.is_reversed}
                  locale={locale}
                  className="w-full h-full"
                />
              </div>
            </motion.div>
            <div className="flex justify-center gap-2 mt-1">
              <button
                type="button"
                onClick={() => setOpenCard(c.position_index)}
                className="text-[0.6rem] underline"
                style={{ color: 'rgba(201,194,224,0.65)' }}
              >
                {locale === 'ru' ? 'значение' : 'meaning'}
              </button>
              <button
                type="button"
                onClick={() => flipCard(c.position_index)}
                aria-label={t.flip}
                title={t.flip}
                className="text-[0.6rem]"
                style={{ color: 'rgba(212,175,55,0.7)' }}
              >
                ⟲
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Deck: drag a card off it, or tap it. Tapping matters — dragging on a
          small screen is fiddly, and the Mini App is where most people are. */}
      <div className="flex items-center gap-4">
        <motion.button
          type="button"
          drag={!isFull}
          dragSnapToOrigin
          dragMomentum={false}
          whileTap={{ scale: 0.96 }}
          disabled={isFull || drawing}
          onDragEnd={(event, info) => {
            const p = pointerPoint(event, info);
            const { x, y } = toFraction(p.x, p.y);
            void draw(x, y);
          }}
          onClick={() => {
            // Tapped, not dragged. Lay each one in the next free spot instead
            // of the same point every time — otherwise repeated taps stack the
            // cards on top of each other and the table looks broken.
            const spot = tapSpot(cards.length);
            void draw(spot.x, spot.y);
          }}
          className="relative shrink-0 disabled:opacity-40"
          style={{ width: '5.5rem', touchAction: 'none' }}
          aria-label={t.deck}
        >
          <div style={{ aspectRatio: `1 / ${CARD_ASPECT}` }}>
            <CardBack className="w-full h-full" />
          </div>
        </motion.button>

        <div className="flex flex-col gap-1 text-xs" style={{ color: 'rgba(201,194,224,0.55)' }}>
          <span style={{ color: 'rgba(212,175,55,0.75)' }}>
            {t.deck} · {cards.length}/{maxCards}
          </span>
          <span style={picked !== null ? { color: 'rgba(212,175,55,0.85)' } : undefined}>
            {picked !== null ? t.hintPicked : cards.length === 0 ? t.hint : t.hintPlaced}
          </span>
          {isFull && <span style={{ color: 'rgba(212,175,55,0.7)' }}>{t.full}</span>}
          {error && <span style={{ color: '#e06c75' }}>{error}</span>}
        </div>
      </div>

      {opened && (
        <CardDetailModal
          card={opened.card}
          isReversed={opened.is_reversed}
          positionLabel={
            locale === 'ru'
              ? `Карта ${opened.position_index + 1}`
              : `Card ${opened.position_index + 1}`
          }
          positionMeaning=""
          locale={locale}
          onClose={() => setOpenCard(null)}
        />
      )}
    </div>
  );
}
