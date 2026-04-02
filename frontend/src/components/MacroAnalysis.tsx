"use client";

import { useEffect, useState } from "react";
import { fetchMacroSynthesis } from "@/lib/api";

/* ═══════════════════════════════════════════════════════════════════ */
/*  TYPES                                                             */
/* ═══════════════════════════════════════════════════════════════════ */

interface ScoreBreakdown {
  category: string;
  signal: string;
  severity: string;
  points: number;
}

interface MacroScore {
  value: number;
  raw: number;
  label: string;
  description: string;
  color: string;
  contradiction_penalty: number;
  breakdown: ScoreBreakdown[];
}

interface Section {
  id: string;
  title: string;
  subtitle: string;
  signal: string;
  signal_label: string;
  narrative: string;
  insights_count: number;
  categories: string[];
  signal_distribution: Record<string, number>;
}

interface ContradictionItem {
  name: string;
  severity: string;
  narrative: string;
  simple: string;
  between: string;
}

interface Contradictions {
  title: string;
  narrative: string;
  count: number;
  high_severity: number;
  medium_severity: number;
  items: ContradictionItem[];
}

interface Recommendation {
  priority: string;
  text: string;
  based_on: string[];
  action: string;
}

interface SignalSummary {
  total_insights: number;
  bullish: number;
  bearish: number;
  risk: number;
  safe: number;
  neutral: number;
}

interface Metadata {
  generated: string;
  data_as_of: string;
  insights_analyzed: number;
  contradictions_found: number;
  sections_generated: number;
  recommendations_generated: number;
  derived: boolean;
  method: string;
  note: string;
}

interface SynthesisData {
  executive_summary: string;
  macro_score: MacroScore;
  sections: Section[];
  contradictions: Contradictions;
  recommendations: Recommendation[];
  signal_summary: SignalSummary;
  metadata: Metadata;
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  HELPERS                                                           */
/* ═══════════════════════════════════════════════════════════════════ */

function signalColor(signal: string): string {
  switch (signal) {
    case "bullish": return "#3BBA13";
    case "bearish": return "#FF433D";
    case "risk": return "#FF9900";
    case "safe": return "#4AF6C3";
    default: return "#7C7C7C";
  }
}

function signalIcon(signal: string): string {
  switch (signal) {
    case "bullish":
    case "safe": return "\u25B2";
    case "bearish":
    case "risk": return "\u25BC";
    default: return "\u25CF";
  }
}

function severityBorderColor(severity: string): string {
  switch (severity) {
    case "alta": return "#FF433D";
    case "media": return "#FF9900";
    default: return "#0B85DF";
  }
}

function priorityStyle(priority: string): { bg: string; text: string; border: string } {
  switch (priority) {
    case "ALTA": return { bg: "rgba(255,67,61,0.08)", text: "#FF433D", border: "#FF433D" };
    case "MEDIA": return { bg: "rgba(255,153,0,0.05)", text: "#FF9900", border: "#FF9900" };
    default: return { bg: "transparent", text: "#0B85DF", border: "#0B85DF" };
  }
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  SCORE GAUGE                                                       */
/* ═══════════════════════════════════════════════════════════════════ */

function ScoreGauge({ score }: { score: MacroScore }) {
  // Map -100..+100 to 0..100% for the bar
  const pct = (score.value + 100) / 2;
  const barWidth = Math.max(2, Math.min(98, pct));

  return (
    <div className="flex items-center gap-4">
      {/* Score number */}
      <div className="text-center" style={{ minWidth: 90 }}>
        <div
          className="font-bold"
          style={{
            fontFamily: "IBM Plex Mono, monospace",
            fontSize: 36,
            color: score.color,
            lineHeight: 1,
          }}
        >
          {score.value > 0 ? "+" : ""}{score.value}
        </div>
        <div
          className="font-bold mt-1"
          style={{
            fontFamily: "IBM Plex Sans Condensed, sans-serif",
            fontSize: 11,
            color: score.color,
            letterSpacing: 2,
          }}
        >
          {score.label}
        </div>
      </div>

      {/* Gauge bar */}
      <div className="flex-1">
        <div
          className="relative w-full"
          style={{ height: 8, background: "#1A1A1A", borderRadius: 1 }}
        >
          {/* Gradient: red → amber → green */}
          <div
            className="absolute inset-0"
            style={{
              background: "linear-gradient(to right, #FF433D 0%, #FF9900 40%, #FF9900 60%, #3BBA13 100%)",
              opacity: 0.15,
              borderRadius: 1,
            }}
          />
          {/* Needle */}
          <div
            className="absolute top-0 h-full"
            style={{
              left: `${barWidth}%`,
              width: 3,
              background: score.color,
              transform: "translateX(-50%)",
              boxShadow: `0 0 6px ${score.color}`,
            }}
          />
        </div>
        {/* Scale labels */}
        <div className="flex justify-between mt-1">
          <span style={{ fontSize: 8, color: "#FF433D" }}>-100 CRISIS</span>
          <span style={{ fontSize: 8, color: "#FF9900" }}>0 NEUTRAL</span>
          <span style={{ fontSize: 8, color: "#3BBA13" }}>+100 EXPANSION</span>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  SIGNAL DISTRIBUTION BAR                                           */
/* ═══════════════════════════════════════════════════════════════════ */

function SignalBar({ summary }: { summary: SignalSummary }) {
  const total = summary.total_insights;
  if (total === 0) return null;

  const segments = [
    { key: "bullish", count: summary.bullish, color: "#3BBA13", label: "ALCISTA" },
    { key: "safe", count: summary.safe, color: "#4AF6C3", label: "SEGURO" },
    { key: "neutral", count: summary.neutral, color: "#7C7C7C", label: "NEUTRAL" },
    { key: "risk", count: summary.risk, color: "#FF9900", label: "RIESGO" },
    { key: "bearish", count: summary.bearish, color: "#FF433D", label: "BAJISTA" },
  ].filter(s => s.count > 0);

  return (
    <div>
      {/* Bar */}
      <div className="flex" style={{ height: 6, borderRadius: 1, overflow: "hidden" }}>
        {segments.map(s => (
          <div
            key={s.key}
            style={{ width: `${(s.count / total) * 100}%`, background: s.color }}
          />
        ))}
      </div>
      {/* Labels */}
      <div className="flex items-center gap-3 mt-1.5">
        {segments.map(s => (
          <span key={s.key} className="flex items-center gap-1" style={{ fontSize: 9 }}>
            <span
              className="inline-block"
              style={{ width: 6, height: 6, background: s.color }}
            />
            <span style={{ color: s.color, fontFamily: "IBM Plex Sans Condensed, sans-serif" }}>
              {s.count} {s.label}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  SECTION CARD                                                      */
/* ═══════════════════════════════════════════════════════════════════ */

function SectionCard({
  section,
  isExpanded,
  onToggle,
}: {
  section: Section;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const dist = section.signal_distribution;
  const total = Object.values(dist).reduce((a, b) => a + b, 0);

  return (
    <div style={{ borderBottom: "1px solid #1A1A1A" }}>
      {/* Header — always visible */}
      <button
        onClick={onToggle}
        className="w-full text-left px-4 py-3 flex items-center justify-between hover:bg-[#0A0A0A] transition-colors"
      >
        <div className="flex items-center gap-3">
          <span
            style={{
              fontSize: 14,
              color: "#FFFFFF",
              fontFamily: "IBM Plex Sans Condensed, sans-serif",
              fontWeight: 700,
            }}
          >
            {section.title}
          </span>
          <span
            style={{
              fontSize: 9,
              color: "#7C7C7C",
              fontFamily: "IBM Plex Sans Condensed, sans-serif",
            }}
          >
            {section.subtitle}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span
            className="px-2 py-0.5 font-bold"
            style={{
              fontSize: 10,
              color: signalColor(section.signal),
              background: `${signalColor(section.signal)}15`,
              fontFamily: "IBM Plex Sans Condensed, sans-serif",
              letterSpacing: 1,
            }}
          >
            {signalIcon(section.signal)} {section.signal_label}
          </span>
          <span
            style={{
              fontSize: 9,
              color: "#7C7C7C",
              fontFamily: "IBM Plex Mono, monospace",
            }}
          >
            {total} indicadores
          </span>
          <span style={{ fontSize: 10, color: "#7C7C7C" }}>
            {isExpanded ? "\u25B4" : "\u25BE"}
          </span>
        </div>
      </button>

      {/* Expanded narrative */}
      {isExpanded && (
        <div className="px-4 pb-4">
          {/* Mini signal bar for this section */}
          <div className="mb-3">
            <div className="flex" style={{ height: 3, borderRadius: 1, overflow: "hidden" }}>
              {(["bullish", "safe", "neutral", "risk", "bearish"] as const).map(sig => {
                const count = dist[sig] || 0;
                if (count === 0) return null;
                return (
                  <div
                    key={sig}
                    style={{ width: `${(count / total) * 100}%`, background: signalColor(sig) }}
                  />
                );
              })}
            </div>
          </div>

          {/* Narrative text */}
          <div
            style={{
              fontSize: 12,
              lineHeight: 1.7,
              color: "#CCCCCC",
              fontFamily: "IBM Plex Sans, sans-serif",
            }}
          >
            {section.narrative}
          </div>

          {/* Categories tags */}
          <div className="flex flex-wrap gap-1 mt-3">
            {section.categories.map(cat => (
              <span
                key={cat}
                className="px-1.5 py-0.5"
                style={{
                  fontSize: 8,
                  color: "#7C7C7C",
                  background: "rgba(124,124,124,0.08)",
                  fontFamily: "IBM Plex Mono, monospace",
                }}
              >
                {cat}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  CONTRADICTION CARD                                                */
/* ═══════════════════════════════════════════════════════════════════ */

function ContradictionCard({
  item,
  showSimple,
  onToggleSimple,
}: {
  item: ContradictionItem;
  showSimple: boolean;
  onToggleSimple: () => void;
}) {
  return (
    <div
      className="px-4 py-3"
      style={{
        borderLeft: `3px solid ${severityBorderColor(item.severity)}`,
        borderBottom: "1px solid #1A1A1A",
        background: item.severity === "alta" ? "rgba(255,67,61,0.03)" : "transparent",
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span
            className="font-bold px-1.5 py-0.5"
            style={{
              fontSize: 8,
              background: severityBorderColor(item.severity),
              color: "#000",
              fontFamily: "IBM Plex Sans Condensed, sans-serif",
            }}
          >
            {item.severity.toUpperCase()}
          </span>
          <span
            className="font-bold"
            style={{
              fontSize: 13,
              color: "#FFFFFF",
              fontFamily: "IBM Plex Sans Condensed, sans-serif",
            }}
          >
            {item.name}
          </span>
        </div>
        <span
          style={{
            fontSize: 9,
            color: "#7C7C7C",
            fontFamily: "IBM Plex Mono, monospace",
          }}
        >
          {item.between}
        </span>
      </div>

      {/* Technical narrative */}
      <div
        style={{
          fontSize: 11,
          lineHeight: 1.6,
          color: "#AAAAAA",
          fontFamily: "IBM Plex Sans, sans-serif",
        }}
      >
        {item.narrative}
      </div>

      {/* Simple explanation toggle */}
      <button
        onClick={onToggleSimple}
        className="mt-2 transition-colors"
        style={{
          fontSize: 10,
          color: "#4AF6C3",
          fontFamily: "IBM Plex Sans Condensed, sans-serif",
          fontWeight: 600,
          letterSpacing: 0.5,
        }}
      >
        {showSimple ? "\u25BC OCULTAR" : "\u25B6 EXPLICACION SIMPLE"}
      </button>

      {showSimple && (
        <div
          className="mt-2 px-3 py-2.5"
          style={{
            background: "rgba(74,246,195,0.04)",
            borderLeft: "2px solid #4AF6C3",
            fontSize: 12,
            lineHeight: 1.6,
            color: "#CCCCCC",
            fontFamily: "IBM Plex Sans, sans-serif",
          }}
        >
          {item.simple}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  MAIN COMPONENT                                                    */
/* ═══════════════════════════════════════════════════════════════════ */

export default function MacroAnalysis() {
  const [data, setData] = useState<SynthesisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [expandedSimple, setExpandedSimple] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<"report" | "score" | "recs">("report");

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchMacroSynthesis()
      .then((d) => {
        setData(d);
        // Auto-expand first section
        if (d.sections?.length > 0) {
          setExpandedSections(new Set([d.sections[0].id]));
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function toggleSection(id: string) {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleSimple(id: string) {
    setExpandedSimple((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  /* Loading state */
  if (loading) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <div className="text-center">
          <div
            className="font-bold mb-2"
            style={{
              fontFamily: "IBM Plex Sans Condensed, sans-serif",
              fontSize: 14,
              color: "#FF9900",
            }}
          >
            PROCESANDO SINTESIS MACROECONOMICA
          </div>
          <div className="text-bb-muted animate-pulse" style={{ fontSize: 10 }}>
            32 indicadores &middot; 7 etapas &middot; 100% algoritmico
          </div>
        </div>
      </div>
    );
  }

  /* Error state */
  if (error || !data) {
    return (
      <div className="bb-panel h-full flex items-center justify-center">
        <div className="text-center">
          <div style={{ fontSize: 13, color: "#FF433D" }}>Error: {error || "Sin datos"}</div>
          <button
            onClick={() => {
              setLoading(true);
              setError(null);
              fetchMacroSynthesis()
                .then(setData)
                .catch((e) => setError(e.message))
                .finally(() => setLoading(false));
            }}
            className="mt-2 text-bb-cyan"
            style={{ fontSize: 10 }}
          >
            REINTENTAR
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "report" as const, label: "INFORME" },
    { id: "score" as const, label: "SCORE" },
    { id: "recs" as const, label: "RECOMENDACIONES" },
  ];

  return (
    <div className="bb-panel flex flex-col h-full">
      {/* ─── HEADER ─── */}
      <div className="bb-panel-header flex justify-between items-center">
        <span>SINTESIS MACROECONOMICA CHILE</span>
        <div className="flex items-center gap-3">
          <span style={{ fontSize: 9, opacity: 0.7 }}>
            Datos al {data.metadata.data_as_of} &middot; Generado {data.metadata.generated}
          </span>
          <button
            onClick={() => {
              setLoading(true);
              fetchMacroSynthesis()
                .then(setData)
                .finally(() => setLoading(false));
            }}
            className="text-bb-blue hover:text-bb-cyan transition-colors"
            style={{ fontSize: 9, fontFamily: "IBM Plex Sans Condensed, sans-serif" }}
          >
            ACTUALIZAR
          </button>
        </div>
      </div>

      {/* ─── SCORE BAR ─── */}
      <div
        className="px-4 py-3"
        style={{ borderBottom: "1px solid #333333", background: "#050505" }}
      >
        <ScoreGauge score={data.macro_score} />
      </div>

      {/* ─── INNER TABS ─── */}
      <div
        className="flex items-center gap-0"
        style={{ borderBottom: "1px solid #333333", background: "#0A0A0A" }}
      >
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className="px-4 py-2 transition-colors"
            style={{
              fontSize: 10,
              fontFamily: "IBM Plex Sans Condensed, sans-serif",
              fontWeight: activeTab === t.id ? 700 : 400,
              color: activeTab === t.id ? "#FF9900" : "#7C7C7C",
              borderBottom: activeTab === t.id ? "2px solid #FF9900" : "2px solid transparent",
              letterSpacing: 1,
            }}
          >
            {t.label}
          </button>
        ))}

        {/* Signal summary inline */}
        <div className="ml-auto pr-4">
          <SignalBar summary={data.signal_summary} />
        </div>
      </div>

      {/* ─── CONTENT ─── */}
      <div className="flex-1 overflow-auto">
        {/* ═══ TAB: INFORME ═══ */}
        {activeTab === "report" && (
          <>
            {/* Executive Summary */}
            <div
              className="px-4 py-4"
              style={{
                borderBottom: "1px solid #333333",
                background: "rgba(255,153,0,0.02)",
              }}
            >
              <div
                className="mb-2 font-bold"
                style={{
                  fontSize: 10,
                  color: "#FF9900",
                  fontFamily: "IBM Plex Sans Condensed, sans-serif",
                  letterSpacing: 1,
                }}
              >
                RESUMEN EJECUTIVO
              </div>
              <div
                style={{
                  fontSize: 13,
                  lineHeight: 1.7,
                  color: "#DDDDDD",
                  fontFamily: "IBM Plex Sans, sans-serif",
                }}
              >
                {data.executive_summary}
              </div>
            </div>

            {/* Sections */}
            <div>
              <div
                className="px-4 py-2 font-bold"
                style={{
                  fontSize: 10,
                  color: "#0B85DF",
                  fontFamily: "IBM Plex Sans Condensed, sans-serif",
                  letterSpacing: 1,
                  background: "#0A0A0A",
                  borderBottom: "1px solid #1A1A1A",
                }}
              >
                DIAGNOSTICO POR SECTOR ({data.sections.length} secciones)
              </div>

              {data.sections.map((section) => (
                <SectionCard
                  key={section.id}
                  section={section}
                  isExpanded={expandedSections.has(section.id)}
                  onToggle={() => toggleSection(section.id)}
                />
              ))}
            </div>

            {/* Contradictions */}
            {data.contradictions.count > 0 && (
              <div>
                <div
                  className="px-4 py-2 font-bold flex items-center justify-between"
                  style={{
                    fontSize: 10,
                    color: "#FF433D",
                    fontFamily: "IBM Plex Sans Condensed, sans-serif",
                    letterSpacing: 1,
                    background: "#0A0A0A",
                    borderBottom: "1px solid #1A1A1A",
                    borderTop: "1px solid #333333",
                  }}
                >
                  <span>{data.contradictions.title}</span>
                  <span style={{ fontSize: 9, color: "#7C7C7C", fontWeight: 400 }}>
                    {data.contradictions.high_severity} alta &middot;{" "}
                    {data.contradictions.medium_severity} media &middot;{" "}
                    {data.contradictions.count - data.contradictions.high_severity - data.contradictions.medium_severity} baja
                  </span>
                </div>

                {/* Contradictions opening narrative */}
                <div
                  className="px-4 py-3"
                  style={{
                    fontSize: 11,
                    lineHeight: 1.6,
                    color: "#AAAAAA",
                    fontFamily: "IBM Plex Sans, sans-serif",
                    borderBottom: "1px solid #1A1A1A",
                  }}
                >
                  {data.contradictions.narrative}
                </div>

                {data.contradictions.items.map((item) => (
                  <ContradictionCard
                    key={item.name}
                    item={item}
                    showSimple={expandedSimple.has(item.name)}
                    onToggleSimple={() => toggleSimple(item.name)}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {/* ═══ TAB: SCORE DETAIL ═══ */}
        {activeTab === "score" && (
          <div className="px-4 py-4">
            <div className="mb-4">
              <div
                className="font-bold mb-1"
                style={{
                  fontSize: 10,
                  color: "#0B85DF",
                  fontFamily: "IBM Plex Sans Condensed, sans-serif",
                  letterSpacing: 1,
                }}
              >
                METODOLOGIA DE CALCULO
              </div>
              <div style={{ fontSize: 11, color: "#AAAAAA", lineHeight: 1.6 }}>
                Cada indicador contribuye puntos segun su senal (alcista/bajista/riesgo/seguro) y severidad
                (info/alerta/critico). Las contradicciones detectadas penalizan el score total.
                Rango: -100 (crisis) a +100 (expansion).
              </div>
            </div>

            {/* Score summary */}
            <div
              className="flex items-center gap-6 mb-4 px-4 py-3"
              style={{ background: "#0A0A0A", border: "1px solid #1A1A1A" }}
            >
              <div className="text-center">
                <div style={{ fontSize: 9, color: "#7C7C7C" }}>SCORE BRUTO</div>
                <div
                  className="font-bold"
                  style={{
                    fontSize: 20,
                    color: "#FFFFFF",
                    fontFamily: "IBM Plex Mono, monospace",
                  }}
                >
                  {data.macro_score.raw > 0 ? "+" : ""}{data.macro_score.raw}
                </div>
              </div>
              <div className="text-center">
                <div style={{ fontSize: 9, color: "#7C7C7C" }}>PENALIZACION</div>
                <div
                  className="font-bold"
                  style={{
                    fontSize: 20,
                    color: "#FF433D",
                    fontFamily: "IBM Plex Mono, monospace",
                  }}
                >
                  -{data.macro_score.contradiction_penalty}
                </div>
              </div>
              <div className="text-center">
                <div style={{ fontSize: 9, color: "#7C7C7C" }}>SCORE FINAL</div>
                <div
                  className="font-bold"
                  style={{
                    fontSize: 20,
                    color: data.macro_score.color,
                    fontFamily: "IBM Plex Mono, monospace",
                  }}
                >
                  {data.macro_score.value > 0 ? "+" : ""}{data.macro_score.value}/100
                </div>
              </div>
              <div className="text-center">
                <div style={{ fontSize: 9, color: "#7C7C7C" }}>CONTRADICCIONES</div>
                <div
                  className="font-bold"
                  style={{
                    fontSize: 20,
                    color: "#FF9900",
                    fontFamily: "IBM Plex Mono, monospace",
                  }}
                >
                  {data.contradictions.count}
                </div>
              </div>
            </div>

            {/* Breakdown table */}
            <div
              className="font-bold mb-2"
              style={{
                fontSize: 10,
                color: "#0B85DF",
                fontFamily: "IBM Plex Sans Condensed, sans-serif",
                letterSpacing: 1,
              }}
            >
              DESGLOSE POR INDICADOR ({data.macro_score.breakdown.length} contribuyentes)
            </div>

            <table className="w-full" style={{ fontSize: 11, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #333333" }}>
                  <th
                    className="text-left py-1.5 px-2"
                    style={{ fontSize: 9, color: "#7C7C7C", fontFamily: "IBM Plex Sans Condensed, sans-serif" }}
                  >
                    CATEGORIA
                  </th>
                  <th
                    className="text-center py-1.5 px-2"
                    style={{ fontSize: 9, color: "#7C7C7C", fontFamily: "IBM Plex Sans Condensed, sans-serif" }}
                  >
                    SENAL
                  </th>
                  <th
                    className="text-center py-1.5 px-2"
                    style={{ fontSize: 9, color: "#7C7C7C", fontFamily: "IBM Plex Sans Condensed, sans-serif" }}
                  >
                    SEVERIDAD
                  </th>
                  <th
                    className="text-right py-1.5 px-2"
                    style={{ fontSize: 9, color: "#7C7C7C", fontFamily: "IBM Plex Sans Condensed, sans-serif" }}
                  >
                    PUNTOS
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.macro_score.breakdown.map((b, i) => (
                  <tr
                    key={i}
                    style={{
                      borderBottom: "1px solid #1A1A1A",
                      background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)",
                    }}
                  >
                    <td
                      className="py-1.5 px-2"
                      style={{ fontFamily: "IBM Plex Mono, monospace", color: "#CCCCCC" }}
                    >
                      {b.category}
                    </td>
                    <td className="text-center py-1.5 px-2">
                      <span style={{ color: signalColor(b.signal), fontSize: 10 }}>
                        {signalIcon(b.signal)} {b.signal.toUpperCase()}
                      </span>
                    </td>
                    <td
                      className="text-center py-1.5 px-2"
                      style={{ color: "#7C7C7C" }}
                    >
                      {b.severity}
                    </td>
                    <td
                      className="text-right py-1.5 px-2 font-bold"
                      style={{
                        fontFamily: "IBM Plex Mono, monospace",
                        color: b.points > 0 ? "#3BBA13" : b.points < 0 ? "#FF433D" : "#7C7C7C",
                      }}
                    >
                      {b.points > 0 ? "+" : ""}{b.points}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ═══ TAB: RECOMENDACIONES ═══ */}
        {activeTab === "recs" && (
          <div>
            <div
              className="px-4 py-3"
              style={{
                fontSize: 11,
                color: "#AAAAAA",
                fontFamily: "IBM Plex Sans, sans-serif",
                borderBottom: "1px solid #1A1A1A",
                lineHeight: 1.5,
              }}
            >
              {data.recommendations.length} recomendaciones de monitoreo ordenadas por prioridad.
              Cada recomendacion esta vinculada a los indicadores que la generan.
            </div>

            {data.recommendations.map((rec, i) => {
              const style = priorityStyle(rec.priority);
              return (
                <div
                  key={i}
                  className="px-4 py-3"
                  style={{
                    borderLeft: `3px solid ${style.border}`,
                    borderBottom: "1px solid #1A1A1A",
                    background: style.bg,
                  }}
                >
                  {/* Priority + action */}
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className="font-bold px-1.5 py-0.5"
                      style={{
                        fontSize: 8,
                        background: style.text,
                        color: "#000",
                        fontFamily: "IBM Plex Sans Condensed, sans-serif",
                      }}
                    >
                      {rec.priority}
                    </span>
                    <span
                      style={{
                        fontSize: 9,
                        color: "#7C7C7C",
                        fontFamily: "IBM Plex Sans Condensed, sans-serif",
                      }}
                    >
                      {rec.action}
                    </span>
                  </div>

                  {/* Text */}
                  <div
                    style={{
                      fontSize: 12,
                      lineHeight: 1.6,
                      color: "#CCCCCC",
                      fontFamily: "IBM Plex Sans, sans-serif",
                    }}
                  >
                    {rec.text}
                  </div>

                  {/* Based on tags */}
                  <div className="flex items-center gap-1 mt-2">
                    <span style={{ fontSize: 8, color: "#7C7C7C" }}>BASADO EN:</span>
                    {rec.based_on.map((cat) => (
                      <span
                        key={cat}
                        className="px-1.5 py-0.5"
                        style={{
                          fontSize: 8,
                          color: "#7C7C7C",
                          background: "rgba(124,124,124,0.1)",
                          fontFamily: "IBM Plex Mono, monospace",
                        }}
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ─── FOOTER ─── */}
        <div
          className="px-4 py-3"
          style={{ borderTop: "1px solid #333333", background: "#050505" }}
        >
          <div
            className="text-bb-muted flex items-center justify-between"
            style={{ fontSize: 9, lineHeight: 1.5 }}
          >
            <span>
              {data.metadata.note}
            </span>
            <span style={{ fontFamily: "IBM Plex Mono, monospace" }}>
              {data.metadata.method} &middot; {data.metadata.insights_analyzed} insights &middot;{" "}
              {data.metadata.contradictions_found} contradicciones &middot;{" "}
              {data.metadata.recommendations_generated} recomendaciones
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
