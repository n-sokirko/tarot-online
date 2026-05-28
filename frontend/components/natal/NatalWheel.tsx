'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import type { NatalPlanet, NatalHouse, NatalAspect } from '@/lib/types';

interface NatalWheelProps {
  planets: NatalPlanet[];
  houses: NatalHouse[];
  aspects: NatalAspect[];
  ascendant: number | null;
  isPremium: boolean;
  birthName?: string;
  birthDate?: string;
}

// ---- Constants ----

const CX = 250;
const CY = 250;

const R_ZODIAC_OUTER = 250;
const R_ZODIAC_INNER = 220;
const R_GLYPH = 236;
const R_HOUSE_OUTER = 218;
const R_HOUSE_INNER = 182;
const R_PLANET = 160;
const R_PLANET_GLYPH = 145;
const R_ASPECT = 130;
const R_CENTER = 80;

const ZODIAC_SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const;

const ZODIAC_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

// Element colors (subtle background fill)
const ELEMENT_COLORS: Record<string, string> = {
  Aries: 'rgba(180,60,40,0.25)',
  Leo: 'rgba(180,60,40,0.25)',
  Sagittarius: 'rgba(180,60,40,0.25)',
  Taurus: 'rgba(80,140,60,0.2)',
  Virgo: 'rgba(80,140,60,0.2)',
  Capricorn: 'rgba(80,140,60,0.2)',
  Gemini: 'rgba(80,140,200,0.2)',
  Libra: 'rgba(80,140,200,0.2)',
  Aquarius: 'rgba(80,140,200,0.2)',
  Cancer: 'rgba(80,80,200,0.2)',
  Scorpio: 'rgba(80,80,200,0.2)',
  Pisces: 'rgba(80,80,200,0.2)',
};

const ASPECT_COLORS: Record<string, string> = {
  Conjunction: 'rgba(212,175,55,0.5)',
  Trine: 'rgba(80,120,220,0.4)',
  Square: 'rgba(200,80,80,0.4)',
  Sextile: 'rgba(80,180,120,0.35)',
  Opposition: 'rgba(160,80,220,0.4)',
};

const ASPECT_STROKE: Record<string, number> = {
  Conjunction: 1.5,
  Trine: 1.2,
  Square: 1.2,
  Sextile: 1,
  Opposition: 1,
};

// Big-3 planets (free tier)
const BIG_THREE = new Set(['Sun', 'Moon', 'ASC']);

// ---- Math helpers ----

function toSvgAngle(absPos: number, ascPos: number): number {
  const offset = ((absPos - ascPos) + 360) % 360;
  return (180 - offset) * (Math.PI / 180);
}

function ptOnCircle(r: number, angle: number): { x: number; y: number } {
  return { x: CX + r * Math.cos(angle), y: CY + r * Math.sin(angle) };
}

function arcPath(
  startAbsDeg: number,
  endAbsDeg: number,
  rInner: number,
  rOuter: number,
  ascPos: number,
): string {
  const a1 = toSvgAngle(startAbsDeg, ascPos);
  const a2 = toSvgAngle(endAbsDeg, ascPos);

  const p1o = ptOnCircle(rOuter, a1);
  const p2o = ptOnCircle(rOuter, a2);
  const p1i = ptOnCircle(rInner, a1);
  const p2i = ptOnCircle(rInner, a2);

  // sweepFlag=0 → CCW arc
  return [
    `M ${p1o.x.toFixed(2)} ${p1o.y.toFixed(2)}`,
    `A ${rOuter} ${rOuter} 0 0 0 ${p2o.x.toFixed(2)} ${p2o.y.toFixed(2)}`,
    `L ${p2i.x.toFixed(2)} ${p2i.y.toFixed(2)}`,
    `A ${rInner} ${rInner} 0 0 1 ${p1i.x.toFixed(2)} ${p1i.y.toFixed(2)}`,
    'Z',
  ].join(' ');
}

// ---- Tooltip state ----

interface TooltipInfo {
  x: number;
  y: number;
  text: string;
}

// ---- Sub-components ----

function ZodiacRing({ ascPos }: { ascPos: number }) {
  return (
    <g>
      {ZODIAC_SIGNS.map((sign, i) => {
        const startDeg = i * 30;
        const endDeg = (i + 1) * 30;
        const midDeg = startDeg + 15;
        const midAngle = toSvgAngle(midDeg, ascPos);
        const glyphPt = ptOnCircle(R_GLYPH, midAngle);
        const color = ELEMENT_COLORS[sign] ?? 'rgba(100,100,150,0.15)';

        return (
          <g key={sign}>
            <path
              d={arcPath(startDeg, endDeg, R_ZODIAC_INNER, R_ZODIAC_OUTER, ascPos)}
              fill={color}
              stroke="rgba(212,175,55,0.25)"
              strokeWidth="0.5"
            />
            <text
              x={glyphPt.x}
              y={glyphPt.y}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="11"
              fill="rgba(212,175,55,0.8)"
              style={{ userSelect: 'none', pointerEvents: 'none' }}
            >
              {ZODIAC_GLYPHS[i]}
            </text>
          </g>
        );
      })}
      {/* Outer and inner border circles */}
      <circle cx={CX} cy={CY} r={R_ZODIAC_OUTER} fill="none" stroke="rgba(212,175,55,0.3)" strokeWidth="0.5" />
      <circle cx={CX} cy={CY} r={R_ZODIAC_INNER} fill="none" stroke="rgba(212,175,55,0.25)" strokeWidth="0.5" />
    </g>
  );
}

function HouseRing({ houses, ascPos }: { houses: NatalHouse[]; ascPos: number }) {
  if (houses.length === 0) return null;
  return (
    <g>
      {houses.map((house) => {
        const angle = toSvgAngle(house.abs_pos, ascPos);
        const outerPt = ptOnCircle(R_HOUSE_OUTER, angle);
        const innerPt = ptOnCircle(R_HOUSE_INNER, angle);
        const midAngle = toSvgAngle(house.abs_pos + 15, ascPos);
        const labelPt = ptOnCircle((R_HOUSE_OUTER + R_HOUSE_INNER) / 2, midAngle);

        return (
          <g key={house.number}>
            <line
              x1={outerPt.x} y1={outerPt.y}
              x2={innerPt.x} y2={innerPt.y}
              stroke="rgba(212,175,55,0.2)"
              strokeWidth="0.75"
            />
            <text
              x={labelPt.x}
              y={labelPt.y}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="8"
              fill="rgba(201,194,224,0.4)"
              style={{ userSelect: 'none', pointerEvents: 'none' }}
            >
              {house.number}
            </text>
          </g>
        );
      })}
      <circle cx={CX} cy={CY} r={R_HOUSE_OUTER} fill="none" stroke="rgba(212,175,55,0.18)" strokeWidth="0.5" />
      <circle cx={CX} cy={CY} r={R_HOUSE_INNER} fill="none" stroke="rgba(212,175,55,0.15)" strokeWidth="0.5" />
    </g>
  );
}

function AspectLines({
  aspects,
  planets,
  ascPos,
  isPremium,
}: {
  aspects: NatalAspect[];
  planets: NatalPlanet[];
  ascPos: number;
  isPremium: boolean;
}) {
  if (!isPremium) return null;

  const planetMap = new Map(planets.map((p) => [p.name, p]));

  return (
    <g>
      {aspects.map((asp, i) => {
        const p1 = planetMap.get(asp.planet1);
        const p2 = planetMap.get(asp.planet2);
        if (!p1 || !p2) return null;

        const a1 = toSvgAngle(p1.abs_pos, ascPos);
        const a2 = toSvgAngle(p2.abs_pos, ascPos);

        // Clip lines to inner aspect circle
        const pt1 = ptOnCircle(R_ASPECT, a1);
        const pt2 = ptOnCircle(R_ASPECT, a2);

        const color = ASPECT_COLORS[asp.aspect] ?? 'rgba(150,150,150,0.3)';
        const strokeWidth = ASPECT_STROKE[asp.aspect] ?? 0.8;

        return (
          <line
            key={i}
            x1={pt1.x.toFixed(2)} y1={pt1.y.toFixed(2)}
            x2={pt2.x.toFixed(2)} y2={pt2.y.toFixed(2)}
            stroke={color}
            strokeWidth={strokeWidth}
          />
        );
      })}
    </g>
  );
}

function PlanetDots({
  planets,
  ascPos,
  isPremium,
  onHover,
  onLeave,
}: {
  planets: NatalPlanet[];
  ascPos: number;
  isPremium: boolean;
  onHover: (info: TooltipInfo) => void;
  onLeave: () => void;
}) {
  // Build positions, then detect collisions and spread them
  const positioned = planets.map((planet) => {
    const angle = toSvgAngle(planet.abs_pos, ascPos);
    const pt = ptOnCircle(R_PLANET, angle);
    const glyphPt = ptOnCircle(R_PLANET_GLYPH, angle);
    return { planet, angle, pt, glyphPt };
  });

  // Simple collision resolution: sort by angle, push overlapping labels
  const MIN_ARC = (2 * Math.PI) / 60; // ~6° spacing threshold
  const sorted = [...positioned].sort((a, b) => a.angle - b.angle);
  const adjusted = sorted.map((item, idx) => {
    const labelAngle = idx === 0
      ? item.angle
      : (() => {
          const prev = sorted[idx - 1];
          const diff = item.angle - prev.angle;
          return diff < MIN_ARC ? prev.angle + MIN_ARC : item.angle;
        })();
    const labelPt = ptOnCircle(R_PLANET_GLYPH, labelAngle);
    return { ...item, labelAngle, labelPt };
  });

  return (
    <g>
      {adjusted.map(({ planet, pt, labelPt }) => {
        const isBig3 = BIG_THREE.has(planet.name);
        const dimmed = !isPremium && !isBig3;
        const opacity = dimmed ? 0.25 : 1;
        const finalLabelPt = labelPt;

        return (
          <g
            key={planet.name}
            opacity={opacity}
            style={{ cursor: dimmed ? 'default' : 'pointer' }}
            onMouseEnter={(e) => {
              if (dimmed) return;
              const svg = (e.currentTarget as SVGElement).closest('svg');
              const rect = svg?.getBoundingClientRect();
              if (!rect) return;
              const svgX = ((pt.x / 500) * rect.width) + rect.left;
              const svgY = ((pt.y / 500) * rect.height) + rect.top;
              const houseText = planet.house > 0 ? ` · H${planet.house}` : '';
              const retroText = planet.retrograde ? ' ℞' : '';
              onHover({
                x: svgX,
                y: svgY,
                text: `${planet.glyph} ${planet.name} ${planet.emoji} ${planet.sign} ${planet.position.toFixed(0)}°${houseText}${retroText}`,
              });
            }}
            onMouseLeave={onLeave}
          >
            {/* Dot */}
            <circle
              cx={pt.x.toFixed(2)}
              cy={pt.y.toFixed(2)}
              r={isBig3 ? 5.5 : 4}
              fill={isBig3 ? '#d4af37' : 'rgba(201,194,224,0.7)'}
              stroke={isBig3 ? 'rgba(212,175,55,0.4)' : 'rgba(201,194,224,0.2)'}
              strokeWidth="1"
            />
            {/* Glyph label */}
            <text
              x={finalLabelPt.x.toFixed(2)}
              y={finalLabelPt.y.toFixed(2)}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={isBig3 ? '11' : '9'}
              fill={isBig3 ? '#d4af37' : 'rgba(201,194,224,0.85)'}
              style={{ userSelect: 'none', pointerEvents: 'none' }}
            >
              {planet.glyph}
            </text>
          </g>
        );
      })}
    </g>
  );
}

function AscendantMarker({ ascPos }: { ascPos: number }) {
  const angle = toSvgAngle(ascPos, ascPos); // = 180° = left
  const outerPt = ptOnCircle(R_ZODIAC_INNER - 2, angle);
  const innerPt = ptOnCircle(R_HOUSE_INNER - 5, angle);

  return (
    <g>
      <line
        x1={outerPt.x.toFixed(2)} y1={outerPt.y.toFixed(2)}
        x2={innerPt.x.toFixed(2)} y2={innerPt.y.toFixed(2)}
        stroke="#d4af37"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <text
        x={(innerPt.x - 8).toFixed(2)}
        y={innerPt.y.toFixed(2)}
        textAnchor="end"
        dominantBaseline="central"
        fontSize="8"
        fill="rgba(212,175,55,0.75)"
        style={{ userSelect: 'none', pointerEvents: 'none' }}
      >
        AC
      </text>
    </g>
  );
}

function CenterInfo({ name, date }: { name?: string; date?: string }) {
  return (
    <g>
      <circle cx={CX} cy={CY} r={R_CENTER} fill="rgba(11,11,31,0.85)" stroke="rgba(212,175,55,0.2)" strokeWidth="0.5" />
      {name && (
        <text
          x={CX} y={CY - 8}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize="8"
          fill="rgba(212,175,55,0.65)"
          style={{ userSelect: 'none', pointerEvents: 'none' }}
        >
          {name.length > 14 ? name.slice(0, 13) + '…' : name}
        </text>
      )}
      {date && (
        <text
          x={CX} y={CY + 8}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize="7"
          fill="rgba(201,194,224,0.4)"
          style={{ userSelect: 'none', pointerEvents: 'none' }}
        >
          {date}
        </text>
      )}
    </g>
  );
}

// ---- Main component ----

export default function NatalWheel({
  planets,
  houses,
  aspects,
  ascendant,
  isPremium,
  birthName,
  birthDate,
}: NatalWheelProps) {
  const [tooltip, setTooltip] = useState<TooltipInfo | null>(null);

  const ascPos = ascendant ?? 0;

  return (
    <div className="relative w-full" style={{ maxWidth: '560px', margin: '0 auto' }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.7, ease: 'easeOut' }}
      >
        <svg
          viewBox="0 0 500 500"
          width="100%"
          aria-label="Natal chart wheel"
          style={{ display: 'block' }}
        >
          {/* Dark background */}
          <circle cx={CX} cy={CY} r={R_ZODIAC_OUTER} fill="rgba(11,11,31,0.95)" />

          {/* Aspect lines (innermost layer) */}
          <AspectLines
            aspects={aspects}
            planets={planets}
            ascPos={ascPos}
            isPremium={isPremium}
          />

          {/* Aspect circle boundary */}
          <circle cx={CX} cy={CY} r={R_ASPECT} fill="none" stroke="rgba(212,175,55,0.08)" strokeWidth="0.5" />

          {/* House ring */}
          <HouseRing houses={houses} ascPos={ascPos} />

          {/* Planet ring background */}
          <circle cx={CX} cy={CY} r={R_PLANET + 16} fill="none" stroke="rgba(212,175,55,0.08)" strokeWidth="0.5" />

          {/* Planet dots */}
          <PlanetDots
            planets={planets}
            ascPos={ascPos}
            isPremium={isPremium}
            onHover={setTooltip}
            onLeave={() => setTooltip(null)}
          />

          {/* Zodiac ring (outermost) */}
          <ZodiacRing ascPos={ascPos} />

          {/* Ascendant marker */}
          {ascendant !== null && <AscendantMarker ascPos={ascPos} />}

          {/* Center info */}
          <CenterInfo name={birthName} date={birthDate} />
        </svg>
      </motion.div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none px-3 py-1.5 rounded-lg text-xs font-mono"
          style={{
            left: tooltip.x,
            top: tooltip.y - 40,
            transform: 'translateX(-50%)',
            background: 'rgba(11,11,31,0.92)',
            border: '1px solid rgba(212,175,55,0.35)',
            color: 'rgba(201,194,224,0.9)',
            whiteSpace: 'nowrap',
            backdropFilter: 'blur(8px)',
          }}
        >
          {tooltip.text}
        </div>
      )}

      {/* Free-tier overlay hint */}
      {!isPremium && (
        <div
          className="mt-3 text-center text-xs"
          style={{ color: 'rgba(201,194,224,0.4)', letterSpacing: '0.05em' }}
        >
          ✦ Dimmed planets visible with Premium
        </div>
      )}
    </div>
  );
}
