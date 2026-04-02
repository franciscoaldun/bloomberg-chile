type TabId = "main" | "analytics" | "cobre_fx" | "renta_fija" | "macro";

export interface CommandAction {
  label: string;
  description: string;
  tab: TabId;
  seriesId?: string;
  special?: "refresh" | "help";
}

export const COMMAND_MAP: Record<string, CommandAction> = {
  // Tab 1 — MERCADO
  TPM:        { label: "TPM",         description: "Tasa de Politica Monetaria", tab: "main", seriesId: "tpm" },
  USD:        { label: "USD/CLP",     description: "Tipo de Cambio Dolar", tab: "main", seriesId: "usd_clp" },
  DOLAR:      { label: "USD/CLP",     description: "Tipo de Cambio Dolar", tab: "main", seriesId: "usd_clp" },
  IPSA:       { label: "IPSA",        description: "Indice Selectivo de Acciones", tab: "main", seriesId: "ipsa" },
  UF:         { label: "UF",          description: "Unidad de Fomento", tab: "main", seriesId: "uf" },
  IMACEC:     { label: "IMACEC",      description: "Indicador Mensual Actividad Economica", tab: "main", seriesId: "imacec" },
  IPC:        { label: "IPC",         description: "Variacion Mensual IPC", tab: "main", seriesId: "ipc_var" },
  DESEMPLEO:  { label: "DESEMPLEO",   description: "Tasa de Desocupacion", tab: "main", seriesId: "desempleo" },
  RESERVAS:   { label: "RESERVAS",    description: "Reservas Internacionales", tab: "main", seriesId: "reservas_intl" },
  DEUDA:      { label: "DEUDA/PIB",   description: "Deuda Bruta Gobierno Central", tab: "main", seriesId: "deuda_pib" },

  // Tab 2 — ANALYTICS
  CORR:       { label: "CORRELACIONES", description: "Matriz de Correlaciones", tab: "analytics" },
  SIM:        { label: "SIMULADOR",     description: "Simulador de Inversion", tab: "analytics" },
  BRIEFING:   { label: "BRIEFING",      description: "Briefing Economico IA", tab: "analytics" },

  // Tab 3 — COBRE & FX
  COBRE:      { label: "COBRE",       description: "Precio Cobre BML", tab: "cobre_fx", seriesId: "cobre" },
  COPPER:     { label: "COBRE",       description: "Precio Cobre BML", tab: "cobre_fx", seriesId: "cobre" },
  EUR:        { label: "EUR/CLP",     description: "Tipo de Cambio Euro", tab: "cobre_fx", seriesId: "eur_clp" },
  CNY:        { label: "CNY/CLP",     description: "Tipo de Cambio Yuan", tab: "cobre_fx", seriesId: "cny_clp" },
  BRL:        { label: "BRL/CLP",     description: "Tipo de Cambio Real", tab: "cobre_fx", seriesId: "brl_clp" },
  LATAM:      { label: "LATAM FX",    description: "Chile vs Latam FX", tab: "cobre_fx" },

  // Tab 4 — RENTA FIJA
  BCP2:       { label: "BCP 2Y",      description: "Bono Central 2 Anos", tab: "renta_fija", seriesId: "bcp_2y" },
  BCP5:       { label: "BCP 5Y",      description: "Bono Central 5 Anos", tab: "renta_fija", seriesId: "bcp_5y" },
  BCP10:      { label: "BCP 10Y",     description: "Bono Central 10 Anos", tab: "renta_fija", seriesId: "bcp_10y" },
  YIELD:      { label: "YIELD CURVE", description: "Curva de Rendimiento", tab: "renta_fija" },
  EOF:        { label: "EOF",         description: "Expectativas Operadores Financieros", tab: "renta_fija" },

  // Tab 5 — MACRO ANALYSIS
  MACRO:      { label: "MACRO",       description: "Analisis Macroeconomico Algoritmico", tab: "macro" },
  ANALISIS:   { label: "MACRO",       description: "Analisis Macroeconomico Algoritmico", tab: "macro" },

  // Especiales
  REFRESH:    { label: "REFRESH",     description: "Re-ingestar datos del BCCh", tab: "main", special: "refresh" },
  HELP:       { label: "HELP",        description: "Comandos disponibles", tab: "main", special: "help" },
};

export function searchCommands(query: string): CommandAction[] {
  const q = query.toUpperCase().trim();
  if (!q) return [];

  const results: CommandAction[] = [];
  const seen = new Set<string>();

  for (const [key, action] of Object.entries(COMMAND_MAP)) {
    if (key.startsWith(q) || action.label.includes(q) || action.description.toUpperCase().includes(q)) {
      if (!seen.has(action.label)) {
        seen.add(action.label);
        results.push(action);
      }
    }
  }

  return results.slice(0, 8);
}
