'use client';

import RuneStone from './RuneStone';
import type { RuneCastItem, RuneCastPosition, RuneLayout } from '@/lib/types';

interface Props {
  layout: RuneLayout;
  items: RuneCastItem[];
  positions: RuneCastPosition[];
  locale: 'ru' | 'en';
}

/**
 * Renders the cast runes in a layout-appropriate arrangement.
 *  - single → one big stone, centered
 *  - three  → three in a row
 *  - five   → cross (top / left-centre-right / bottom)
 */
export default function RuneCastBoard({ layout, items, positions, locale }: Props) {
  const sorted = [...items].sort((a, b) => a.position_index - b.position_index);

  const labelFor = (idx: number) => {
    const pos = positions[idx];
    if (!pos) return undefined;
    return locale === 'ru' ? pos.label_ru : pos.label_en;
  };
  const nameFor = (item: RuneCastItem) => (locale === 'ru' ? item.rune.name_ru : item.rune.name_en);

  if (layout === 'single' && sorted.length >= 1) {
    return (
      <div className="flex justify-center">
        <RuneStone
          symbol={sorted[0].rune.symbol}
          name={nameFor(sorted[0])}
          positionLabel={labelFor(0)}
          size="lg"
        />
      </div>
    );
  }

  if (layout === 'three') {
    return (
      <div className="flex justify-center gap-6 md:gap-10 flex-wrap">
        {sorted.map((item, i) => (
          <RuneStone
            key={item.position_index}
            symbol={item.rune.symbol}
            name={nameFor(item)}
            positionLabel={labelFor(item.position_index)}
            delay={i * 0.18}
            size="md"
          />
        ))}
      </div>
    );
  }

  // five — cross layout
  const [past, present, hidden, advice, outcome] = [0, 1, 2, 3, 4].map((i) =>
    sorted.find((it) => it.position_index === i),
  );
  return (
    <div className="grid grid-cols-3 gap-4 max-w-md mx-auto place-items-center">
      <div />
      {past && (
        <RuneStone
          symbol={past.rune.symbol}
          name={nameFor(past)}
          positionLabel={labelFor(0)}
          delay={0}
          size="sm"
        />
      )}
      <div />
      {hidden && (
        <RuneStone
          symbol={hidden.rune.symbol}
          name={nameFor(hidden)}
          positionLabel={labelFor(2)}
          delay={0.18}
          size="sm"
        />
      )}
      {present && (
        <RuneStone
          symbol={present.rune.symbol}
          name={nameFor(present)}
          positionLabel={labelFor(1)}
          delay={0.36}
          size="md"
        />
      )}
      {advice && (
        <RuneStone
          symbol={advice.rune.symbol}
          name={nameFor(advice)}
          positionLabel={labelFor(3)}
          delay={0.54}
          size="sm"
        />
      )}
      <div />
      {outcome && (
        <RuneStone
          symbol={outcome.rune.symbol}
          name={nameFor(outcome)}
          positionLabel={labelFor(4)}
          delay={0.72}
          size="sm"
        />
      )}
      <div />
    </div>
  );
}
