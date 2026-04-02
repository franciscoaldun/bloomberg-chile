"use client";

import { useEffect, useState, useCallback } from "react";
import type { RefreshInfo } from "@/types/series";

interface StatusBarProps {
  lastUpdate: string | null;
  seriesCount: number;
  refresh?: RefreshInfo;
  onRefresh: () => void;
}

function formatCountdown(targetIso: string | null): string {
  if (!targetIso) return "--:--";
  const diff = Math.max(0, Math.floor((new Date(targetIso).getTime() - Date.now()) / 1000));
  const m = Math.floor(diff / 60);
  const s = diff % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function formatDateTime(isoStr: string | null): string {
  if (!isoStr) return "---";
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "---";
  }
}

export default function StatusBar({ lastUpdate, seriesCount, refresh, onRefresh }: StatusBarProps) {
  const [clock, setClock] = useState("");
  const [countdown, setCountdown] = useState("--:--");
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setClock(
        now.toLocaleDateString("es-CL", { weekday: "short", day: "2-digit", month: "short", year: "numeric" }) +
        "  " +
        now.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
      );
      setCountdown(formatCountdown(refresh?.next ?? null));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [refresh?.next]);

  const handleRefresh = useCallback(() => {
    if (refresh?.refreshing) return;
    onRefresh();
  }, [refresh?.refreshing, onRefresh]);

  return (
    <>
      {/* Panel de detalle (expandible) */}
      {showDetail && (
        <div
          className="border-t border-bb-border px-4 py-2"
          style={{ background: "#0a0a0a", fontSize: "10px", fontFamily: "IBM Plex Mono, monospace" }}
        >
          <div className="flex items-center gap-6 flex-wrap">
            <span className="text-bb-amber font-semibold">DATA PIPELINE</span>
            <span className="text-bb-muted">
              FUENTE: <span className="text-bb-white">API Banco Central de Chile (si.api.bcch.cl)</span>
            </span>
            <span className="text-bb-muted">
              FRECUENCIA: <span className="text-bb-white">AUTO CADA {(refresh?.interval_sec ?? 1800) / 60} MIN</span>
            </span>
            <span className="text-bb-muted">
              SERIES EN DB: <span className="text-bb-white">{seriesCount}</span>
            </span>
            <span className="text-bb-muted">
              ULTIMO REFRESH: <span className={refresh?.last_ok === false ? "text-bb-red" : "text-bb-white"}>
                {formatDateTime(refresh?.last ?? null)}
                {refresh?.last_ok === true && " OK"}
                {refresh?.last_ok === false && " ERROR"}
              </span>
            </span>
            <span className="text-bb-muted">
              SERIES ACT: <span className="text-bb-white">{refresh?.last_series ?? "---"}</span>
            </span>
            <span className="text-bb-muted">
              OBS: <span className="text-bb-white">{refresh?.last_obs?.toLocaleString("es-CL") ?? "---"}</span>
            </span>
          </div>
        </div>
      )}

      {/* Barra principal */}
      <div className="bb-status-bar flex justify-between items-center">
        <div className="flex items-center gap-4">
          <span className="text-bb-green">● CONECTADO</span>
          <span>SERIES: {seriesCount}</span>
          <span>FUENTE: BANCO CENTRAL DE CHILE</span>
          <button
            onClick={() => setShowDetail((v) => !v)}
            className="text-bb-muted hover:text-bb-amber transition-colors cursor-pointer"
            style={{ fontSize: "10px" }}
            title="Ver detalle del pipeline de datos"
          >
            [{showDetail ? "OCULTAR" : "PIPELINE"}]
          </button>
        </div>
        <div className="flex items-center gap-4">
          {/* Countdown al proximo refresh */}
          <span className="text-bb-muted" style={{ fontSize: "10px" }}>
            PROX: <span className="text-bb-blue">{countdown}</span>
          </span>

          {/* Boton de refresh manual */}
          <button
            onClick={handleRefresh}
            disabled={refresh?.refreshing}
            className={`px-2 py-0 border transition-colors cursor-pointer ${
              refresh?.refreshing
                ? "border-bb-muted text-bb-muted"
                : "border-bb-amber text-bb-amber hover:bg-bb-amber hover:text-black"
            }`}
            style={{ fontSize: "10px", fontFamily: "IBM Plex Sans Condensed, sans-serif", lineHeight: "16px" }}
            title="Actualizar datos manualmente desde el BCCh"
          >
            {refresh?.refreshing ? "ACTUALIZANDO..." : "REFRESH"}
          </button>

          <span>ULT. ACT: {lastUpdate ?? "---"}</span>
          <span className="text-bb-amber">{clock}</span>
        </div>
      </div>
    </>
  );
}
