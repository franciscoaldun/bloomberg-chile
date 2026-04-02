"use client";

import { useEffect, useState, useRef } from "react";
import { fetchYieldCurve } from "@/lib/api";

interface YieldPoint {
  id: string;
  tenor_years: number;
  value: number | null;
}

interface YieldData {
  points: YieldPoint[];
  signal: string;
}

export default function YieldCurveChart() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<YieldData | null>(null);

  useEffect(() => {
    fetchYieldCurve().then(setData).catch(console.error);
  }, []);

  useEffect(() => {
    if (!data || !canvasRef.current || !containerRef.current) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const w = container.clientWidth;
    const h = container.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    ctx.scale(dpr, dpr);

    // Background
    ctx.fillStyle = "#000000";
    ctx.fillRect(0, 0, w, h);

    const valid = data.points.filter((p) => p.value !== null);
    if (valid.length < 2) return;

    const padLeft = 60;
    const padRight = 30;
    const padTop = 30;
    const padBottom = 40;
    const plotW = w - padLeft - padRight;
    const plotH = h - padTop - padBottom;

    const tenors = valid.map((p) => p.tenor_years);
    const values = valid.map((p) => p.value as number);
    const minT = 0;
    const maxT = Math.max(...tenors, 10);
    const minV = Math.min(...values) - 0.3;
    const maxV = Math.max(...values) + 0.3;

    function xPos(tenor: number) {
      return padLeft + ((tenor - minT) / (maxT - minT)) * plotW;
    }
    function yPos(val: number) {
      return padTop + (1 - (val - minV) / (maxV - minV)) * plotH;
    }

    // Grid
    ctx.strokeStyle = "#1A1A1A";
    ctx.lineWidth = 1;
    const ySteps = 5;
    for (let i = 0; i <= ySteps; i++) {
      const val = minV + ((maxV - minV) * i) / ySteps;
      const y = yPos(val);
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(w - padRight, y);
      ctx.stroke();

      ctx.fillStyle = "#7C7C7C";
      ctx.font = "10px 'IBM Plex Mono', monospace";
      ctx.textAlign = "right";
      ctx.fillText(`${val.toFixed(2)}%`, padLeft - 8, y + 3);
    }

    // X axis labels
    ctx.textAlign = "center";
    ctx.fillStyle = "#7C7C7C";
    for (const t of [0, 2, 5, 10]) {
      const x = xPos(t);
      ctx.fillText(t === 0 ? "TPM" : `${t}Y`, x, h - padBottom + 20);
    }

    // Curve line
    const lineColor = data.signal === "inverted" ? "#FF433D" : data.signal === "normal" ? "#3BBA13" : "#FF9900";
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 3;
    ctx.lineJoin = "round";
    ctx.beginPath();
    valid.forEach((p, i) => {
      const x = xPos(p.tenor_years);
      const y = yPos(p.value as number);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Points
    valid.forEach((p) => {
      const x = xPos(p.tenor_years);
      const y = yPos(p.value as number);

      // Outer circle
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
      ctx.fillStyle = lineColor;
      ctx.fill();

      // Inner circle
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = "#000000";
      ctx.fill();

      // Value label
      ctx.fillStyle = "#FFFFFF";
      ctx.font = "bold 12px 'IBM Plex Mono', monospace";
      ctx.textAlign = "center";
      ctx.fillText(`${(p.value as number).toFixed(2)}%`, x, y - 14);
    });

    // Title
    ctx.fillStyle = lineColor;
    ctx.font = "bold 11px 'IBM Plex Sans Condensed', sans-serif";
    ctx.textAlign = "left";
    const signalText = data.signal === "normal" ? "CURVA NORMAL" : data.signal === "inverted" ? "CURVA INVERTIDA" : "CURVA FLAT";
    ctx.fillText(signalText, padLeft + 5, padTop - 10);
  }, [data]);

  // ResizeObserver
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const ro = new ResizeObserver(() => {
      // Re-trigger render
      if (data) setData({ ...data });
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, [data]);

  if (!data) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <span className="text-bb-muted">Cargando curva...</span>
      </div>
    );
  }

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between">
        <span>CURVA DE RENDIMIENTO CHILE</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>TPM + BCP 2Y, 5Y, 10Y</span>
      </div>
      <div ref={containerRef} className="flex-1 min-h-0 relative">
        <canvas ref={canvasRef} className="absolute inset-0" />
      </div>
    </div>
  );
}
