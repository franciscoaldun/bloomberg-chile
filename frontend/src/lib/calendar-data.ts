export interface CalendarEvent {
  date: string; // YYYY-MM-DD
  type: "reunion" | "dato" | "publicacion";
  name: string;
}

// Calendario BCCh 2026 — fechas públicas
// Fuente: https://www.bcentral.cl/reuniones-de-politica-monetaria
export const CALENDAR_2026: CalendarEvent[] = [
  // Reuniones de Política Monetaria BCCh 2026
  { date: "2026-01-28", type: "reunion", name: "RPM BCCh Enero" },
  { date: "2026-03-25", type: "reunion", name: "RPM BCCh Marzo" },
  { date: "2026-05-06", type: "reunion", name: "RPM BCCh Mayo" },
  { date: "2026-06-17", type: "reunion", name: "RPM BCCh Junio" },
  { date: "2026-07-29", type: "reunion", name: "RPM BCCh Julio" },
  { date: "2026-09-02", type: "reunion", name: "RPM BCCh Septiembre" },
  { date: "2026-10-14", type: "reunion", name: "RPM BCCh Octubre" },
  { date: "2026-12-16", type: "reunion", name: "RPM BCCh Diciembre" },

  // IPC (publicación INE ~día 8 del mes siguiente)
  { date: "2026-01-08", type: "dato", name: "IPC Diciembre 2025" },
  { date: "2026-02-06", type: "dato", name: "IPC Enero 2026" },
  { date: "2026-03-06", type: "dato", name: "IPC Febrero 2026" },
  { date: "2026-04-08", type: "dato", name: "IPC Marzo 2026" },
  { date: "2026-05-08", type: "dato", name: "IPC Abril 2026" },
  { date: "2026-06-05", type: "dato", name: "IPC Mayo 2026" },
  { date: "2026-07-08", type: "dato", name: "IPC Junio 2026" },
  { date: "2026-08-07", type: "dato", name: "IPC Julio 2026" },
  { date: "2026-09-08", type: "dato", name: "IPC Agosto 2026" },
  { date: "2026-10-08", type: "dato", name: "IPC Septiembre 2026" },
  { date: "2026-11-06", type: "dato", name: "IPC Octubre 2026" },
  { date: "2026-12-08", type: "dato", name: "IPC Noviembre 2026" },

  // IMACEC (publicación BCCh ~primer viernes del 2do mes)
  { date: "2026-01-05", type: "dato", name: "IMACEC Noviembre 2025" },
  { date: "2026-02-05", type: "dato", name: "IMACEC Diciembre 2025" },
  { date: "2026-03-05", type: "dato", name: "IMACEC Enero 2026" },
  { date: "2026-04-06", type: "dato", name: "IMACEC Febrero 2026" },
  { date: "2026-05-05", type: "dato", name: "IMACEC Marzo 2026" },
  { date: "2026-06-04", type: "dato", name: "IMACEC Abril 2026" },
  { date: "2026-07-06", type: "dato", name: "IMACEC Mayo 2026" },
  { date: "2026-08-05", type: "dato", name: "IMACEC Junio 2026" },
  { date: "2026-09-04", type: "dato", name: "IMACEC Julio 2026" },
  { date: "2026-10-05", type: "dato", name: "IMACEC Agosto 2026" },
  { date: "2026-11-05", type: "dato", name: "IMACEC Septiembre 2026" },
  { date: "2026-12-04", type: "dato", name: "IMACEC Octubre 2026" },

  // IPoM (Informe de Política Monetaria)
  { date: "2026-03-26", type: "publicacion", name: "IPoM Marzo 2026" },
  { date: "2026-06-18", type: "publicacion", name: "IPoM Junio 2026" },
  { date: "2026-09-03", type: "publicacion", name: "IPoM Septiembre 2026" },
  { date: "2026-12-17", type: "publicacion", name: "IPoM Diciembre 2026" },

  // IEF (Informe de Estabilidad Financiera)
  { date: "2026-05-07", type: "publicacion", name: "IEF 1er Semestre 2026" },
  { date: "2026-11-05", type: "publicacion", name: "IEF 2do Semestre 2026" },
];
