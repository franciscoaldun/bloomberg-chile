"use client";

import { useState, useRef, useEffect } from "react";
import { searchCommands, COMMAND_MAP, type CommandAction } from "@/lib/commands";

type TabId = "main" | "analytics" | "cobre_fx" | "renta_fija";

interface CommandLineProps {
  open: boolean;
  onClose: () => void;
  onExecute: (action: CommandAction) => void;
}

export default function CommandLine({ open, onClose, onExecute }: CommandLineProps) {
  const [input, setInput] = useState("");
  const [results, setResults] = useState<CommandAction[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setInput("");
      setResults([]);
      setSelectedIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    setResults(searchCommands(input));
    setSelectedIdx(0);
  }, [input]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      onClose();
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIdx((i) => Math.min(i + 1, results.length - 1));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIdx((i) => Math.max(i - 1, 0));
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      // Try exact match first
      const exact = COMMAND_MAP[input.toUpperCase().trim()];
      if (exact) {
        onExecute(exact);
        onClose();
        return;
      }
      // Otherwise use selected from dropdown
      if (results[selectedIdx]) {
        onExecute(results[selectedIdx]);
        onClose();
        return;
      }
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]" onClick={onClose}>
      <div
        className="w-[560px] border border-bb-amber"
        style={{ background: "#0A0A0A" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Input bar */}
        <div className="flex items-center px-3 py-2 border-b border-bb-border">
          <span
            className="text-bb-amber font-bold mr-2"
            style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "11px" }}
          >
            CMD&gt;
          </span>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value.toUpperCase())}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent text-bb-white outline-none"
            style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "13px", caretColor: "#FF9900" }}
            placeholder="TPM, USD, COBRE, YIELD..."
            autoComplete="off"
            spellCheck={false}
          />
          <span
            className="text-bb-amber font-bold ml-2 cursor-pointer px-2 py-0.5 border border-bb-amber"
            style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "10px" }}
            onClick={() => {
              const exact = COMMAND_MAP[input.toUpperCase().trim()];
              if (exact) { onExecute(exact); onClose(); }
              else if (results[selectedIdx]) { onExecute(results[selectedIdx]); onClose(); }
            }}
          >
            &lt;GO&gt;
          </span>
        </div>

        {/* Results dropdown */}
        {results.length > 0 && (
          <div className="max-h-[300px] overflow-auto">
            {results.map((r, i) => (
              <div
                key={r.label + i}
                className={`flex items-center justify-between px-3 py-1.5 cursor-pointer ${
                  i === selectedIdx ? "bg-bb-amber/10" : ""
                }`}
                style={{ borderBottom: "1px solid #1A1A1A" }}
                onClick={() => { onExecute(r); onClose(); }}
                onMouseEnter={() => setSelectedIdx(i)}
              >
                <div className="flex items-center gap-3">
                  <span
                    className="text-bb-white font-bold"
                    style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "12px", minWidth: "100px" }}
                  >
                    {r.label}
                  </span>
                  <span className="text-bb-muted" style={{ fontSize: "11px" }}>
                    {r.description}
                  </span>
                </div>
                <span className="text-bb-blue" style={{ fontSize: "9px", fontFamily: "IBM Plex Sans Condensed, sans-serif" }}>
                  {r.tab === "main" ? "MERCADO" : r.tab === "analytics" ? "ANALYTICS" : r.tab === "cobre_fx" ? "COBRE & FX" : "RENTA FIJA"}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Help text */}
        <div className="px-3 py-1.5 flex items-center justify-between" style={{ borderTop: "1px solid #1A1A1A" }}>
          <span className="text-bb-muted" style={{ fontSize: "9px" }}>
            ESC cerrar | ENTER ejecutar | / abrir
          </span>
          <span className="text-bb-muted" style={{ fontSize: "9px" }}>
            1-4 cambiar tabs
          </span>
        </div>
      </div>
    </div>
  );
}
