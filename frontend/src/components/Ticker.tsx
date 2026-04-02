"use client";

import { Indicator } from "@/types/series";
import { shortName, formatValue, formatChangePct } from "@/lib/format";

interface TickerProps {
  indicators: Indicator[];
}

function TickerItem({ ind }: { ind: Indicator }) {
  const isUp = (ind.change_pct ?? 0) >= 0;
  const colorClass = ind.change_pct === null || ind.change_pct === 0
    ? "text-bb-amber"
    : isUp
      ? "text-bb-green"
      : "text-bb-red";

  return (
    <span className="inline-flex items-center gap-2 px-4">
      <span className="text-bb-white font-semibold" style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "11px" }}>
        {shortName(ind.id)}
      </span>
      <span className="text-bb-amber">{formatValue(ind.value, ind.unit)}</span>
      <span className={colorClass}>{formatChangePct(ind.change_pct)}</span>
    </span>
  );
}

export default function Ticker({ indicators }: TickerProps) {
  // Duplicar items para scroll infinito
  const items = [...indicators, ...indicators];

  return (
    <div className="w-full overflow-hidden border-b border-bb-border" style={{ background: "#0A0A0A" }}>
      <div
        className="ticker-animate flex whitespace-nowrap py-1"
        style={{ ["--ticker-duration" as string]: `${indicators.length * 3}s` }}
      >
        {items.map((ind, i) => (
          <TickerItem key={`${ind.id}-${i}`} ind={ind} />
        ))}
      </div>
    </div>
  );
}
