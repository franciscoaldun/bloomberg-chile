"use client";

import { Indicator } from "@/types/series";
import { formatValue, formatChange, formatChangePct, formatDate, shortName } from "@/lib/format";

interface QuoteDisplayProps {
  indicator: Indicator;
}

export default function QuoteDisplay({ indicator }: QuoteDisplayProps) {
  const isUp = (indicator.change ?? 0) >= 0;
  const changeColor = indicator.change === null || indicator.change === 0
    ? "text-bb-amber"
    : isUp
      ? "text-bb-green"
      : "text-bb-red";

  const arrow = indicator.change === null || indicator.change === 0
    ? ""
    : isUp
      ? "\u25B2"
      : "\u25BC";

  return (
    <div className="bb-panel h-full flex flex-col">
      <div className="bb-panel-header flex justify-between">
        <span>{shortName(indicator.id)}</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>{indicator.frequency}</span>
      </div>
      <div className="flex-1 flex flex-col justify-center px-4 py-2">
        <div className="text-bb-white text-xs mb-1" style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif" }}>
          {indicator.name}
        </div>
        <div className="bb-quote-value text-bb-amber">
          {formatValue(indicator.value, indicator.unit)}
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className={`text-sm font-semibold ${changeColor}`}>
            {arrow} {formatChange(indicator.change)}
          </span>
          <span className={`text-sm ${changeColor}`}>
            ({formatChangePct(indicator.change_pct)})
          </span>
          <span className="text-bb-muted text-xs">
            {formatDate(indicator.date)}
          </span>
        </div>
      </div>
    </div>
  );
}
