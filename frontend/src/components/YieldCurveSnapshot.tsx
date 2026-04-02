"use client";

import { useEffect, useState } from "react";
import { fetchYieldCurve } from "@/lib/api";

interface YieldPoint {
  id: string;
  name: string;
  tenor_years: number;
  value: number | null;
  date: string | null;
}

interface YieldData {
  points: YieldPoint[];
  spread_10_2: number | null;
  signal: string;
}

function signalColor(signal: string): string {
  if (signal === "normal") return "text-bb-green";
  if (signal === "inverted") return "text-bb-red";
  return "text-bb-amber";
}

function signalLabel(signal: string): string {
  if (signal === "normal") return "NORMAL";
  if (signal === "inverted") return "INVERTIDA";
  return "FLAT";
}

export default function YieldCurveSnapshot() {
  const [data, setData] = useState<YieldData | null>(null);

  useEffect(() => {
    fetchYieldCurve().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <span className="text-bb-muted">Cargando yield curve...</span>
      </div>
    );
  }

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header">CURVA DE RENDIMIENTO</div>

      <div className="flex-1 overflow-auto">
        <table className="bb-table w-full">
          <thead>
            <tr>
              <th>PLAZO</th>
              <th>TASA</th>
            </tr>
          </thead>
          <tbody>
            {data.points.map((p) => (
              <tr key={p.id}>
                <td
                  style={{
                    fontFamily: "IBM Plex Sans Condensed, sans-serif",
                    fontWeight: 600,
                    fontSize: "11px",
                  }}
                >
                  {p.tenor_years === 0 ? "TPM" : `BCP ${p.tenor_years}Y`}
                </td>
                <td
                  className="text-bb-amber"
                  style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "13px" }}
                >
                  {p.value !== null ? `${p.value.toFixed(2)}%` : "---"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Spread & Signal */}
        <div className="border-t border-bb-border px-3 py-2">
          <div className="flex justify-between items-center mb-2">
            <span className="text-bb-muted" style={{ fontSize: "9px", fontFamily: "IBM Plex Sans Condensed, sans-serif" }}>
              SPREAD 10Y-2Y
            </span>
            <span
              className="text-bb-white font-bold"
              style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "14px" }}
            >
              {data.spread_10_2 !== null ? `${data.spread_10_2 > 0 ? "+" : ""}${data.spread_10_2.toFixed(2)}%` : "---"}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-bb-muted" style={{ fontSize: "9px", fontFamily: "IBM Plex Sans Condensed, sans-serif" }}>
              FORMA CURVA
            </span>
            <span
              className={`font-bold ${signalColor(data.signal)}`}
              style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "12px" }}
            >
              {signalLabel(data.signal)}
            </span>
          </div>
        </div>

        <div className="px-3 py-1 text-bb-muted" style={{ fontSize: "8px" }}>
          DERIVADO: spread y senal calculados sobre datos raw BCCh
        </div>
      </div>
    </div>
  );
}
