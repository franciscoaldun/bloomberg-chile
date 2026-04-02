/**
 * Formateo de valores para display.
 * NOTA: esto es solo presentación visual. Los datos raw NO se modifican.
 */

export function formatValue(value: number | null, unit: string): string {
  if (value === null) return "---";

  switch (unit) {
    case "porcentaje":
    case "porcentaje_pib":
      return value.toFixed(2) + "%";
    case "clp_por_usd":
    case "clp_por_eur":
    case "clp_por_cny":
    case "clp_por_brl":
    case "clp_por_ars":
    case "clp_por_cop":
    case "clp_por_pen":
    case "clp_por_mxn":
      return "$" + value.toFixed(2);
    case "clp":
      return "$" + value.toLocaleString("es-CL", { maximumFractionDigits: 2 });
    case "usd_lb":
      return "US$" + value.toFixed(2) + "/lb";
    case "puntos":
      return value.toLocaleString("es-CL", { maximumFractionDigits: 2 });
    case "indice":
      return value.toFixed(2);
    case "millones_usd":
      return "US$" + value.toLocaleString("es-CL", { maximumFractionDigits: 0 }) + "M";
    case "miles_millones_clp":
      return "$" + value.toLocaleString("es-CL", { maximumFractionDigits: 0 }) + "MM";
    default:
      return value.toLocaleString("es-CL", { maximumFractionDigits: 2 });
  }
}

export function formatChange(change: number | null): string {
  if (change === null) return "---";
  const sign = change >= 0 ? "+" : "";
  return sign + change.toFixed(2);
}

export function formatChangePct(pct: number | null): string {
  if (pct === null) return "---";
  const sign = pct >= 0 ? "+" : "";
  return sign + pct.toFixed(2) + "%";
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "---";
  const [year, month, day] = dateStr.split("-");
  return `${day}/${month}/${year}`;
}

export function formatTime(isoStr: string | null): string {
  if (!isoStr) return "---";
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "---";
  }
}

export function shortName(id: string): string {
  const names: Record<string, string> = {
    tpm: "TPM",
    usd_clp: "USD/CLP",
    ipsa: "IPSA",
    uf: "UF",
    imacec: "IMACEC",
    desempleo: "DESEMPLEO",
    ipc_var: "IPC M/M",
    base_monetaria: "BASE MON",
    reservas_intl: "RESERVAS",
    export_mineras: "EXP MIN",
    deuda_pib: "DEUDA/PIB",
    cuenta_corriente: "CTA CTE",
    cobre: "COBRE",
    cobre_export: "EXP COBRE",
    bcp_2y: "BCP 2Y",
    bcp_5y: "BCP 5Y",
    bcp_10y: "BCP 10Y",
    eur_clp: "EUR/CLP",
    cny_clp: "CNY/CLP",
    brl_clp: "BRL/CLP",
    ars_clp: "ARS/CLP",
    cop_clp: "COP/CLP",
    pen_clp: "PEN/CLP",
    mxn_clp: "MXN/CLP",
    eof_5y_2m: "EOF 2M",
    eof_5y_11m: "EOF 11M",
    eof_5y_23m: "EOF 23M",
  };
  return names[id] || id.toUpperCase();
}
