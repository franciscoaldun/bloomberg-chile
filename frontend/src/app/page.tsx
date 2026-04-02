"use client";

import { useState, useCallback } from "react";
import { useMarketData } from "@/hooks/useMarketData";
import { useKeyboardNav } from "@/hooks/useKeyboardNav";
import Ticker from "@/components/Ticker";
import Mainboard1 from "@/components/Mainboard1";
import Mainboard2 from "@/components/Mainboard2";
import Mainboard3 from "@/components/Mainboard3";
import Mainboard4 from "@/components/Mainboard4";
import Mainboard5 from "@/components/Mainboard5";
import CommandLine from "@/components/CommandLine";
import StatusBar from "@/components/StatusBar";
import { formatTime } from "@/lib/format";
import type { CommandAction } from "@/lib/commands";

const TABS = [
  { id: "main", label: "MERCADO", key: "1" },
  { id: "analytics", label: "ANALYTICS", key: "2" },
  { id: "cobre_fx", label: "COBRE & FX", key: "3" },
  { id: "renta_fija", label: "RENTA FIJA", key: "4" },
  { id: "macro", label: "MACRO ANALYSIS", key: "5" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function Terminal() {
  const [activeTab, setActiveTab] = useState<TabId>("main");
  const [commandLineOpen, setCommandLineOpen] = useState(false);
  const {
    dashboard,
    health,
    selectedSeries,
    selectedId,
    selectSeries,
    loading,
    error,
    refresh,
  } = useMarketData(30000);

  useKeyboardNav({
    activeTab,
    setActiveTab,
    commandLineOpen,
    setCommandLineOpen,
  });

  const triggerRefresh = useCallback(() => {
    fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/refresh`,
      { method: "POST" }
    ).then(() => refresh());
  }, [refresh]);

  const handleCommand = useCallback(
    (action: CommandAction) => {
      if (action.special === "refresh") {
        triggerRefresh();
        return;
      }
      setActiveTab(action.tab as TabId);
      if (action.seriesId) {
        selectSeries(action.seriesId);
      }
    },
    [triggerRefresh, selectSeries]
  );

  if (loading && !dashboard) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-black">
        <div className="text-center">
          <div className="text-bb-amber text-2xl font-bold mb-2" style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif" }}>
            BLOOMBERG CHILE
          </div>
          <div className="text-bb-muted text-sm">Conectando con Banco Central de Chile...</div>
          <div className="mt-4 text-bb-blue animate-pulse">■ ■ ■</div>
        </div>
      </div>
    );
  }

  if (error && !dashboard) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-black">
        <div className="text-center">
          <div className="text-bb-red text-xl font-bold mb-2">ERROR DE CONEXION</div>
          <div className="text-bb-muted text-sm">{error}</div>
          <div className="text-bb-amber text-xs mt-4">
            Asegurate de que el backend esta corriendo en http://localhost:8000
          </div>
        </div>
      </div>
    );
  }

  const indicators = dashboard?.indicators ?? [];

  const lastUpdateStr = health?.last_updates
    ? formatTime(Object.values(health.last_updates).sort().pop() ?? null)
    : null;

  return (
    <div className="h-screen w-screen flex flex-col bg-black overflow-hidden">
      {/* Header con tabs */}
      <div className="flex items-center justify-between px-3 py-0 border-b border-bb-border" style={{ background: "#050505" }}>
        <div className="flex items-center gap-0">
          <span
            className="text-bb-amber font-bold tracking-wide pr-4"
            style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "14px" }}
          >
            BLOOMBERG CHILE
          </span>

          {/* Tabs */}
          <div className="flex items-center">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-1.5 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "text-bb-white border-bb-amber bg-black/50"
                    : "text-bb-muted border-transparent hover:text-bb-amber-dim"
                }`}
                style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", letterSpacing: "0.5px" }}
              >
                <span className="text-bb-muted mr-1" style={{ fontSize: "9px" }}>{tab.key}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setCommandLineOpen(true)}
            className="text-bb-muted hover:text-bb-amber transition-colors cursor-pointer"
            style={{ fontSize: "10px", fontFamily: "IBM Plex Mono, monospace" }}
            title="/ para abrir"
          >
            CMD&gt; _
          </button>
          <span className="text-bb-muted" style={{ fontSize: "10px" }}>
            DATOS: BANCO CENTRAL DE CHILE
          </span>
          {error && (
            <span className="text-bb-red" style={{ fontSize: "10px" }}>
              ● RECONECTANDO
            </span>
          )}
        </div>
      </div>

      {/* Ticker */}
      <Ticker indicators={indicators} />

      {/* Active board */}
      {activeTab === "main" ? (
        <Mainboard1
          indicators={indicators}
          selectedId={selectedId}
          selectedSeries={selectedSeries}
          onSelect={selectSeries}
        />
      ) : activeTab === "analytics" ? (
        <Mainboard2 />
      ) : activeTab === "cobre_fx" ? (
        <Mainboard3 />
      ) : activeTab === "renta_fija" ? (
        <Mainboard4 />
      ) : (
        <Mainboard5 />
      )}

      {/* Status Bar */}
      <StatusBar
        lastUpdate={lastUpdateStr}
        seriesCount={health?.series_count ?? 0}
        refresh={health?.refresh}
        onRefresh={triggerRefresh}
      />

      {/* Command Line overlay */}
      <CommandLine
        open={commandLineOpen}
        onClose={() => setCommandLineOpen(false)}
        onExecute={handleCommand}
      />
    </div>
  );
}
