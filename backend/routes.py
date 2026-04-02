"""
Endpoints de la API.

Todos los datos que salen de aquí son:
- Raw: tal cual están en la DB (que a su vez es parseo mecánico del BCCh)
- Derivados: claramente etiquetados como "derived" (cambios %, etc.)
"""

from datetime import date, timedelta
from fastapi import APIRouter, Query
from config import SERIES_CATALOG
import storage
import analysis_engine
import synthesis_engine

# IDs de series FX Latam para el endpoint /api/fx/latam
FX_LATAM_IDS = ["usd_clp", "brl_clp", "ars_clp", "cop_clp", "pen_clp", "mxn_clp"]
FX_MONITOR_IDS = ["usd_clp", "eur_clp", "cny_clp", "brl_clp", "ars_clp", "cop_clp", "pen_clp", "mxn_clp"]
EOF_IDS = ["eof_5y_2m", "eof_5y_11m", "eof_5y_23m"]

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    """Status del sistema con info de auto-refresh."""
    from main import refresh_state

    meta = storage.get_all_meta()
    last_updates = {
        m["panel_id"]: m["last_updated"]
        for m in meta
        if m["last_updated"]
    }
    return {
        "status": "ok",
        "series_count": len(meta),
        "last_updates": last_updates,
        "refresh": {
            "last": refresh_state["last_refresh"],
            "last_ok": refresh_state["last_refresh_ok"],
            "last_series": refresh_state["last_refresh_series"],
            "last_obs": refresh_state["last_refresh_obs"],
            "next": refresh_state["next_refresh"],
            "refreshing": refresh_state["refreshing"],
            "interval_sec": refresh_state["interval_sec"],
        },
    }


@router.get("/dashboard")
def dashboard():
    """
    Todos los indicadores principales con último valor + cambio.
    El campo 'change' y 'change_pct' son DERIVADOS (calculados por nosotros).
    """
    indicators = []

    for panel_id, info in SERIES_CATALOG.items():
        bcch_id = info["bcch_id"]
        latest = storage.get_latest_value(bcch_id)

        if not latest:
            indicators.append({
                "id": panel_id,
                "name": info["name_es"],
                "unit": info["unit"],
                "frequency": info["frequency"],
                "value": None,
                "date": None,
                "change": None,
                "change_pct": None,
                "source": "bcch",
            })
            continue

        # Calcular cambio respecto al valor anterior (DERIVADO)
        prev = storage.get_previous_value(bcch_id, latest["date"])
        change = None
        change_pct = None
        if prev and prev["value"] and prev["value"] != 0:
            change = latest["value"] - prev["value"]
            change_pct = (change / prev["value"]) * 100

        indicators.append({
            "id": panel_id,
            "name": info["name_es"],
            "unit": info["unit"],
            "frequency": info["frequency"],
            "value": latest["value"],
            "date": latest["date"],
            "change": round(change, 4) if change is not None else None,
            "change_pct": round(change_pct, 4) if change_pct is not None else None,
            "prev_date": prev["date"] if prev else None,
            "source": "bcch",
            "derived_fields": ["change", "change_pct"],
        })

    return {"indicators": indicators}


@router.get("/series/{panel_id}")
def get_series(
    panel_id: str,
    from_date: str = Query(None, alias="from", description="YYYY-MM-DD"),
    to_date: str = Query(None, alias="to", description="YYYY-MM-DD"),
):
    """
    Datos históricos de una serie.
    Los valores son RAW del BCCh. NULL = dato no disponible (no interpolado).
    """
    if panel_id not in SERIES_CATALOG:
        return {"error": f"Serie '{panel_id}' no encontrada", "available": list(SERIES_CATALOG.keys())}

    info = SERIES_CATALOG[panel_id]
    bcch_id = info["bcch_id"]

    data = storage.get_series_data(bcch_id, from_date, to_date)

    return {
        "id": panel_id,
        "bcch_id": bcch_id,
        "name": info["name_es"],
        "unit": info["unit"],
        "frequency": info["frequency"],
        "count": len(data),
        "data": data,
        "source": "bcch",
        "note": "Valores raw del Banco Central de Chile. NULL = dato no disponible.",
    }


@router.get("/series/{panel_id}/latest")
def get_latest(panel_id: str):
    """Último valor disponible de una serie."""
    if panel_id not in SERIES_CATALOG:
        return {"error": f"Serie '{panel_id}' no encontrada"}

    info = SERIES_CATALOG[panel_id]
    latest = storage.get_latest_value(info["bcch_id"])

    return {
        "id": panel_id,
        "name": info["name_es"],
        "unit": info["unit"],
        "latest": latest,
        "source": "bcch",
    }


@router.get("/correlations")
def correlations(
    from_date: str = Query(None, alias="from"),
    to_date: str = Query(None, alias="to"),
):
    """
    Matriz de correlación entre series mensuales.
    DERIVADO: calculado por nosotros a partir de datos raw.
    Usa solo series mensuales para tener fechas alineadas.
    """
    if not from_date:
        from_date = (date.today() - timedelta(days=365 * 5)).isoformat()
    if not to_date:
        to_date = date.today().isoformat()

    # Solo series mensuales (se alinean por mes)
    monthly_ids = [
        pid for pid, info in SERIES_CATALOG.items()
        if info["frequency"] == "MONTHLY"
    ]

    # Recolectar datos por fecha
    MIN_OBS = 24  # mínimo de obs para incluir una serie
    MIN_PAIR = 12  # mínimo de fechas comunes para calcular correlación de un par

    all_series: dict[str, dict[str, float]] = {}
    for pid in monthly_ids:
        bcch_id = SERIES_CATALOG[pid]["bcch_id"]
        data = storage.get_series_data(bcch_id, from_date, to_date)
        series_dict = {
            p["date"]: p["value"]
            for p in data
            if p["value"] is not None
        }
        if len(series_dict) >= MIN_OBS:
            all_series[pid] = series_dict

    labels = sorted(all_series.keys())
    if len(labels) < 2:
        return {"matrix": {}, "labels": [], "derived": True, "note": "Insuficientes series con datos"}

    # Calcular correlación de Pearson pairwise (por fechas comunes de cada par)
    matrix: dict[str, dict[str, float]] = {}
    min_common = None

    for a in labels:
        matrix[a] = {}
        for b in labels:
            if a == b:
                matrix[a][b] = 1.0
                continue
            common = sorted(set(all_series[a].keys()) & set(all_series[b].keys()))
            n = len(common)
            if n < MIN_PAIR:
                matrix[a][b] = None
                continue
            if min_common is None or n < min_common:
                min_common = n
            va = [all_series[a][d] for d in common]
            vb = [all_series[b][d] for d in common]
            mean_a = sum(va) / n
            mean_b = sum(vb) / n
            cov = sum((va[i] - mean_a) * (vb[i] - mean_b) for i in range(n))
            std_a = (sum((x - mean_a) ** 2 for x in va) / n) ** 0.5
            std_b = (sum((x - mean_b) ** 2 for x in vb) / n) ** 0.5
            if std_a > 0 and std_b > 0:
                matrix[a][b] = round(cov / (n * std_a * std_b), 4)
            else:
                matrix[a][b] = 0.0

    return {
        "matrix": matrix,
        "labels": labels,
        "period": {"from": from_date, "to": to_date},
        "observations": min_common or 0,
        "derived": True,
        "note": "Correlacion de Pearson pairwise sobre datos raw mensuales del BCCh.",
    }


@router.get("/simulator")
def simulator(
    amount: float = Query(1000000, description="Monto inicial en CLP"),
    from_date: str = Query(None, alias="from"),
    to_date: str = Query(None, alias="to"),
):
    """
    Simulador de inversión: compara rendimiento de distintos instrumentos.
    DERIVADO: cálculo propio basado en datos raw.
    Instrumentos: UF, IPSA, USD, Depósito (TPM proxy).
    """
    if not from_date:
        from_date = (date.today() - timedelta(days=365 * 3)).isoformat()
    if not to_date:
        to_date = date.today().isoformat()

    instruments = {
        "uf": {"bcch_id": SERIES_CATALOG["uf"]["bcch_id"], "name": "UF (Inflacion)"},
        "ipsa": {"bcch_id": SERIES_CATALOG["ipsa"]["bcch_id"], "name": "IPSA (Bolsa)"},
        "usd_clp": {"bcch_id": SERIES_CATALOG["usd_clp"]["bcch_id"], "name": "Dolar (USD)"},
    }

    results = {}
    for inst_id, inst_info in instruments.items():
        data = storage.get_series_data(inst_info["bcch_id"], from_date, to_date)
        valid = [p for p in data if p["value"] is not None]

        if len(valid) < 2:
            results[inst_id] = {"name": inst_info["name"], "error": "Datos insuficientes"}
            continue

        first_val = valid[0]["value"]
        last_val = valid[-1]["value"]
        return_pct = ((last_val / first_val) - 1) * 100
        final_amount = amount * (last_val / first_val)

        # Serie normalizada (base 100 desde inicio)
        normalized = [
            {"date": p["date"], "value": round((p["value"] / first_val) * 100, 4)}
            for p in valid
        ]

        results[inst_id] = {
            "name": inst_info["name"],
            "first_date": valid[0]["date"],
            "last_date": valid[-1]["date"],
            "first_value": first_val,
            "last_value": last_val,
            "return_pct": round(return_pct, 2),
            "initial_amount": amount,
            "final_amount": round(final_amount, 0),
            "profit": round(final_amount - amount, 0),
            "data_points": len(valid),
            "normalized": normalized,
        }

    # Agregar deposito a plazo (TPM como proxy de tasa anual)
    tpm_data = storage.get_series_data(
        SERIES_CATALOG["tpm"]["bcch_id"], from_date, to_date
    )
    tpm_valid = [p for p in tpm_data if p["value"] is not None]
    if tpm_valid:
        # Calcular rendimiento compuesto dia a dia usando TPM/365
        balance = amount
        normalized_dep = [{"date": tpm_valid[0]["date"], "value": 100.0}]
        for i in range(1, len(tpm_valid)):
            daily_rate = (tpm_valid[i - 1]["value"] / 100) / 365
            balance *= (1 + daily_rate)
            normalized_dep.append({
                "date": tpm_valid[i]["date"],
                "value": round((balance / amount) * 100, 4),
            })

        results["deposito"] = {
            "name": "Deposito a Plazo (TPM)",
            "first_date": tpm_valid[0]["date"],
            "last_date": tpm_valid[-1]["date"],
            "return_pct": round(((balance / amount) - 1) * 100, 2),
            "initial_amount": amount,
            "final_amount": round(balance, 0),
            "profit": round(balance - amount, 0),
            "data_points": len(tpm_valid),
            "normalized": normalized_dep,
        }

    return {
        "instruments": results,
        "initial_amount": amount,
        "period": {"from": from_date, "to": to_date},
        "derived": True,
        "note": "Simulacion basada en datos raw del BCCh. Deposito usa TPM como proxy. No incluye comisiones.",
    }


@router.get("/analysis")
def analysis():
    """
    Genera insights clave del estado actual de la economia.
    DERIVADO: interpretacion computada de datos raw.
    """
    indicators = dashboard()["indicators"]
    ind_map = {i["id"]: i for i in indicators}

    insights = []

    # TPM
    tpm = ind_map.get("tpm")
    if tpm and tpm["value"] is not None:
        tpm_data = storage.get_series_data(
            SERIES_CATALOG["tpm"]["bcch_id"], "2024-01-01", date.today().isoformat()
        )
        tpm_vals = [p["value"] for p in tpm_data if p["value"] is not None]
        tpm_unique = list(dict.fromkeys(tpm_vals))
        direction = "bajando" if len(tpm_unique) > 1 and tpm_unique[-1] < tpm_unique[0] else "estable"
        insights.append({
            "category": "POLITICA MONETARIA",
            "title": f"TPM en {tpm['value']}%",
            "detail": f"La tasa de politica monetaria viene {direction}. "
                      f"Inicio 2024: {tpm_unique[0]}% → Actual: {tpm_unique[-1]}%. "
                      f"Se han realizado {len(tpm_unique) - 1} cambios en el periodo.",
            "signal": "neutral" if direction == "estable" else "dovish",
        })

    # Dolar
    usd = ind_map.get("usd_clp")
    if usd and usd["value"] is not None and usd["change_pct"] is not None:
        trend = "al alza" if usd["change_pct"] > 0 else "a la baja"
        urgency = "high" if abs(usd["change_pct"]) > 0.5 else "low"
        insights.append({
            "category": "TIPO DE CAMBIO",
            "title": f"Dolar a ${usd['value']:.2f}",
            "detail": f"El dolar observado cerro {trend} ({usd['change_pct']:+.2f}% vs dia anterior). "
                      f"{'Movimiento significativo.' if urgency == 'high' else 'Movimiento moderado.'}",
            "signal": "risk" if usd["change_pct"] > 1 else "neutral",
        })

    # IPSA
    ipsa = ind_map.get("ipsa")
    if ipsa and ipsa["value"] is not None:
        insights.append({
            "category": "RENTA VARIABLE",
            "title": f"IPSA en {ipsa['value']:,.0f} pts",
            "detail": f"Variacion: {ipsa['change_pct']:+.2f}% vs sesion anterior. "
                      f"{'Bolsa en positivo.' if (ipsa['change_pct'] or 0) >= 0 else 'Bolsa en rojo.'}",
            "signal": "bullish" if (ipsa["change_pct"] or 0) > 0 else "bearish",
        })

    # Desempleo
    desemp = ind_map.get("desempleo")
    if desemp and desemp["value"] is not None:
        level = "alto" if desemp["value"] > 8 else "moderado" if desemp["value"] > 6 else "bajo"
        insights.append({
            "category": "MERCADO LABORAL",
            "title": f"Desempleo en {desemp['value']:.1f}%",
            "detail": f"Nivel {level} de desocupacion. "
                      f"{'Presion sobre consumo interno.' if desemp['value'] > 8 else 'Mercado laboral relativamente estable.'}",
            "signal": "risk" if desemp["value"] > 8 else "neutral",
        })

    # Inflacion
    ipc = ind_map.get("ipc_var")
    if ipc and ipc["value"] is not None:
        insights.append({
            "category": "INFLACION",
            "title": f"IPC mensual {ipc['value']:+.1f}%",
            "detail": f"Variacion mensual del IPC: {ipc['value']:+.2f}%. "
                      f"{'Presion inflacionaria.' if ipc['value'] > 0.5 else 'Inflacion contenida.' if ipc['value'] <= 0.3 else 'Inflacion moderada.'}",
            "signal": "risk" if ipc["value"] > 0.5 else "neutral",
        })

    # Reservas
    reservas = ind_map.get("reservas_intl")
    if reservas and reservas["value"] is not None:
        insights.append({
            "category": "SECTOR EXTERNO",
            "title": f"Reservas: US${reservas['value']:,.0f}M",
            "detail": f"Reservas internacionales en US${reservas['value']:,.0f} millones. "
                      f"{'Nivel robusto, respaldo solido.' if reservas['value'] > 40000 else 'Nivel moderado.'}",
            "signal": "safe" if reservas["value"] > 40000 else "neutral",
        })

    return {
        "insights": insights,
        "generated_at": date.today().isoformat(),
        "derived": True,
        "note": "Analisis computado a partir de datos raw del BCCh. No es consejo financiero.",
    }


@router.get("/cobre")
def cobre():
    """
    Panel de cobre: precio actual, variación, exportaciones mensuales.
    DERIVADO: change y change_pct calculados por nosotros.
    """
    cobre_info = SERIES_CATALOG.get("cobre")
    export_info = SERIES_CATALOG.get("cobre_export")

    result = {"derived_fields": ["change", "change_pct"]}

    if cobre_info:
        latest = storage.get_latest_value(cobre_info["bcch_id"])
        prev = None
        if latest:
            prev = storage.get_previous_value(cobre_info["bcch_id"], latest["date"])
        change = None
        change_pct = None
        if latest and prev and prev["value"] and prev["value"] != 0:
            change = latest["value"] - prev["value"]
            change_pct = (change / prev["value"]) * 100
        result["price"] = {
            "value": latest["value"] if latest else None,
            "date": latest["date"] if latest else None,
            "change": round(change, 4) if change is not None else None,
            "change_pct": round(change_pct, 4) if change_pct is not None else None,
            "unit": cobre_info["unit"],
            "name": cobre_info["name_es"],
        }

    if export_info:
        latest_exp = storage.get_latest_value(export_info["bcch_id"])
        result["exports"] = {
            "value": latest_exp["value"] if latest_exp else None,
            "date": latest_exp["date"] if latest_exp else None,
            "unit": export_info["unit"],
            "name": export_info["name_es"],
        }

    return result


@router.get("/fx/latam")
def fx_latam(
    from_date: str = Query(None, alias="from"),
    to_date: str = Query(None, alias="to"),
):
    """
    Series FX Latam normalizadas base 100 para comparación.
    DERIVADO: normalización calculada por nosotros.
    """
    if not from_date:
        from_date = (date.today() - timedelta(days=365)).isoformat()
    if not to_date:
        to_date = date.today().isoformat()

    currencies = {}
    for pid in FX_LATAM_IDS:
        info = SERIES_CATALOG.get(pid)
        if not info:
            continue
        data = storage.get_series_data(info["bcch_id"], from_date, to_date)
        valid = [p for p in data if p["value"] is not None]
        if len(valid) < 2:
            currencies[pid] = {"name": info["name_es"], "error": "Datos insuficientes"}
            continue

        first_val = valid[0]["value"]
        normalized = [
            {"date": p["date"], "value": round((p["value"] / first_val) * 100, 4)}
            for p in valid
        ]

        last_val = valid[-1]["value"]
        change_pct = ((last_val / first_val) - 1) * 100

        currencies[pid] = {
            "name": info["name_es"],
            "first_date": valid[0]["date"],
            "last_date": valid[-1]["date"],
            "first_value": first_val,
            "last_value": last_val,
            "change_pct": round(change_pct, 2),
            "data_points": len(valid),
            "normalized": normalized,
        }

    return {
        "currencies": currencies,
        "period": {"from": from_date, "to": to_date},
        "derived": True,
        "note": "Series normalizadas base 100 a partir de datos raw del BCCh.",
    }


@router.get("/fx/monitor")
def fx_monitor():
    """
    Todos los pares FX con último valor y variación.
    DERIVADO: change y change_pct calculados por nosotros.
    """
    pairs = []
    for pid in FX_MONITOR_IDS:
        info = SERIES_CATALOG.get(pid)
        if not info:
            continue
        latest = storage.get_latest_value(info["bcch_id"])
        prev = None
        change = None
        change_pct = None
        if latest:
            prev = storage.get_previous_value(info["bcch_id"], latest["date"])
        if latest and prev and prev["value"] and prev["value"] != 0:
            change = latest["value"] - prev["value"]
            change_pct = (change / prev["value"]) * 100
        pairs.append({
            "id": pid,
            "name": info["name_es"],
            "value": latest["value"] if latest else None,
            "date": latest["date"] if latest else None,
            "change": round(change, 4) if change is not None else None,
            "change_pct": round(change_pct, 4) if change_pct is not None else None,
            "unit": info["unit"],
        })

    return {
        "pairs": pairs,
        "derived_fields": ["change", "change_pct"],
    }


@router.get("/yield-curve")
def yield_curve():
    """
    Curva de rendimiento: TPM + BCP 2Y, 5Y, 10Y.
    DERIVADO: spread y señal calculados por nosotros.
    """
    points = []
    values = {}
    for pid, tenor in [("tpm", 0), ("bcp_2y", 2), ("bcp_5y", 5), ("bcp_10y", 10)]:
        info = SERIES_CATALOG.get(pid)
        if not info:
            continue
        latest = storage.get_latest_value(info["bcch_id"])
        val = latest["value"] if latest else None
        dt = latest["date"] if latest else None
        values[pid] = val
        points.append({
            "id": pid,
            "name": info["name_es"],
            "tenor_years": tenor,
            "value": val,
            "date": dt,
        })

    # Spread 10Y - 2Y (derivado)
    spread_10_2 = None
    signal = "flat"
    if values.get("bcp_10y") is not None and values.get("bcp_2y") is not None:
        spread_10_2 = round(values["bcp_10y"] - values["bcp_2y"], 4)
        if spread_10_2 > 0.2:
            signal = "normal"
        elif spread_10_2 < -0.2:
            signal = "inverted"

    return {
        "points": points,
        "spread_10_2": spread_10_2,
        "signal": signal,
        "derived": True,
        "derived_fields": ["spread_10_2", "signal"],
    }


@router.get("/tpm-decisions")
def tpm_decisions(
    limit: int = Query(20, description="Numero maximo de decisiones"),
):
    """
    Últimas N fechas donde la TPM cambió de valor.
    Detección mecánica: busca puntos donde tpm[t] != tpm[t-1].
    DERIVADO: la detección de cambio es un cálculo nuestro.
    """
    info = SERIES_CATALOG.get("tpm")
    if not info:
        return {"decisions": [], "error": "TPM no configurada"}

    # Traer toda la historia de TPM
    data = storage.get_series_data(info["bcch_id"])
    valid = [p for p in data if p["value"] is not None]

    decisions = []
    for i in range(1, len(valid)):
        if valid[i]["value"] != valid[i - 1]["value"]:
            change = valid[i]["value"] - valid[i - 1]["value"]
            decisions.append({
                "date": valid[i]["date"],
                "rate": valid[i]["value"],
                "previous_rate": valid[i - 1]["value"],
                "change": round(change, 4),
                "direction": "up" if change > 0 else "down",
            })

    # Más recientes primero, limitar
    decisions.reverse()
    decisions = decisions[:limit]

    return {
        "decisions": decisions,
        "total_changes": len(decisions),
        "derived": True,
        "note": "Deteccion mecanica de cambios en la serie diaria de TPM del BCCh.",
    }


@router.get("/eof")
def eof(
    from_date: str = Query(None, alias="from"),
    to_date: str = Query(None, alias="to"),
):
    """
    Expectativas de tasas (Encuesta de Operadores Financieros).
    Series EOF BCP5 a distintos horizontes.
    """
    if not from_date:
        from_date = (date.today() - timedelta(days=365 * 3)).isoformat()
    if not to_date:
        to_date = date.today().isoformat()

    series = {}
    for pid in EOF_IDS:
        info = SERIES_CATALOG.get(pid)
        if not info:
            continue
        data = storage.get_series_data(info["bcch_id"], from_date, to_date)
        valid = [p for p in data if p["value"] is not None]
        series[pid] = {
            "name": info["name_es"],
            "data": valid,
            "data_points": len(valid),
        }

    return {
        "series": series,
        "period": {"from": from_date, "to": to_date},
        "source": "bcch",
    }


@router.get("/series/{panel_id}/sma")
def get_sma(
    panel_id: str,
    windows: str = Query("20,50,200", description="Ventanas SMA separadas por coma"),
    from_date: str = Query(None, alias="from"),
    to_date: str = Query(None, alias="to"),
):
    """
    Promedios móviles simples (SMA) para una serie.
    DERIVADO: calculado por nosotros sobre datos raw.
    Respeta NULLs: si hay NULL en la ventana, ese punto SMA es NULL.
    """
    if panel_id not in SERIES_CATALOG:
        return {"error": f"Serie '{panel_id}' no encontrada"}

    info = SERIES_CATALOG[panel_id]
    bcch_id = info["bcch_id"]

    # Parsear ventanas
    try:
        window_list = [int(w.strip()) for w in windows.split(",")]
    except ValueError:
        return {"error": "Formato de ventanas invalido. Usar: 20,50,200"}

    # Traer datos con margen extra para calcular SMA desde el inicio
    max_window = max(window_list)
    effective_from = from_date
    if from_date:
        # Retroceder max_window * 2 días para tener suficiente data
        from_dt = date.fromisoformat(from_date)
        effective_from = (from_dt - timedelta(days=max_window * 2)).isoformat()

    data = storage.get_series_data(bcch_id, effective_from, to_date)

    # Calcular SMA para cada ventana
    sma_results = {}
    for w in window_list:
        sma_key = f"sma_{w}"
        sma_values = []
        for i in range(len(data)):
            if i < w - 1:
                continue
            window_vals = [data[j]["value"] for j in range(i - w + 1, i + 1)]
            # Si hay algún NULL en la ventana, SMA es NULL
            if any(v is None for v in window_vals):
                sma_val = None
            else:
                sma_val = round(sum(window_vals) / w, 6)

            point_date = data[i]["date"]
            # Solo incluir si está dentro del rango solicitado
            if from_date and point_date < from_date:
                continue
            sma_values.append({"date": point_date, "value": sma_val})

        sma_results[sma_key] = sma_values

    return {
        "id": panel_id,
        "windows": window_list,
        "sma": sma_results,
        "derived": True,
        "method": "SMA",
        "note": "Promedios moviles simples calculados sobre datos raw. NULL en ventana = NULL en SMA.",
    }


@router.get("/macro-analysis")
def macro_analysis():
    """
    Análisis macroeconómico algorítmico.
    DERIVADO: reglas determinísticas que cruzan indicadores raw del BCCh.
    Cada insight incluye explicación técnica y explicación simple.
    """
    insights = analysis_engine.run_analysis()
    return {
        "insights": insights,
        "count": len(insights),
        "generated_at": date.today().isoformat(),
        "derived": True,
        "note": "Analisis algoritmico basado en reglas economicas aplicadas a datos raw del BCCh. No es consejo financiero.",
    }


@router.get("/macro-synthesis")
def macro_synthesis():
    """
    Síntesis narrativa macroeconómica.
    DERIVADO: informe generado algorítmicamente a partir de insights del analysis_engine.
    Pipeline de 7 etapas: clasificar → contradicciones → score → secciones → narrativa → resumen → recomendaciones.
    100% determinístico, sin IA, portable.
    """
    insights = analysis_engine.run_analysis()
    return synthesis_engine.synthesize(insights)
