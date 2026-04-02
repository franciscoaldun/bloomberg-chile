"use client";

import { useEffect, useState, useRef } from "react";
import { createChart, LineSeries, type Time } from "lightweight-charts";
import { fetchLatamFx } from "@/lib/api";
import TimeframeBar from "./TimeframeBar";

interface CurrencyResult {
  name: string;
  change_pct?: number;
  normalized?: { date: string; value: number }[];
  error?: string;
}

const FX_COLORS: Record<string, string> = {
  usd_clp: "#FF9900",
  brl_clp: "#3BBA13",
  ars_clp: "#FF433D",
  cop_clp: "#0B85DF",
  pen_clp: "#4AF6C3",
  mxn_clp: "#FEE334",
};

const FX_LABELS: Record<string, string> = {
  usd_clp: "USD/CLP",
  brl_clp: "BRL/CLP",
  ars_clp: "ARS/CLP",
  cop_clp: "COP/CLP",
  pen_clp: "PEN/CLP",
  mxn_clp: "MXN/CLP",
};

export default function LatamFxChart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<Record<string, CurrencyResult> | null>(null);
  const [timeframe, setTimeframe] = useState("1Y");
  const [fromDate, setFromDate] = useState<string | undefined>(() => {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 1);
    return d.toISOString().split("T")[0];
  });

  useEffect(() => {
    const to = new Date().toISOString().split("T")[0];
    fetchLatamFx(fromDate, to)
      .then((d) => setData(d.currencies))
      .catch(console.error);
  }, [fromDate]);

  useEffect(() => {
    if (!data || !containerRef.current) return;
    const container = containerRef.current;

    const chart = createChart(container, {
      layout: {
        background: { color: "#000000" },
        textColor: "#7C7C7C",
        fontFamily: "IBM Plex Mono, monospace",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: "#1A1A1A" },
        horzLines: { color: "#1A1A1A" },
      },
      crosshair: {
        mode: 0,
        vertLine: { color: "#4AF6C3", width: 1, style: 2, labelBackgroundColor: "#0B85DF" },
        horzLine: { color: "#4AF6C3", width: 1, style: 2, labelBackgroundColor: "#0B85DF" },
      },
      rightPriceScale: { borderColor: "#333333" },
      timeScale: { borderColor: "#333333", timeVisible: false, rightOffset: 5 },
    });

    for (const [id, curr] of Object.entries(data)) {
      if (curr.error || !curr.normalized) continue;
      const color = FX_COLORS[id] || "#7C7C7C";
      const series = chart.addSeries(LineSeries, {
        color,
        lineWidth: 2,
        title: FX_LABELS[id] || id,
        priceFormat: { type: "price", precision: 1, minMove: 0.1 },
      });
      const chartData = curr.normalized.map((p) => ({
        time: p.date as Time,
        value: p.value,
      }));
      series.setData(chartData);
    }

    chart.timeScale().fitContent();

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [data]);

  // Ranking table
  const sorted = data
    ? Object.entries(data)
        .filter(([, v]) => !v.error && v.change_pct !== undefined)
        .sort(([, a], [, b]) => (b.change_pct ?? 0) - (a.change_pct ?? 0))
    : [];

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between">
        <span>CHILE vs LATAM FX (BASE 100)</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>NORMALIZADO</span>
      </div>
      <TimeframeBar
        active={timeframe}
        onChange={(label, from) => {
          setTimeframe(label);
          setFromDate(from);
        }}
      />
      <div className="flex-1 flex flex-col min-h-0">
        <div ref={containerRef} className="flex-1 min-h-0" />

        {/* Ranking strip */}
        {sorted.length > 0 && (
          <div className="flex items-center gap-3 px-2 py-1" style={{ borderTop: "1px solid #1A1A1A", fontSize: "9px" }}>
            {sorted.map(([id, curr]) => (
              <span key={id} className="flex items-center gap-1">
                <span className="inline-block w-2 h-2" style={{ background: FX_COLORS[id] || "#7C7C7C" }} />
                <span className="text-bb-muted">{FX_LABELS[id] || id}</span>
                <span className={(curr.change_pct ?? 0) >= 0 ? "text-bb-green" : "text-bb-red"}>
                  {(curr.change_pct ?? 0) >= 0 ? "+" : ""}{curr.change_pct?.toFixed(1)}%
                </span>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
