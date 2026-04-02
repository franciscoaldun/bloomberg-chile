"use client";

import { useEffect, useState } from "react";
import { fetchCobre } from "@/lib/api";

interface CobreData {
  price: {
    value: number | null;
    date: string | null;
    change: number | null;
    change_pct: number | null;
    unit: string;
    name: string;
  };
  exports: {
    value: number | null;
    date: string | null;
    unit: string;
    name: string;
  };
}

export default function CobrePanel() {
  const [data, setData] = useState<CobreData | null>(null);

  useEffect(() => {
    fetchCobre().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <span className="text-bb-muted">Cargando cobre...</span>
      </div>
    );
  }

  const { price, exports: exp } = data;
  const isUp = (price.change_pct ?? 0) >= 0;

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header">COBRE</div>

      <div className="flex-1 flex flex-col justify-center px-3 py-2">
        {/* Price */}
        <div className="mb-4">
          <div className="text-bb-muted" style={{ fontSize: "9px", fontFamily: "IBM Plex Sans Condensed, sans-serif" }}>
            PRECIO BML (USD/LB)
          </div>
          <div
            className="text-bb-amber font-bold"
            style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "28px", lineHeight: "1.1" }}
          >
            {price.value !== null ? `$${price.value.toFixed(4)}` : "---"}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`font-semibold ${isUp ? "text-bb-green" : "text-bb-red"}`}
              style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "13px" }}
            >
              {price.change !== null ? `${isUp ? "+" : ""}${price.change.toFixed(4)}` : "---"}
            </span>
            <span
              className={`font-semibold ${isUp ? "text-bb-green" : "text-bb-red"}`}
              style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "13px" }}
            >
              ({price.change_pct !== null ? `${isUp ? "+" : ""}${price.change_pct.toFixed(2)}%` : "---"})
            </span>
          </div>
          <div className="text-bb-muted mt-1" style={{ fontSize: "9px" }}>
            {price.date || "---"}
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-bb-border mb-4" />

        {/* Exports */}
        <div>
          <div className="text-bb-muted" style={{ fontSize: "9px", fontFamily: "IBM Plex Sans Condensed, sans-serif" }}>
            EXPORTACIONES COBRE (MENSUAL)
          </div>
          <div
            className="text-bb-white font-bold"
            style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "18px" }}
          >
            {exp.value !== null ? `US$${exp.value.toLocaleString("es-CL", { maximumFractionDigits: 0 })}M` : "---"}
          </div>
          <div className="text-bb-muted mt-1" style={{ fontSize: "9px" }}>
            {exp.date || "---"}
          </div>
        </div>
      </div>
    </div>
  );
}
