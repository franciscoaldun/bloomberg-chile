"use client";

import { useEffect, useState } from "react";
import { fetchCorrelations } from "@/lib/api";
import { shortName } from "@/lib/format";

interface CorrelationData {
  matrix: Record<string, Record<string, number>>;
  labels: string[];
  observations: number;
}

function getCellColor(val: number): string {
  if (val >= 0.7) return "rgba(59, 186, 19, 0.8)";    // fuerte positiva — verde
  if (val >= 0.3) return "rgba(59, 186, 19, 0.35)";   // moderada positiva
  if (val > -0.3) return "rgba(124, 124, 124, 0.15)";  // neutra
  if (val > -0.7) return "rgba(255, 67, 61, 0.35)";   // moderada negativa
  return "rgba(255, 67, 61, 0.8)";                      // fuerte negativa — rojo
}

function getTextColor(val: number): string {
  if (Math.abs(val) >= 0.7) return "#FFFFFF";
  if (Math.abs(val) >= 0.3) return "#FF9900";
  return "#7C7C7C";
}

export default function CorrelationHeatmap() {
  const [data, setData] = useState<CorrelationData | null>(null);

  useEffect(() => {
    fetchCorrelations().then(setData).catch(console.error);
  }, []);

  if (!data || !data.labels.length) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <span className="text-bb-muted">Calculando correlaciones...</span>
      </div>
    );
  }

  const { matrix, labels, observations } = data;

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between">
        <span>MATRIZ DE CORRELACIONES</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>{observations} OBS</span>
      </div>
      <div className="flex-1 overflow-auto p-2">
        <table className="w-full border-collapse" style={{ fontSize: "10px" }}>
          <thead>
            <tr>
              <th className="p-1 text-left text-bb-muted" style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif" }}></th>
              {labels.map((l) => (
                <th
                  key={l}
                  className="p-1 text-center text-bb-white"
                  style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "9px", fontWeight: 600 }}
                >
                  {shortName(l)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {labels.map((row) => (
              <tr key={row}>
                <td
                  className="p-1 text-bb-white"
                  style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "9px", fontWeight: 600 }}
                >
                  {shortName(row)}
                </td>
                {labels.map((col) => {
                  const raw = matrix[row]?.[col];
                  const val = raw ?? null;
                  const isDiag = row === col;
                  return (
                    <td
                      key={col}
                      className="p-1 text-center"
                      style={{
                        background: isDiag ? "rgba(11, 133, 223, 0.3)" : val !== null ? getCellColor(val) : "rgba(124, 124, 124, 0.05)",
                        color: isDiag ? "#0B85DF" : val !== null ? getTextColor(val) : "#555",
                        fontWeight: val !== null && Math.abs(val) >= 0.7 ? 700 : 400,
                        minWidth: "45px",
                      }}
                    >
                      {isDiag ? "1.00" : val !== null ? val.toFixed(2) : "—"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex items-center gap-4 mt-3 px-1" style={{ fontSize: "9px" }}>
          <span className="text-bb-muted">ESCALA:</span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3" style={{ background: "rgba(255, 67, 61, 0.8)" }}></span>
            <span className="text-bb-muted">-1.0</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3" style={{ background: "rgba(124, 124, 124, 0.15)" }}></span>
            <span className="text-bb-muted">0.0</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3" style={{ background: "rgba(59, 186, 19, 0.8)" }}></span>
            <span className="text-bb-muted">+1.0</span>
          </span>
        </div>
      </div>
    </div>
  );
}
