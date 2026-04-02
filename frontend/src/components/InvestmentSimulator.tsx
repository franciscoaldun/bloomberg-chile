"use client";

import { useEffect, useState, useRef } from "react";
import { createChart, LineSeries, type Time } from "lightweight-charts";
import { fetchSimulator } from "@/lib/api";

interface InstrumentResult {
  name: string;
  return_pct: number;
  initial_amount: number;
  final_amount: number;
  profit: number;
  first_date: string;
  last_date: string;
  data_points: number;
  normalized: { date: string; value: number }[];
  error?: string;
}

interface SimulatorData {
  instruments: Record<string, InstrumentResult>;
  initial_amount: number;
  period: { from: string; to: string };
}

const COLORS: Record<string, string> = {
  uf: "#FEE334",       // amarillo
  ipsa: "#3BBA13",     // verde
  usd_clp: "#0B85DF",  // azul
  deposito: "#FF9900",  // amber
};

export default function InvestmentSimulator() {
  const [data, setData] = useState<SimulatorData | null>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSimulator(1000000).then(setData).catch(console.error);
  }, []);

  useEffect(() => {
    if (!data || !chartContainerRef.current) return;

    const container = chartContainerRef.current;
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

    for (const [instId, inst] of Object.entries(data.instruments)) {
      if (inst.error || !inst.normalized) continue;
      const color = COLORS[instId] || "#FF9900";
      const series = chart.addSeries(LineSeries, {
        color,
        lineWidth: 2,
        title: inst.name,
        priceFormat: { type: "price", precision: 1, minMove: 0.1 },
      });
      const chartData = inst.normalized.map((p) => ({
        time: p.date as Time,
        value: p.value,
      }));
      series.setData(chartData);
    }

    chart.timeScale().fitContent();

    const ro = new ResizeObserver(() => {
      if (container) {
        chart.applyOptions({
          width: container.clientWidth,
          height: container.clientHeight,
        });
      }
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [data]);

  if (!data) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <span className="text-bb-muted">Calculando simulacion...</span>
      </div>
    );
  }

  const sorted = Object.entries(data.instruments)
    .filter(([, v]) => !v.error)
    .sort(([, a], [, b]) => b.return_pct - a.return_pct);

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between">
        <span>SIMULADOR DE INVERSION (BASE 100)</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>
          ${(data.initial_amount / 1000000).toFixed(0)}M CLP INICIAL
        </span>
      </div>
      <div className="flex-1 flex flex-col min-h-0">
        {/* Chart */}
        <div ref={chartContainerRef} className="flex-1 min-h-0" />

        {/* Results table */}
        <div className="border-t border-bb-border">
          <table className="bb-table">
            <thead>
              <tr>
                <th>INSTRUMENTO</th>
                <th>RETORNO</th>
                <th>MONTO FINAL</th>
                <th>GANANCIA</th>
                <th>PERIODO</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(([id, inst]) => (
                <tr key={id}>
                  <td style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontWeight: 600 }}>
                    <span className="inline-block w-2 h-2 mr-2" style={{ background: COLORS[id] || "#FF9900" }}></span>
                    {inst.name}
                  </td>
                  <td className={inst.return_pct >= 0 ? "text-bb-green" : "text-bb-red"}>
                    {inst.return_pct >= 0 ? "+" : ""}{inst.return_pct.toFixed(2)}%
                  </td>
                  <td className="text-bb-amber">
                    ${inst.final_amount.toLocaleString("es-CL")}
                  </td>
                  <td className={inst.profit >= 0 ? "text-bb-green" : "text-bb-red"}>
                    {inst.profit >= 0 ? "+" : ""}${inst.profit.toLocaleString("es-CL")}
                  </td>
                  <td className="text-bb-muted" style={{ fontSize: "9px" }}>
                    {inst.first_date?.slice(0, 7)} → {inst.last_date?.slice(0, 7)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
