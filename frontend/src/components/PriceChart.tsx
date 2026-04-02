"use client";

import { useEffect, useRef } from "react";
import { createChart, LineSeries, type IChartApi, type Time } from "lightweight-charts";
import { SeriesPoint } from "@/types/series";
import { shortName } from "@/lib/format";

interface PriceChartProps {
  seriesId: string;
  data: SeriesPoint[];
  title?: string;
  unit?: string;
  color?: string;
}

export default function PriceChart({
  seriesId,
  data,
  title,
  unit,
  color = "#FF9900",
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const seriesRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
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
        vertLine: {
          color: "#4AF6C3",
          width: 1,
          style: 2,
          labelBackgroundColor: "#0B85DF",
        },
        horzLine: {
          color: "#4AF6C3",
          width: 1,
          style: 2,
          labelBackgroundColor: "#0B85DF",
        },
      },
      rightPriceScale: {
        borderColor: "#333333",
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: "#333333",
        timeVisible: false,
        rightOffset: 5,
      },
      handleScroll: { vertTouchDrag: false },
    });

    const series = chart.addSeries(LineSeries, {
      color: color,
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 3,
      crosshairMarkerBorderColor: "#FFFFFF",
      crosshairMarkerBackgroundColor: color,
      priceFormat: {
        type: "price",
        precision: 2,
        minMove: 0.01,
      },
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(containerRef.current);
    handleResize();

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [color]);

  useEffect(() => {
    if (!seriesRef.current) return;

    // Filtrar NULLs — TradingView no puede graficar nulls, se muestran como gaps naturalmente
    const chartData = data
      .filter((p) => p.value !== null)
      .map((p) => ({
        time: p.date as Time,
        value: p.value as number,
      }));

    seriesRef.current.setData(chartData);

    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [data]);

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between">
        <span>{title || shortName(seriesId)}</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>{unit || ""}</span>
      </div>
      <div ref={containerRef} className="flex-1 min-h-0" />
    </div>
  );
}
