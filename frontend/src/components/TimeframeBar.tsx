"use client";

const TIMEFRAMES = [
  { label: "1M", months: 1 },
  { label: "3M", months: 3 },
  { label: "6M", months: 6 },
  { label: "1Y", months: 12 },
  { label: "2Y", months: 24 },
  { label: "5Y", months: 60 },
  { label: "MAX", months: 0 },
] as const;

interface TimeframeBarProps {
  active: string;
  onChange: (label: string, fromDate: string | undefined) => void;
}

function calcFromDate(months: number): string | undefined {
  if (months === 0) return undefined; // MAX = sin límite
  const d = new Date();
  d.setMonth(d.getMonth() - months);
  return d.toISOString().split("T")[0];
}

export default function TimeframeBar({ active, onChange }: TimeframeBarProps) {
  return (
    <div className="flex items-center gap-0 px-2 py-1" style={{ borderBottom: "1px solid #1A1A1A" }}>
      {TIMEFRAMES.map((tf) => (
        <button
          key={tf.label}
          onClick={() => onChange(tf.label, calcFromDate(tf.months))}
          className={`px-2 py-0.5 text-xs font-semibold transition-colors ${
            active === tf.label
              ? "text-bb-amber bg-bb-amber/10"
              : "text-bb-muted hover:text-bb-white"
          }`}
          style={{
            fontFamily: "IBM Plex Sans Condensed, sans-serif",
            fontSize: "10px",
            letterSpacing: "0.5px",
          }}
        >
          {tf.label}
        </button>
      ))}
    </div>
  );
}
