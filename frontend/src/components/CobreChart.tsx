"use client";

import { useEffect, useState, useRef } from "react";
import { createChart, LineSeries, type Time } from "lightweight-charts";
import { fetchSeries, fetchSma } from "@/lib/api";
import TimeframeBar from "./TimeframeBar";

const SMA_COLORS: Record<string, string> = {
  sma_20: "#FF9900",
  sma_50: "#0B85DF",
  sma_200: "#FF433D",
};

export default function CobreChart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [timeframe, setTimeframe] = useState("2Y");
  const [fromDate, setFromDate] = useState<string | undefined>(() => {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 2);
    return d.toISOString().split("T")[0];
  });
  const [smaEnabled, setSmaEnabled] = useState<Record<string, boolean>>({
    sma_20: false,
    sma_50: true,
    sma_200: true,
  });

  useEffect(() => {
    if (!containerRef.current) return;
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

    const mainSeries = chart.addSeries(LineSeries, {
      color: "#FF9900",
      lineWidth: 2,
      title: "COBRE",
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const smaSeries: Record<string, any> = {};

    async function loadData() {
      const to = new Date().toISOString().split("T")[0];
      try {
        const [seriesData, smaData] = await Promise.all([
          fetchSeries("cobre", fromDate, to),
          fetchSma("cobre", "20,50,200", fromDate, to),
        ]);

        const chartData = (seriesData.data || [])
          .filter((p: { value: number | null }) => p.value !== null)
          .map((p: { date: string; value: number }) => ({ time: p.date as Time, value: p.value }));
        mainSeries.setData(chartData);

        // SMA lines
        for (const [key, color] of Object.entries(SMA_COLORS)) {
          if (smaSeries[key]) {
            chart.removeSeries(smaSeries[key]);
            delete smaSeries[key];
          }
          if (smaEnabled[key] && smaData.sma?.[key]) {
            const s = chart.addSeries(LineSeries, {
              color,
              lineWidth: 1,
              lineStyle: 2, // dashed
              title: key.toUpperCase().replace("_", " "),
              priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
            });
            const smaChartData = smaData.sma[key]
              .filter((p: { value: number | null }) => p.value !== null)
              .map((p: { date: string; value: number }) => ({ time: p.date as Time, value: p.value }));
            s.setData(smaChartData);
            smaSeries[key] = s;
          }
        }

        chart.timeScale().fitContent();
      } catch (e) {
        console.error("Error loading cobre chart:", e);
      }
    }

    loadData();

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [fromDate, smaEnabled]);

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between items-center">
        <span>PRECIO COBRE BML (USD/LB)</span>
        <div className="flex items-center gap-1">
          {Object.entries(SMA_COLORS).map(([key, color]) => (
            <button
              key={key}
              onClick={() => setSmaEnabled((prev) => ({ ...prev, [key]: !prev[key] }))}
              className={`px-1.5 py-0.5 text-xs transition-colors ${
                smaEnabled[key] ? "opacity-100" : "opacity-30"
              }`}
              style={{
                color,
                fontFamily: "IBM Plex Sans Condensed, sans-serif",
                fontSize: "9px",
                fontWeight: 600,
              }}
            >
              {key.replace("sma_", "SMA ")}
            </button>
          ))}
        </div>
      </div>
      <TimeframeBar
        active={timeframe}
        onChange={(label, from) => {
          setTimeframe(label);
          setFromDate(from);
        }}
      />
      <div ref={containerRef} className="flex-1 min-h-0" />
    </div>
  );
}
