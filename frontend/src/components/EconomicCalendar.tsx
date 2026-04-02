"use client";

import { useMemo } from "react";
import { CALENDAR_2026, type CalendarEvent } from "@/lib/calendar-data";

function typeColor(type: CalendarEvent["type"]): string {
  switch (type) {
    case "reunion": return "text-bb-cyan";
    case "dato": return "text-bb-amber";
    case "publicacion": return "text-bb-blue";
  }
}

function typeLabel(type: CalendarEvent["type"]): string {
  switch (type) {
    case "reunion": return "RPM";
    case "dato": return "DATO";
    case "publicacion": return "PUB";
  }
}

function daysUntil(dateStr: string): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const target = new Date(dateStr);
  target.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

function countdownText(days: number): string {
  if (days === 0) return "HOY";
  if (days === 1) return "MANANA";
  if (days > 0) return `EN ${days}D`;
  return `HACE ${Math.abs(days)}D`;
}

export default function EconomicCalendar() {
  const events = useMemo(() => {
    const today = new Date().toISOString().split("T")[0];

    // Mostrar: últimos 3 pasados + próximos 10
    const past = CALENDAR_2026
      .filter((e) => e.date < today)
      .sort((a, b) => b.date.localeCompare(a.date))
      .slice(0, 3)
      .reverse();

    const upcoming = CALENDAR_2026
      .filter((e) => e.date >= today)
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(0, 10);

    return [...past, ...upcoming];
  }, []);

  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="bb-panel flex flex-col h-full">
      <div className="bb-panel-header flex justify-between">
        <span>CALENDARIO ECONOMICO</span>
        <span style={{ fontSize: "9px", opacity: 0.7 }}>2026</span>
      </div>
      <div className="flex-1 overflow-auto">
        {events.map((evt, i) => {
          const days = daysUntil(evt.date);
          const isPast = evt.date < today;
          const isToday = evt.date === today;
          const isNext = !isPast && !isToday && i === events.findIndex((e) => e.date >= today);

          return (
            <div
              key={`${evt.date}-${evt.name}`}
              className={`flex items-center px-3 py-1.5 ${isPast ? "opacity-40" : ""}`}
              style={{
                borderBottom: "1px solid #1A1A1A",
                background: isToday
                  ? "rgba(74, 246, 195, 0.08)"
                  : isNext
                  ? "rgba(11, 133, 223, 0.06)"
                  : "transparent",
              }}
            >
              {/* Type badge */}
              <span
                className={`${typeColor(evt.type)} font-bold mr-2`}
                style={{
                  fontFamily: "IBM Plex Sans Condensed, sans-serif",
                  fontSize: "8px",
                  minWidth: "28px",
                }}
              >
                {typeLabel(evt.type)}
              </span>

              {/* Date */}
              <span
                className="text-bb-muted mr-2"
                style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "9px", minWidth: "55px" }}
              >
                {evt.date.slice(5)}
              </span>

              {/* Name */}
              <span
                className="flex-1 text-bb-white"
                style={{ fontFamily: "IBM Plex Sans Condensed, sans-serif", fontSize: "10px" }}
              >
                {evt.name}
              </span>

              {/* Countdown */}
              <span
                className={`font-semibold ${
                  isToday ? "text-bb-cyan" : days > 0 ? "text-bb-muted" : "text-bb-muted"
                }`}
                style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: "9px", minWidth: "48px", textAlign: "right" }}
              >
                {countdownText(days)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
