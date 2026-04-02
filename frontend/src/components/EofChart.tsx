"use client";

import { useEffect, useState, useRef } from "react";
import { createChart, LineSeries, type Time } from "lightweight-charts";
import { fetchEof } from "@/lib/api";

interface EofSeries {
  name: string;
  data: { date: string; value: number }[];
  data_points: number;
}

const EOF_COLORS: Record<string, string> = {
  eof_5y_2m: "#4AF6C3",
  eof_5y_11m: "#0B85DF",
  eof_5y_23m: "#FF9900",
};

const EOF_LABELS: Record<string, string> = {
  eof_5y_2m: "2 Meses",
  eof_5y_11m: "11 Meses",
  eof_5y_23m: "23 Meses",
};

export default function EofChart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<Record<string, EofSeries> | null>(null);

  useEffect(() => {
    fetchEof().then((d) => setData(d.series)).catch(console.error);
  }, []);

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

    for (const [id, series] of Object.entries(data)) {
      if (!series.data?.length) continue;
      const color = EOF_COLORS[id] || "#7C7C7C";
      const s = chart.addSeries(LineSeries, {
        color,
        lineWidth: 2,
        title: EOF_LABELS[id] || id,
        priceFormat: { type: "price", precision: 2, minMove: 0.01 },
      });
      const chartData = series.data
        .filter((p) => p.value !== null)
        .map((p) => ({
          time: p.date as Time,
          value: p.value,
        }));
      s.setData(chartData);
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

  if (!data) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <span className="text-bb-muted">Cargando expectativas...</span>
      </div>
    );
  }

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between">
        <span>EXPECTATIVAS EOF (BCP 5Y)</span>
        <div className="flex items-center gap-2" style={{ fontSize: "9px" }}>
          {Object.entries(EOF_COLORS).map(([id, color]) => (
            <span key={id} className="flex items-center gap-1">
              <span className="inline-block w-2 h-2" style={{ background: color }} />
              <span className="text-bb-muted">{EOF_LABELS[id]}</span>
            </span>
          ))}
        </div>
      </div>
      <div ref={containerRef} className="flex-1 min-h-0" />
    </div>
  );
}
