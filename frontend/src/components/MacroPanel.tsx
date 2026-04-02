"use client";

import { Indicator } from "@/types/series";
import { shortName, formatValue, formatChange, formatChangePct, formatDate } from "@/lib/format";
import FlashCell from "./FlashCell";

interface MacroPanelProps {
  title: string;
  indicators: Indicator[];
  onSelect?: (id: string) => void;
  selectedId?: string;
}

export default function MacroPanel({ title, indicators, onSelect, selectedId }: MacroPanelProps) {
  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between items-center">
        <span>{title}</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>BCCH</span>
      </div>
      <div className="flex-1 overflow-auto">
        <table className="bb-table">
          <thead>
            <tr>
              <th>INDICADOR</th>
              <th>VALOR</th>
              <th>CHG</th>
              <th>CHG%</th>
              <th>FECHA</th>
            </tr>
          </thead>
          <tbody>
            {indicators.map((ind) => {
              const isSelected = selectedId === ind.id;
              return (
                <tr
                  key={ind.id}
                  onClick={() => onSelect?.(ind.id)}
                  className={`cursor-pointer ${isSelected ? "!bg-bb-surface-light" : ""}`}
                >
                  <td
                    className={isSelected ? "!text-bb-cyan" : ""}
                    style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontWeight: 600 }}
                  >
                    {shortName(ind.id)}
                  </td>
                  <td className="text-bb-amber font-semibold">
                    {formatValue(ind.value, ind.unit)}
                  </td>
                  <FlashCell
                    value={formatChange(ind.change)}
                    change={ind.change}
                  />
                  <FlashCell
                    value={formatChangePct(ind.change_pct)}
                    change={ind.change_pct}
                  />
                  <td className="text-bb-muted" style={{ fontSize: "10px" }}>
                    {formatDate(ind.date)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
