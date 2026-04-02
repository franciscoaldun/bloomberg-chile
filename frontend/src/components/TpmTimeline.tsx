"use client";

import { useEffect, useState } from "react";
import { fetchTpmDecisions } from "@/lib/api";

interface Decision {
  date: string;
  rate: number;
  previous_rate: number;
  change: number;
  direction: "up" | "down";
}

export default function TpmTimeline() {
  const [decisions, setDecisions] = useState<Decision[]>([]);

  useEffect(() => {
    fetchTpmDecisions(15)
      .then((d) => setDecisions(d.decisions || []))
      .catch(console.error);
  }, []);

  if (!decisions.length) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <span className="text-bb-muted">Cargando decisiones TPM...</span>
      </div>
    );
  }

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between">
        <span>DECISIONES TPM</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>{decisions.length} CAMBIOS</span>
      </div>
      <div className="flex-1 overflow-auto">
        {decisions.map((d, i) => {
          const isUp = d.direction === "up";
          const icon = isUp ? "\u25B2" : "\u25BC";
          const color = isUp ? "text-bb-red" : "text-bb-green";

          return (
            <div
              key={d.date}
              className="flex items-center px-3 py-2"
              style={{
                borderBottom: "1px solid #1A1A1A",
                background: i === 0 ? "rgba(11, 133, 223, 0.08)" : "transparent",
              }}
            >
              {/* Timeline dot */}
              <div className="flex flex-col items-center mr-3" style={{ minWidth: "12px" }}>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${isUp ? "bg-bb-red" : "bg-bb-green"}`}
                />
                {i < decisions.length - 1 && (
                  <div className="w-px h-4 bg-bb-border mt-1" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 flex items-center justify-between">
                <div>
                  <div
                    className="text-bb-white font-semibold"
                    style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "11px" }}
                  >
                    TPM {d.previous_rate}% → {d.rate}%
                  </div>
                  <div className="text-bb-muted" style={{ fontSize: "9px" }}>
                    {d.date}
                  </div>
                </div>

                <div className="text-right">
                  <span
                    className={`font-bold ${color}`}
                    style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "12px" }}
                  >
                    {icon} {d.change > 0 ? "+" : ""}{(d.change * 100).toFixed(0)} bps
                  </span>
                </div>
              </div>
            </div>
          );
        })}

        <div className="px-3 py-1 text-bb-muted" style={{ fontSize: "8px" }}>
          DERIVADO: deteccion mecanica de cambios en serie diaria TPM del BCCh
        </div>
      </div>
    </div>
  );
}
