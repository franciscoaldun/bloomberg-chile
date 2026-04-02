"use client";

import { useEffect, useState } from "react";
import { fetchAnalysis } from "@/lib/api";

interface Insight {
  category: string;
  title: string;
  detail: string;
  signal: string;
}

interface AnalysisData {
  insights: Insight[];
  generated_at: string;
}

function signalColor(signal: string): string {
  switch (signal) {
    case "bullish":
    case "dovish":
    case "safe":
      return "text-bb-green";
    case "bearish":
    case "risk":
      return "text-bb-red";
    default:
      return "text-bb-amber";
  }
}

function signalIcon(signal: string): string {
  switch (signal) {
    case "bullish":
    case "safe":
      return "\u25B2";
    case "bearish":
    case "risk":
      return "\u25BC";
    case "dovish":
      return "\u25C0";
    default:
      return "\u25CF";
  }
}

function signalLabel(signal: string): string {
  switch (signal) {
    case "bullish": return "ALCISTA";
    case "bearish": return "BAJISTA";
    case "dovish": return "EXPANSIVO";
    case "risk": return "RIESGO";
    case "safe": return "SEGURO";
    default: return "NEUTRAL";
  }
}

export default function AnalysisPanel() {
  const [data, setData] = useState<AnalysisData | null>(null);

  useEffect(() => {
    fetchAnalysis().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <span className="text-bb-muted">Generando analisis...</span>
      </div>
    );
  }

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between">
        <span>BRIEFING ECONOMICO</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>{data.generated_at}</span>
      </div>
      <div className="flex-1 overflow-auto">
        {data.insights.map((insight, i) => (
          <div
            key={i}
            className="border-b border-bb-border px-3 py-2"
            style={{ borderColor: "#1A1A1A" }}
          >
            <div className="flex items-center justify-between mb-1">
              <span
                className="text-bb-blue"
                style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "9px", fontWeight: 700, letterSpacing: "0.5px" }}
              >
                {insight.category}
              </span>
              <span className={`${signalColor(insight.signal)} flex items-center gap-1`} style={{ fontSize: "9px", fontWeight: 600 }}>
                {signalIcon(insight.signal)} {signalLabel(insight.signal)}
              </span>
            </div>
            <div className="text-bb-white text-sm font-semibold mb-1" style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif" }}>
              {insight.title}
            </div>
            <div className="text-bb-muted" style={{ fontSize: "11px", lineHeight: "1.4" }}>
              {insight.detail}
            </div>
          </div>
        ))}
        <div className="px-3 py-2 text-bb-muted" style={{ fontSize: "9px" }}>
          NOTA: Analisis computado a partir de datos raw del BCCh. No constituye consejo financiero.
        </div>
      </div>
    </div>
  );
}
