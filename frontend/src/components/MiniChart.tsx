"use client";

import { useEffect, useRef } from "react";
import { createChart, AreaSeries, type IChartApi, type Time } from "lightweight-charts";
import { SeriesPoint } from "@/types/series";

interface MiniChartProps {
  data: SeriesPoint[];
  color?: string;
  height?: number;
}

export default function MiniChart({ data, color = "#FF9900", height = 60 }: MiniChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: "transparent" },
        textColor: "transparent",
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
      },
      rightPriceScale: { visible: false },
      timeScale: { visible: false },
      handleScroll: false,
      handleScale: false,
      crosshair: {
        vertLine: { visible: false },
        horzLine: { visible: false },
      },
      width: containerRef.current.clientWidth,
      height: height,
    });

    const areaSeries = chart.addSeries(AreaSeries, {
      lineColor: color,
      lineWidth: 1,
      topColor: color + "30",
      bottomColor: color + "05",
      crosshairMarkerVisible: false,
    });

    const chartData = data
      .filter((p) => p.value !== null)
      .map((p) => ({ time: p.date as Time, value: p.value as number }));

    areaSeries.setData(chartData);
    chart.timeScale().fitContent();
    chartRef.current = chart;

    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [data, color, height]);

  return <div ref={containerRef} style={{ height }} />;
}
