import React from 'react';

/**
 * ScoreRadarChart
 * Custom SVG Radar Chart displaying the 6 ATS scoring breakdown dimensions:
 * - Keyword Match
 * - Semantic Similarity
 * - Section Completeness
 * - Formatting
 * - Experience Relevance
 * - Quantified Impact
 */
export default function ScoreRadarChart({ breakdown = {}, size = 280 }) {
  const dimensions = [
    { key: 'keyword_match', label: 'Keyword Match', value: breakdown.keyword_match ?? 78 },
    {
      key: 'semantic_similarity',
      label: 'Semantic Similarity',
      value: breakdown.semantic_similarity ?? 85,
    },
    {
      key: 'section_completeness',
      label: 'Completeness',
      value: breakdown.section_completeness ?? 95,
    },
    { key: 'formatting', label: 'ATS Format', value: breakdown.formatting ?? 90 },
    {
      key: 'experience_relevance',
      label: 'Experience Fit',
      value: breakdown.experience_relevance ?? 80,
    },
    {
      key: 'quantified_impact',
      label: 'Impact / Metrics',
      value: breakdown.quantified_impact ?? 65,
    },
  ];

  const center = size / 2;
  const radius = size * 0.36;
  const numAxes = dimensions.length;

  // Compute (x, y) coordinates for polygon
  const points = dimensions
    .map((d, i) => {
      const angle = ((Math.PI * 2) / numAxes) * i - Math.PI / 2;
      const r = (d.value / 100) * radius;
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);
      return `${x},${y}`;
    })
    .join(' ');

  // Grid concentric rings (25%, 50%, 75%, 100%)
  const gridRings = [0.25, 0.5, 0.75, 1.0];

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="overflow-visible">
        {/* Background Grid Rings */}
        {gridRings.map((scale, idx) => {
          const ringPoints = dimensions
            .map((_, i) => {
              const angle = ((Math.PI * 2) / numAxes) * i - Math.PI / 2;
              const r = radius * scale;
              const x = center + r * Math.cos(angle);
              const y = center + r * Math.sin(angle);
              return `${x},${y}`;
            })
            .join(' ');

          return (
            <polygon
              key={`ring-${idx}`}
              points={ringPoints}
              fill={idx === 3 ? 'rgba(99, 102, 241, 0.03)' : 'none'}
              stroke="currentColor"
              className="text-slate-200 dark:text-slate-700/60"
              strokeWidth="1"
              strokeDasharray={idx < 3 ? '3 3' : 'none'}
            />
          );
        })}

        {/* Axes lines */}
        {dimensions.map((_, i) => {
          const angle = ((Math.PI * 2) / numAxes) * i - Math.PI / 2;
          const x = center + radius * Math.cos(angle);
          const y = center + radius * Math.sin(angle);
          return (
            <line
              key={`axis-${i}`}
              x1={center}
              y1={center}
              x2={x}
              y2={y}
              stroke="currentColor"
              className="text-slate-200 dark:text-slate-700/60"
              strokeWidth="1"
            />
          );
        })}

        {/* Shaded polygon of actual resume scores */}
        <polygon
          points={points}
          fill="rgba(99, 102, 241, 0.25)"
          stroke="#6366F1"
          strokeWidth="2.5"
          className="transition-all duration-500 ease-out"
        />

        {/* Vertex Dots */}
        {dimensions.map((d, i) => {
          const angle = ((Math.PI * 2) / numAxes) * i - Math.PI / 2;
          const r = (d.value / 100) * radius;
          const x = center + r * Math.cos(angle);
          const y = center + r * Math.sin(angle);
          return (
            <circle
              key={`dot-${i}`}
              cx={x}
              cy={y}
              r="4.5"
              fill="#6366F1"
              stroke="#ffffff"
              strokeWidth="1.5"
              className="dark:stroke-slate-900"
            />
          );
        })}

        {/* Outer Axis Labels */}
        {dimensions.map((d, i) => {
          const angle = ((Math.PI * 2) / numAxes) * i - Math.PI / 2;
          const labelDist = radius + 24;
          const x = center + labelDist * Math.cos(angle);
          const y = center + labelDist * Math.sin(angle);
          const anchor = Math.abs(x - center) < 10 ? 'middle' : x > center ? 'start' : 'end';

          return (
            <text
              key={`label-${i}`}
              x={x}
              y={y + 4}
              textAnchor={anchor}
              className="text-[10px] font-semibold fill-slate-600 dark:fill-slate-300"
            >
              {d.label} ({d.value}%)
            </text>
          );
        })}
      </svg>
    </div>
  );
}
