const ORDER = [
  { key: 'evidence_based_advice', short: 'Evidence', color: 'var(--evidence)' },
  { key: 'anecdotal_experience', short: 'Anecdote', color: 'var(--anecdote)' },
  { key: 'unsupported_take', short: 'Take', color: 'var(--unsupported)' },
  { key: 'emotional_reaction', short: 'Feeling', color: 'var(--emotional)' },
];

// Semicircle from 180deg (left) to 0deg (right), split into 4 equal zones.
const START_ANGLE = 180;
const END_ANGLE = 0;
const CX = 150;
const CY = 150;
const R = 118;

function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy - r * Math.sin(rad) };
}

function arcPath(cx, cy, r, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, r, startAngle);
  const end = polarToCartesian(cx, cy, r, endAngle);
  const largeArc = Math.abs(startAngle - endAngle) > 180 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

export default function Gauge({ scoresByLabel, predictedLabel }) {
  const zoneSpan = (START_ANGLE - END_ANGLE) / ORDER.length;

  // Needle angle: place it at the center of the predicted label's zone,
  // nudged within the zone by that label's relative share of confidence.
  const predictedIndex = ORDER.findIndex((o) => o.key === predictedLabel);
  const needleAngle =
    predictedIndex >= 0
      ? START_ANGLE - zoneSpan * (predictedIndex + 0.5)
      : 90;

  const needleTip = polarToCartesian(CX, CY, R - 18, needleAngle);
  const predicted = ORDER.find((o) => o.key === predictedLabel);

  return (
    <div className="gauge-wrap">
      <svg viewBox="0 0 300 190" className="gauge-svg" role="img" aria-label={`Meter pointing at ${predicted?.short ?? '—'}`}>
        {ORDER.map((zone, i) => {
          const zoneStart = START_ANGLE - zoneSpan * i;
          const zoneEnd = START_ANGLE - zoneSpan * (i + 1);
          const isActive = zone.key === predictedLabel;
          return (
            <path
              key={zone.key}
              d={arcPath(CX, CY, R, zoneStart, zoneEnd)}
              stroke={zone.color}
              strokeWidth={isActive ? 16 : 10}
              strokeLinecap="butt"
              fill="none"
              opacity={isActive || !predictedLabel ? 1 : 0.35}
              style={{ transition: 'stroke-width 0.4s ease, opacity 0.4s ease' }}
            />
          );
        })}

        {/* zone dividers */}
        {[0, 1, 2, 3, 4].map((i) => {
          const angle = START_ANGLE - zoneSpan * i;
          const inner = polarToCartesian(CX, CY, R - 10, angle);
          const outer = polarToCartesian(CX, CY, R + 10, angle);
          return (
            <line
              key={i}
              x1={inner.x}
              y1={inner.y}
              x2={outer.x}
              y2={outer.y}
              stroke="var(--bg)"
              strokeWidth={2}
            />
          );
        })}

        {/* needle */}
        <g style={{ transition: 'transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1)' }}>
          <line
            x1={CX}
            y1={CY}
            x2={needleTip.x}
            y2={needleTip.y}
            stroke="var(--ink)"
            strokeWidth={3}
            strokeLinecap="round"
          />
          <circle cx={CX} cy={CY} r={7} fill="var(--ink)" />
          <circle cx={CX} cy={CY} r={3} fill="var(--bg)" />
        </g>
      </svg>

      <div className="gauge-labels">
        {ORDER.map((zone) => (
          <span key={zone.key} className="gauge-label" style={{ color: zone.color }}>
            {zone.short}
          </span>
        ))}
      </div>
    </div>
  );
}
