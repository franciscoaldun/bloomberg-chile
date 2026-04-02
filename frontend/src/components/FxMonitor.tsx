"use client";

import { useEffect, useState } from "react";
import { fetchFxMonitor } from "@/lib/api";

interface FxPair {
  id: string;
  name: string;
  value: number | null;
  date: string | null;
  change: number | null;
  change_pct: number | null;
  unit: string;
}

const PAIR_LABELS: Record<string, string> = {
  usd_clp: "USD/CLP",
  eur_clp: "EUR/CLP",
  cny_clp: "CNY/CLP",
  brl_clp: "BRL/CLP",
  ars_clp: "ARS/CLP",
  cop_clp: "COP/CLP",
  pen_clp: "PEN/CLP",
  mxn_clp: "MXN/CLP",
};

export default function FxMonitor() {
  const [pairs, setPairs] = useState<FxPair[]>([]);

  useEffect(() => {
    fetchFxMonitor()
      .then((data) => setPairs(data.pairs || []))
      .catch(console.error);
  }, []);

  if (!pairs.length) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <span className="text-bb-muted">Cargando FX...</span>
      </div>
    );
  }

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header">CLP MONITOR</div>
      <div className="flex-1 overflow-auto">
        <table className="bb-table w-full">
          <thead>
            <tr>
              <th>PAR</th>
              <th>VALOR</th>
              <th>VAR %</th>
            </tr>
          </thead>
          <tbody>
            {pairs.map((p) => {
              const isUp = (p.change_pct ?? 0) >= 0;
              return (
                <tr key={p.id}>
                  <td
                    style={{
                      fontFamily: "IBM Plex Sans Condensed, sans-serif",
                      fontWeight: 600,
                      fontSize: "11px",
                    }}
                  >
                    {PAIR_LABELS[p.id] || p.id}
                  </td>
                  <td
                    className="text-bb-amber"
                    style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "11px" }}
                  >
                    {p.value !== null ? `$${p.value.toFixed(2)}` : "---"}
                  </td>
                  <td
                    className={isUp ? "text-bb-green" : "text-bb-red"}
                    style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "11px" }}
                  >
                    {p.change_pct !== null
                      ? `${isUp ? "+" : ""}${p.change_pct.toFixed(2)}%`
                      : "---"}
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
