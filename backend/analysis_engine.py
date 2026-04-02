"""
Motor de Análisis Algorítmico — Bloomberg Chile

Reglas económicas determinísticas que cruzan indicadores.
DERIVADO: todo lo que sale de aquí es cálculo propio, etiquetado como tal.
Cada insight tiene:
- Explicación técnica (para entendidos)
- Explicación simple (para cualquier persona)
- Los indicadores raw que usa (trazabilidad)
"""

from datetime import date, timedelta
import storage
from config import SERIES_CATALOG


def _latest(panel_id: str) -> dict | None:
    """Obtiene último valor de una serie."""
    info = SERIES_CATALOG.get(panel_id)
    if not info:
        return None
    return storage.get_latest_value(info["bcch_id"])


def _prev(panel_id: str, before_date: str) -> dict | None:
    """Obtiene valor anterior a una fecha."""
    info = SERIES_CATALOG.get(panel_id)
    if not info:
        return None
    return storage.get_previous_value(info["bcch_id"], before_date)


def _series(panel_id: str, from_date: str = None, to_date: str = None) -> list[dict]:
    """Obtiene serie completa."""
    info = SERIES_CATALOG.get(panel_id)
    if not info:
        return []
    return storage.get_series_data(info["bcch_id"], from_date, to_date)


def _pct_change(panel_id: str, months: int) -> float | None:
    """Calcula variación % comparando último valor vs valor de hace N meses.

    Usa la fecha del último dato como referencia (no today()), y busca el dato
    más cercano a N meses antes de esa fecha. Esto garantiza comparaciones
    correctas para series mensuales (YoY) y diarias.
    """
    info = SERIES_CATALOG.get(panel_id)
    if not info:
        return None
    latest = storage.get_latest_value(info["bcch_id"])
    if not latest or latest["value"] is None:
        return None
    try:
        latest_date = date.fromisoformat(latest["date"])
    except (ValueError, TypeError):
        return None
    # Buscar dato de hace N meses desde la fecha del último dato
    target_date = latest_date - timedelta(days=months * 30)
    window_from = (target_date - timedelta(days=20)).isoformat()
    window_to = (target_date + timedelta(days=20)).isoformat()
    data = storage.get_series_data(info["bcch_id"], window_from, window_to)
    valid = [p for p in data if p["value"] is not None]
    if not valid:
        return None
    # Elegir el dato más cercano a la fecha objetivo
    prev = min(valid, key=lambda p: abs((date.fromisoformat(p["date"]) - target_date).days))
    if prev["value"] == 0:
        return None
    return ((latest["value"] / prev["value"]) - 1) * 100


def _trend(panel_id: str, months: int = 6) -> str | None:
    """Determina tendencia: 'up', 'down', 'flat'."""
    pct = _pct_change(panel_id, months)
    if pct is None:
        return None
    if pct > 2:
        return "up"
    if pct < -2:
        return "down"
    return "flat"


def _is_stale(data_point: dict | None, max_months: int = 6) -> bool:
    """Verifica si un dato es obsoleto (más antiguo que max_months)."""
    if not data_point or not data_point.get("date"):
        return True
    try:
        data_date = date.fromisoformat(data_point["date"])
        cutoff = date.today() - timedelta(days=max_months * 30)
        return data_date < cutoff
    except (ValueError, TypeError):
        return True


def run_analysis() -> list[dict]:
    """Ejecuta todas las reglas y retorna lista de insights."""
    insights = []

    # Recopilar datos
    usd = _latest("usd_clp")
    cobre = _latest("cobre")
    tpm = _latest("tpm")
    ipsa = _latest("ipsa")
    ipc = _latest("ipc_var")
    desempleo = _latest("desempleo")
    deuda = _latest("deuda_pib")
    cc = _latest("cuenta_corriente")
    reservas = _latest("reservas_intl")
    imacec = _latest("imacec")
    bcp2 = _latest("bcp_2y")
    bcp5 = _latest("bcp_5y")
    bcp10 = _latest("bcp_10y")
    uf = _latest("uf")
    eof_2m = _latest("eof_5y_2m")

    usd_3m = _pct_change("usd_clp", 3)
    cobre_3m = _pct_change("cobre", 3)
    ipsa_3m = _pct_change("ipsa", 3)
    usd_trend = _trend("usd_clp", 3)
    cobre_trend = _trend("cobre", 3)

    # ─────────────────────────────────────────────
    # REGLA 1: Paradoja Cobre-Dólar
    # ─────────────────────────────────────────────
    if cobre_trend and usd_trend:
        if cobre_trend == "up" and usd_trend == "up":
            insights.append({
                "category": "DIVERGENCIA",
                "title": "Paradoja Cobre-Dolar: ambos suben",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"El cobre ha subido {cobre_3m:+.1f}% en 3 meses, lo que normalmente "
                    f"fortalece al CLP. Sin embargo, el dolar tambien subio {usd_3m:+.1f}%. "
                    f"Esto sugiere que hay factores negativos (riesgo pais, deuda, salida "
                    f"de capitales) que contrarrestan el efecto positivo del cobre."
                ),
                "simple": (
                    "Imagina que tu negocio esta vendiendo mas que nunca (el cobre es el "
                    "gran producto de Chile). Normalmente eso te haria mas rico y tu moneda "
                    "valdria mas. Pero el dolar IGUAL sube, lo que significa que algo mas "
                    "esta asustando a los inversionistas — como si tu negocio vendiera mucho "
                    "pero tuvieras deudas que preocupan a todos."
                ),
                "indicators": ["cobre", "usd_clp"],
            })
        elif cobre_trend == "up" and usd_trend == "down":
            insights.append({
                "category": "FAVORABLE",
                "title": "Ciclo positivo: cobre sube, dolar baja",
                "severity": "info",
                "signal": "bullish",
                "detail": (
                    f"El cobre sube {cobre_3m:+.1f}% y el dolar baja {usd_3m:+.1f}% — "
                    f"la relacion historica normal esta funcionando. Chile recibe mas "
                    f"dolares por cobre, el CLP se fortalece."
                ),
                "simple": (
                    "Chile es como un pais que vende manzanas al mundo. Cuando las manzanas "
                    "suben de precio (el cobre), Chile recibe mas plata y el peso chileno "
                    "se pone mas fuerte frente al dolar. Eso es exactamente lo que esta "
                    "pasando ahora — todo calza como deberia."
                ),
                "indicators": ["cobre", "usd_clp"],
            })
        elif cobre_trend == "down" and usd_trend == "up":
            insights.append({
                "category": "RIESGO",
                "title": "Doble presion: cobre baja y dolar sube",
                "severity": "critical",
                "signal": "bearish",
                "detail": (
                    f"El cobre cae {cobre_3m:+.1f}% mientras el dolar sube {usd_3m:+.1f}%. "
                    f"Esto es la peor combinacion para Chile: menos ingresos por exportaciones "
                    f"Y una moneda mas debil. Presion fiscal y cambiaria simultanea."
                ),
                "simple": (
                    "Es como si el producto estrella de tu negocio bajara de precio Y "
                    "al mismo tiempo tuvieras que pagar tus deudas en una moneda mas cara. "
                    "Chile gana menos por el cobre y todo lo importado se encarece. "
                    "Es la tormenta perfecta en economia."
                ),
                "indicators": ["cobre", "usd_clp"],
            })
        elif cobre_trend == "flat" and usd_trend == "up":
            insights.append({
                "category": "TIPO DE CAMBIO",
                "title": f"Dolar sube sin soporte del cobre ({usd_3m:+.1f}% en 3M)",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"El cobre se mantiene estable ({cobre_3m:+.1f}%) pero el dolar sube "
                    f"{usd_3m:+.1f}% en 3 meses. Si no es el cobre lo que mueve al dolar, "
                    f"son factores como tasas de interes en EEUU, riesgo politico local, "
                    f"o salida de capitales."
                ),
                "simple": (
                    "El dolar esta subiendo, pero no es porque el cobre baje (el cobre esta "
                    "mas o menos igual). Eso significa que algo MAS esta haciendo subir al "
                    "dolar — puede ser que EEUU suba sus tasas, que inversionistas saquen "
                    "plata de Chile, o que haya incertidumbre politica. Es como si tu negocio "
                    "fuera igual de bien pero tu moneda igual perdiera valor."
                ),
                "indicators": ["cobre", "usd_clp"],
            })
        else:
            # Cualquier otra combinación (flat/flat, flat/down, down/down, down/flat)
            combo = f"Cobre {cobre_trend} ({cobre_3m:+.1f}%), Dolar {usd_trend} ({usd_3m:+.1f}%)"
            insights.append({
                "category": "COBRE Y DOLAR",
                "title": f"Relacion cobre-dolar: {combo}",
                "severity": "info",
                "signal": "neutral",
                "detail": (
                    f"Cobre varia {cobre_3m:+.1f}% y dolar {usd_3m:+.1f}% en 3 meses. "
                    f"No hay divergencia significativa en este momento. La relacion entre "
                    f"ambos funciona dentro de parametros normales."
                ),
                "simple": (
                    "El cobre y el dolar se mueven sin grandes sorpresas. No hay señales "
                    "de alerta en la relacion entre ambos. Es como un dia normal en la "
                    "economia — sin tormentas ni bonanzas inesperadas."
                ),
                "indicators": ["cobre", "usd_clp"],
            })

    # ─────────────────────────────────────────────
    # REGLA 2: Semáforo del BCCh
    # ─────────────────────────────────────────────
    if tpm and ipc and tpm["value"] is not None and ipc["value"] is not None:
        tpm_val = tpm["value"]
        ipc_val = ipc["value"]

        # Buscar tendencia de TPM (últimos cambios)
        tpm_data = _series("tpm", (date.today() - timedelta(days=365)).isoformat())
        tpm_vals = list(dict.fromkeys([p["value"] for p in tpm_data if p["value"] is not None]))

        if len(tpm_vals) >= 2:
            tpm_direction = "bajando" if tpm_vals[-1] < tpm_vals[0] else "subiendo" if tpm_vals[-1] > tpm_vals[0] else "estable"

            if tpm_direction == "bajando" and ipc_val > 0.4:
                insights.append({
                    "category": "POLITICA MONETARIA",
                    "title": "BCCh baja tasas con inflacion activa",
                    "severity": "warning",
                    "signal": "risk",
                    "detail": (
                        f"La TPM viene bajando (ahora {tpm_val}%) mientras el IPC mensual "
                        f"es {ipc_val:+.2f}%, por encima de lo esperado. El BCCh podria "
                        f"estar priorizando crecimiento sobre inflacion, o apostando a que "
                        f"la inflacion es transitoria."
                    ),
                    "simple": (
                        "El Banco Central es como el termostato de la economia. Cuando baja "
                        "la tasa (TPM), es como bajar la calefaccion — hace que sea mas barato "
                        "pedir prestado y la economia se mueve mas rapido. Pero si los precios "
                        "ya estan subiendo (IPC alto), bajar el termostato puede recalentar todo "
                        "aun mas. Es como echar bencina al fuego."
                    ),
                    "indicators": ["tpm", "ipc_var"],
                })
            elif tpm_direction == "bajando" and ipc_val > 0.3 and ipc_val <= 0.4:
                insights.append({
                    "category": "POLITICA MONETARIA",
                    "title": "BCCh recorta tasas — inflacion en zona de transicion",
                    "severity": "info",
                    "signal": "neutral",
                    "detail": (
                        f"La TPM baja (ahora {tpm_val}%) con IPC mensual en {ipc_val:+.2f}%. "
                        f"La inflacion esta en zona de vigilancia: no impide recortes pero "
                        f"limita la velocidad del ciclo de baja."
                    ),
                    "simple": (
                        "El Banco Central esta bajando las tasas, pero los precios no estan "
                        "del todo calmos. No es alarma, pero obliga al Central a ir con cuidado — "
                        "como manejar en una carretera mojada: puedes avanzar, pero mas lento."
                    ),
                    "indicators": ["tpm", "ipc_var"],
                })
            elif tpm_direction == "bajando" and ipc_val <= 0.3:
                insights.append({
                    "category": "POLITICA MONETARIA",
                    "title": "BCCh recorta con inflacion controlada",
                    "severity": "info",
                    "signal": "bullish",
                    "detail": (
                        f"La TPM baja (ahora {tpm_val}%) y la inflacion mensual esta "
                        f"contenida en {ipc_val:+.2f}%. Hay espacio para seguir recortando "
                        f"sin riesgo inflacionario inmediato."
                    ),
                    "simple": (
                        "Los precios estan tranquilos, asi que el Banco Central puede darse "
                        "el lujo de hacer los creditos mas baratos. Eso es bueno para la gente "
                        "que quiere comprar casa, auto, o para empresas que quieren crecer. "
                        "Es como cuando el clima esta bueno y puedes abrir las ventanas."
                    ),
                    "indicators": ["tpm", "ipc_var"],
                })

    # ─────────────────────────────────────────────
    # REGLA 3: Yield Curve — Señal de Recesión
    # ─────────────────────────────────────────────
    if bcp10 and bcp2 and bcp10["value"] is not None and bcp2["value"] is not None:
        spread = bcp10["value"] - bcp2["value"]
        imacec_trend = _trend("imacec", 6)
        desemp_trend = _trend("desempleo", 6)

        if spread < -0.1:
            recession_signals = 1  # curva invertida
            if imacec_trend == "down":
                recession_signals += 1
            if desemp_trend == "up":
                recession_signals += 1

            severity = "critical" if recession_signals >= 3 else "warning" if recession_signals >= 2 else "info"

            insights.append({
                "category": "SENAL DE RECESION",
                "title": f"Curva de rendimiento invertida (spread {spread:+.2f}%)",
                "severity": severity,
                "signal": "bearish",
                "detail": (
                    f"El bono a 10 anos rinde {bcp10['value']:.2f}% vs {bcp2['value']:.2f}% "
                    f"a 2 anos. Spread: {spread:+.2f}%. Una curva invertida ha predicho "
                    f"recesiones en el pasado. "
                    f"{'IMACEC tambien cae. ' if imacec_trend == 'down' else ''}"
                    f"{'Desempleo subiendo. ' if desemp_trend == 'up' else ''}"
                    f"{recession_signals}/3 senales de recesion activas."
                ),
                "simple": (
                    "Normalmente, si le prestas plata a alguien por 10 anos, te pagan mas "
                    "que si se la prestas por 2, porque es mas riesgoso. Cuando pasa al reves "
                    "(te pagan MAS por prestar a 2 anos que a 10), significa que la gente "
                    "cree que el futuro va a ser PEOR que el presente. Historicamente, "
                    "cuando esto pasa, viene una recesion. Es como cuando todos empiezan "
                    "a guardar paraguas aunque hoy este soleado."
                ),
                "indicators": ["bcp_2y", "bcp_10y", "imacec", "desempleo"],
            })
        elif spread > 0.5:
            insights.append({
                "category": "CURVA DE RENDIMIENTO",
                "title": f"Curva normal y saludable (spread +{spread:.2f}%)",
                "severity": "info",
                "signal": "bullish",
                "detail": (
                    f"Spread 10Y-2Y de +{spread:.2f}%. La curva tiene pendiente positiva "
                    f"normal, lo que indica expectativas de crecimiento e inflacion moderada."
                ),
                "simple": (
                    "Los inversionistas esperan que el futuro sea mejor que el presente. "
                    "Es la senal normal de una economia que funciona bien — como cuando "
                    "la gente hace planes a largo plazo porque confia en que las cosas "
                    "van a seguir andando."
                ),
                "indicators": ["bcp_2y", "bcp_10y"],
            })
        else:
            # Spread entre -0.1 y 0.5 — curva plana
            insights.append({
                "category": "CURVA DE RENDIMIENTO",
                "title": f"Curva aplanada — senal de cautela (spread {spread:+.2f}%)",
                "severity": "warning",
                "signal": "neutral",
                "detail": (
                    f"BCP 10Y ({bcp10['value']:.2f}%) rinde apenas {spread:+.2f}% mas que "
                    f"BCP 2Y ({bcp2['value']:.2f}%). Una curva plana indica que el mercado "
                    f"no espera mucho crecimiento futuro, o anticipa que el BCCh bajara tasas "
                    f"significativamente."
                ),
                "simple": (
                    "La 'curva de tasas' esta casi plana — significa que prestar plata a "
                    "2 anos paga casi lo mismo que a 10 anos. Eso NO es normal. Normalmente "
                    "a mas plazo, mas te pagan. Cuando se aplana, el mercado esta diciendo: "
                    "'no esperamos mucho crecimiento'. No es tan grave como una curva invertida "
                    "(que predice recesion), pero es una luz amarilla."
                ),
                "indicators": ["bcp_2y", "bcp_10y"],
            })

    # ─────────────────────────────────────────────
    # REGLA 4: Vulnerabilidad Fiscal
    # ─────────────────────────────────────────────
    if deuda and deuda["value"] is not None:
        deuda_val = deuda["value"]
        cc_val = cc["value"] if cc and cc["value"] is not None else None
        reservas_val = reservas["value"] if reservas and reservas["value"] is not None else None
        reservas_trend = _trend("reservas_intl", 6)

        fiscal_risk = 0
        reasons = []
        if deuda_val > 35:
            fiscal_risk += 1
            reasons.append(f"deuda en {deuda_val:.1f}% del PIB")
        if cc_val is not None and cc_val < 0:
            fiscal_risk += 1
            reasons.append(f"cuenta corriente negativa (US${cc_val:,.0f}M)")
        if reservas_trend == "down":
            fiscal_risk += 1
            reasons.append("reservas internacionales cayendo")

        if fiscal_risk >= 2:
            insights.append({
                "category": "SALUD FISCAL",
                "title": "Presion fiscal: " + " + ".join(reasons),
                "severity": "warning" if fiscal_risk == 2 else "critical",
                "signal": "risk",
                "detail": (
                    f"Chile muestra {fiscal_risk} senales de vulnerabilidad fiscal: "
                    f"{', '.join(reasons)}. Si el cobre cae, los ingresos del fisco se "
                    f"reducen y la presion aumenta."
                ),
                "simple": (
                    "Piensa en Chile como una familia. La deuda es lo que debe el pais, "
                    "la cuenta corriente es si gasta mas de lo que gana con el exterior, "
                    "y las reservas son el ahorro de emergencia. "
                    f"Ahora mismo: {reasons[0]}"
                    f"{', ' + reasons[1] if len(reasons) > 1 else ''}"
                    f"{', y ' + reasons[2] if len(reasons) > 2 else ''}. "
                    "Es como una familia que debe plata, gasta mas de lo que gana, "
                    "y se esta comiendo los ahorros. No es crisis aun, pero hay que "
                    "estar atentos."
                ),
                "indicators": ["deuda_pib", "cuenta_corriente", "reservas_intl"],
            })
        elif fiscal_risk == 1 and deuda_val > 35:
            insights.append({
                "category": "SALUD FISCAL",
                "title": f"Deuda elevada ({deuda_val:.1f}% PIB) pero sin crisis",
                "severity": "info",
                "signal": "neutral",
                "detail": (
                    f"Deuda en {deuda_val:.1f}% del PIB — sobre el 35% de referencia historica "
                    f"de Chile. Sin embargo, otros indicadores fiscales no encienden alarmas: "
                    f"{'cuenta corriente positiva, ' if cc_val and cc_val > 0 else ''}"
                    f"{'reservas estables o creciendo.' if reservas_trend != 'down' else ''} "
                    f"La deuda es manejable pero la tendencia debe monitorearse."
                ),
                "simple": (
                    f"Chile debe {deuda_val:.0f}% de lo que produce en un ano. Es mas de lo "
                    f"que acostumbra, pero no esta en crisis porque sus otros numeros estan "
                    f"bien — tiene ahorros, no gasta mas de lo que gana afuera. "
                    f"Es como una persona que tiene una deuda grande pero gana buen sueldo "
                    f"y paga sus cuentas a tiempo. No es ideal, pero es sostenible... por ahora."
                ),
                "indicators": ["deuda_pib", "cuenta_corriente", "reservas_intl"],
            })
        elif fiscal_risk == 0 and deuda_val < 30:
            insights.append({
                "category": "SALUD FISCAL",
                "title": f"Finanzas publicas solidas (deuda {deuda_val:.1f}% PIB)",
                "severity": "info",
                "signal": "safe",
                "detail": (
                    f"Deuda en {deuda_val:.1f}% del PIB — bajo para estandares "
                    f"internacionales. {'Reservas estables o creciendo. ' if reservas_trend != 'down' else ''}"
                    f"Chile mantiene espacio fiscal."
                ),
                "simple": (
                    "Chile tiene sus cuentas relativamente ordenadas. La deuda es baja "
                    "comparada con otros paises (Japon tiene mas de 200%, por ejemplo). "
                    "Es como una familia que debe poco y tiene ahorros — si viene una "
                    "emergencia, puede aguantar."
                ),
                "indicators": ["deuda_pib", "reservas_intl"],
            })

    # ─────────────────────────────────────────────
    # REGLA 5: Competitividad Latam
    # ─────────────────────────────────────────────
    latam_changes = {}
    for pid in ["usd_clp", "brl_clp", "cop_clp", "pen_clp", "mxn_clp"]:
        pct = _pct_change(pid, 3)
        if pct is not None:
            latam_changes[pid] = pct

    if len(latam_changes) >= 3 and "usd_clp" in latam_changes:
        clp_change = latam_changes["usd_clp"]
        others = {k: v for k, v in latam_changes.items() if k != "usd_clp"}
        avg_others = sum(others.values()) / len(others)

        names = {"brl_clp": "Real brasileno", "cop_clp": "Peso colombiano",
                 "pen_clp": "Sol peruano", "mxn_clp": "Peso mexicano"}

        # Encontrar la más y menos depreciada
        all_sorted = sorted(latam_changes.items(), key=lambda x: x[1], reverse=True)

        worst = all_sorted[0]
        best = all_sorted[-1]
        worst_name = names.get(worst[0], worst[0])
        best_name = names.get(best[0], best[0])

        if clp_change > avg_others + 3:
            insights.append({
                "category": "COMPETITIVIDAD REGIONAL",
                "title": "CLP se deprecia mas que sus pares Latam",
                "severity": "warning",
                "signal": "bearish",
                "detail": (
                    f"El CLP se ha depreciado {clp_change:+.1f}% en 3 meses vs promedio "
                    f"Latam de {avg_others:+.1f}%. Chile pierde terreno frente a vecinos. "
                    f"Esto puede indicar factores Chile-especificos (politica, fiscal, "
                    f"confianza) mas alla del contexto global."
                ),
                "simple": (
                    "Si todas las monedas de Latinoamerica fueran corredores en una carrera, "
                    "el peso chileno esta quedando atras. Las monedas de Brasil, Colombia y "
                    "Mexico aguantan mejor. Eso puede significar que los inversionistas "
                    "confian menos en Chile que en sus vecinos — algo especifico de Chile "
                    "los esta preocupando."
                ),
                "indicators": list(latam_changes.keys()),
            })
        elif clp_change < avg_others - 3:
            insights.append({
                "category": "COMPETITIVIDAD REGIONAL",
                "title": "CLP mas resiliente que pares Latam",
                "severity": "info",
                "signal": "bullish",
                "detail": (
                    f"El CLP varia {clp_change:+.1f}% en 3 meses vs promedio Latam de "
                    f"{avg_others:+.1f}%. Chile se mantiene mas solido que sus vecinos."
                ),
                "simple": (
                    "En la carrera de monedas latinoamericanas, el peso chileno va "
                    "adelante (o al menos no se queda atras). Los inversionistas ven "
                    "a Chile como un pais mas estable que sus vecinos. Es como ser "
                    "el alumno mas confiable del curso."
                ),
                "indicators": list(latam_changes.keys()),
            })
        else:
            # CLP se mueve en línea con Latam
            insights.append({
                "category": "COMPETITIVIDAD REGIONAL",
                "title": f"CLP se mueve en linea con Latam (CLP {clp_change:+.1f}% vs region {avg_others:+.1f}%)",
                "severity": "info",
                "signal": "neutral",
                "detail": (
                    f"CLP varia {clp_change:+.1f}% en 3 meses, similar al promedio Latam "
                    f"({avg_others:+.1f}%). Mas depreciada: {worst_name} ({worst[1]:+.1f}%). "
                    f"Mas resiliente: {best_name} ({best[1]:+.1f}%). "
                    f"El movimiento cambiario es regional, no especifico de Chile."
                ),
                "simple": (
                    f"Todas las monedas de la region se mueven parecido — el peso chileno "
                    f"no esta mejor ni peor que sus vecinos. Si el dolar sube en Chile, "
                    f"tambien sube en Brasil, Colombia y Mexico. Eso significa que el "
                    f"movimiento viene de afuera (EEUU, China) y no de algo especifico "
                    f"de Chile. La moneda mas golpeada es {worst_name} y la mas fuerte "
                    f"es {best_name}."
                ),
                "indicators": list(latam_changes.keys()),
            })

    # ─────────────────────────────────────────────
    # REGLA 6: Presión Inflacionaria
    # ─────────────────────────────────────────────
    if ipc and ipc["value"] is not None and desempleo and desempleo["value"] is not None:
        ipc_val = ipc["value"]
        desemp_val = desempleo["value"]
        desemp_trend = _trend("desempleo", 6)

        if ipc_val > 0.4 and desemp_trend == "down":
            insights.append({
                "category": "INFLACION",
                "title": "Presion de demanda: precios suben y desempleo baja",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"IPC mensual de {ipc_val:+.2f}% con desempleo en {desemp_val:.1f}% "
                    f"y cayendo. Mercado laboral ajustado genera presion salarial que "
                    f"se traspasa a precios. El BCCh podria pausar recortes de TPM."
                ),
                "simple": (
                    "Cuando hay mucho trabajo y poca gente disponible, las empresas "
                    "tienen que pagar mas para contratar. Eso sube los costos y al final "
                    "los precios. Es como cuando hay mucha gente queriendo comprar "
                    "en una feria con pocos puestos — todo se encarece. El Banco Central "
                    "podria tener que subir las tasas para enfriar la economia."
                ),
                "indicators": ["ipc_var", "desempleo"],
            })
        elif ipc_val > 0.4 and usd_trend == "up":
            insights.append({
                "category": "INFLACION",
                "title": "Presion de costos: dolar sube y arrastra precios",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"IPC mensual de {ipc_val:+.2f}% coincide con dolar al alza "
                    f"({usd_3m:+.1f}% en 3 meses). Inflacion importada: Chile compra "
                    f"muchas cosas en dolares (petroleo, tecnologia, alimentos)."
                ),
                "simple": (
                    "Chile importa muchas cosas pagando en dolares — bencina, "
                    "computadores, algunos alimentos. Cuando el dolar sube, todo eso "
                    "se encarece aunque en Chile no haya cambiado nada. Es como si "
                    "el supermercado subiera los precios solo porque cambio el tipo de "
                    "cambio, no porque haya escasez."
                ),
                "indicators": ["ipc_var", "usd_clp"],
            })
        elif ipc_val > 0.2 and ipc_val <= 0.4:
            # Inflación moderada sin triggers especiales (desempleo/dólar)
            insights.append({
                "category": "INFLACION",
                "title": f"Inflacion en zona de vigilancia (IPC {ipc_val:+.2f}% mensual)",
                "severity": "info",
                "signal": "neutral",
                "detail": (
                    f"IPC mensual de {ipc_val:+.2f}%. Sobre el rango de confort pero sin "
                    f"presion de demanda ni costos identificables. Requiere seguimiento "
                    f"para determinar si es transitorio o persistente."
                ),
                "simple": (
                    "Los precios subieron un poco — no es alarma pero tampoco es ideal. "
                    "Hay que ver si el mes que viene se repite. Si es solo un mes, no pasa nada. "
                    "Si se repite, empieza a ser un problema."
                ),
                "indicators": ["ipc_var"],
            })
        elif ipc_val <= 0.2 and ipc_val >= -0.1:
            insights.append({
                "category": "INFLACION",
                "title": f"Inflacion contenida (IPC {ipc_val:+.2f}% mensual)",
                "severity": "info",
                "signal": "safe",
                "detail": (
                    f"IPC mensual de {ipc_val:+.2f}%, dentro del rango normal. "
                    f"No hay presion inflacionaria significativa en este momento."
                ),
                "simple": (
                    "Los precios estan tranquilos, sin grandes subidas ni bajadas. "
                    "Tu carrito del super cuesta mas o menos lo mismo que el mes pasado. "
                    "Eso es bueno — significa que la economia esta equilibrada."
                ),
                "indicators": ["ipc_var"],
            })
        elif ipc_val < -0.1:
            insights.append({
                "category": "INFLACION",
                "title": f"Deflacion: precios caen {ipc_val:+.2f}% mensual",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"IPC mensual de {ipc_val:+.2f}%. Caida generalizada de precios. "
                    f"Si se prolonga, puede indicar debilidad severa de la demanda, "
                    f"postergar decisiones de consumo e inversion, y dificultar el pago "
                    f"de deudas (que son fijas pero los ingresos bajan)."
                ),
                "simple": (
                    "Los precios estan cayendo — suena bien pero no lo es. Cuando la gente "
                    "piensa que manana sera mas barato, deja de comprar hoy. Las empresas "
                    "venden menos, bajan sueldos o despiden gente, y se genera un circulo "
                    "vicioso. Japon vivio decadas con este problema."
                ),
                "indicators": ["ipc_var"],
            })

    # ─────────────────────────────────────────────
    # REGLA 7: Señal Inversión IPSA
    # ─────────────────────────────────────────────
    if ipsa and tpm and ipc:
        ipsa_val = ipsa["value"] if ipsa["value"] is not None else None
        tpm_val = tpm["value"] if tpm["value"] is not None else None
        ipc_val = ipc["value"] if ipc["value"] is not None else None
        tpm_data = _series("tpm", (date.today() - timedelta(days=365)).isoformat())
        tpm_vals = list(dict.fromkeys([p["value"] for p in tpm_data if p["value"] is not None]))
        tpm_bajando = len(tpm_vals) >= 2 and tpm_vals[-1] < tpm_vals[0]

        if ipsa_val and ipsa_3m and ipsa_3m > 5 and tpm_bajando and ipc_val is not None and ipc_val < 0.5:
            insights.append({
                "category": "RENTA VARIABLE",
                "title": f"Entorno favorable para bolsa (IPSA {ipsa_3m:+.1f}% en 3M)",
                "severity": "info",
                "signal": "bullish",
                "detail": (
                    f"IPSA sube {ipsa_3m:+.1f}% en 3 meses, TPM en recorte ({tpm_val}%), "
                    f"inflacion baja ({ipc_val:+.2f}% mensual). Triple condicion favorable "
                    f"para renta variable: plata barata + precios controlados + momentum."
                ),
                "simple": (
                    "La bolsa esta subiendo, los creditos se estan abaratando, y los "
                    "precios no se descontrolan. Es como un semaforo en verde para "
                    "invertir en acciones chilenas. Ojo: esto no es consejo financiero, "
                    "es solo lo que dicen los numeros hoy."
                ),
                "indicators": ["ipsa", "tpm", "ipc_var"],
            })
        elif ipsa_3m and ipsa_3m < -5:
            insights.append({
                "category": "RENTA VARIABLE",
                "title": f"Bolsa en retroceso (IPSA {ipsa_3m:+.1f}% en 3M)",
                "severity": "warning",
                "signal": "bearish",
                "detail": (
                    f"IPSA cae {ipsa_3m:+.1f}% en 3 meses. "
                    f"{'TPM subiendo agrega presion. ' if not tpm_bajando else ''}"
                    f"Posible aversion al riesgo o deterioro de expectativas."
                ),
                "simple": (
                    "La bolsa chilena esta cayendo — la gente esta vendiendo acciones. "
                    "Puede ser porque tienen miedo del futuro economico, o porque hay "
                    "mejores opciones en otro lado. Es como cuando la gente empieza "
                    "a cerrar negocios en un barrio — senal de que algo preocupa."
                ),
                "indicators": ["ipsa", "tpm"],
            })
        elif ipsa_val and ipsa_3m is not None:
            # Caso intermedio: IPSA se mueve poco
            insights.append({
                "category": "RENTA VARIABLE",
                "title": f"Bolsa lateral (IPSA {ipsa_3m:+.1f}% en 3M, nivel {ipsa_val:,.0f})",
                "severity": "info",
                "signal": "neutral",
                "detail": (
                    f"IPSA en {ipsa_val:,.0f} puntos, variacion de {ipsa_3m:+.1f}% en 3 meses. "
                    f"Mercado sin direccion clara. "
                    f"{'TPM en recorte podria impulsar la bolsa.' if tpm_bajando else 'TPM estable/al alza limita el upside.'}"
                ),
                "simple": (
                    f"La bolsa chilena esta 'plana' — no sube ni baja mucho. Los inversionistas "
                    f"estan esperando a ver que pasa antes de tomar decisiones grandes. "
                    f"Es como cuando estas en una tienda y no te decides si comprar o no — "
                    f"miras, comparas, pero no te mueves. En IPSA {ipsa_val:,.0f} puntos."
                ),
                "indicators": ["ipsa", "tpm"],
            })

    # ─────────────────────────────────────────────
    # REGLA 8: Mercado Laboral
    # ─────────────────────────────────────────────
    if desempleo and desempleo["value"] is not None:
        desemp_val = desempleo["value"]
        desemp_trend = _trend("desempleo", 6)

        if desemp_val > 9:
            insights.append({
                "category": "MERCADO LABORAL",
                "title": f"Desempleo alto: {desemp_val:.1f}%",
                "severity": "critical",
                "signal": "bearish",
                "detail": (
                    f"Desempleo en {desemp_val:.1f}%, nivel preocupante. "
                    f"{'Tendencia al alza agrava la situacion. ' if desemp_trend == 'up' else ''}"
                    f"Impacto directo en consumo interno y recaudacion fiscal."
                ),
                "simple": (
                    f"De cada 100 personas que quieren trabajar, casi {desemp_val:.0f} no "
                    f"encuentran pega. Eso es mucha gente sin sueldo, lo que significa "
                    f"menos gente comprando, menos ventas para los negocios, y menos "
                    f"impuestos para el Estado. Es un circulo vicioso que cuesta romper."
                ),
                "indicators": ["desempleo"],
            })
        elif desemp_val < 7 and desemp_trend != "up":
            insights.append({
                "category": "MERCADO LABORAL",
                "title": f"Empleo saludable: {desemp_val:.1f}%",
                "severity": "info",
                "signal": "safe",
                "detail": (
                    f"Desempleo en {desemp_val:.1f}%, nivel moderado-bajo. "
                    f"{'Estable o mejorando. ' if desemp_trend != 'up' else ''}"
                    f"Buen soporte para consumo interno."
                ),
                "simple": (
                    f"La mayoria de la gente que busca trabajo lo encuentra. "
                    f"Eso mantiene la economia moviéndose — la gente con pega "
                    f"compra cosas, los negocios venden, y el Estado recauda. "
                    f"Es el motor basico de una economia sana."
                ),
                "indicators": ["desempleo"],
            })
        else:
            # 7-9%: zona intermedia
            direction_text = (
                "y subiendo — podria empeorar" if desemp_trend == "up" else
                "y bajando — se esta recuperando" if desemp_trend == "down" else
                "y estable"
            )
            insights.append({
                "category": "MERCADO LABORAL",
                "title": f"Desempleo moderado: {desemp_val:.1f}% {direction_text}",
                "severity": "info" if desemp_trend != "up" else "warning",
                "signal": "neutral" if desemp_trend != "up" else "risk",
                "detail": (
                    f"Desempleo en {desemp_val:.1f}% — en el rango 7-9% que es zona "
                    f"de atencion sin ser critico. "
                    f"{'Tendencia al alza es preocupante. ' if desemp_trend == 'up' else ''}"
                    f"{'Tendencia a la baja es positiva. ' if desemp_trend == 'down' else ''}"
                    f"Cada punto de desempleo representa ~100.000 personas sin trabajo en Chile."
                ),
                "simple": (
                    f"De cada 100 personas que buscan trabajo, {desemp_val:.0f} no encuentran. "
                    f"No es lo peor que ha vivido Chile, pero tampoco esta bien. "
                    f"{'Lo bueno es que va mejorando. ' if desemp_trend == 'down' else ''}"
                    f"{'Lo preocupante es que va empeorando. ' if desemp_trend == 'up' else ''}"
                    f"Cada punto de desempleo son miles de familias sin ingresos estables."
                ),
                "indicators": ["desempleo"],
            })

    # ─────────────────────────────────────────────
    # REGLA 9: Expectativas de Rendimiento Bonos (EOF BCP5 vs BCP5 actual)
    # ─────────────────────────────────────────────
    # Compara expectativa de rendimiento BCP5 (EOF) vs rendimiento actual BCP5
    # Solo si los datos NO son obsoletos (EOF BCP5 puede estar discontinuado)
    if bcp5 and eof_2m and not _is_stale(eof_2m, 6) and bcp5["value"] is not None and eof_2m["value"] is not None:
        bcp5_val = bcp5["value"]
        eof_val = eof_2m["value"]
        diff = eof_val - bcp5_val

        if abs(diff) > 0.2:
            expect_dir = "mayores" if diff > 0 else "menores"
            insights.append({
                "category": "EXPECTATIVAS",
                "title": f"Mercado espera rendimientos {expect_dir} en bonos (EOF: {eof_val:.2f}% vs BCP5: {bcp5_val:.2f}%)",
                "severity": "info" if abs(diff) < 0.5 else "warning",
                "signal": "risk" if diff > 0 else "bullish",
                "detail": (
                    f"La Encuesta de Operadores Financieros proyecta el BCP5 en {eof_val:.2f}% "
                    f"a 2 meses, mientras el rendimiento actual es {bcp5_val:.2f}%. "
                    f"Diferencia: {diff:+.2f}%. "
                    f"{'El mercado espera que los bonos paguen mas — implicando mayor percepcion de riesgo o expectativa de menor recorte del BCCh.' if diff > 0 else 'El mercado espera que los bonos paguen menos — implicando confianza en que el BCCh seguira recortando.'}"
                ),
                "simple": (
                    f"Los expertos creen que los bonos del gobierno a 5 anos "
                    f"{'van a pagar mas intereses' if diff > 0 else 'van a pagar menos intereses'} "
                    f"en los proximos meses. "
                    f"{'Eso sugiere que el mercado ve mas riesgo o menos recortes de tasa.' if diff > 0 else 'Eso sugiere confianza en que las tasas seguiran bajando.'}"
                ),
                "indicators": ["bcp_5y", "eof_5y_2m"],
            })
        else:
            insights.append({
                "category": "EXPECTATIVAS",
                "title": f"Expectativas de bonos alineadas con mercado (EOF {eof_val:.2f}% ≈ BCP5 {bcp5_val:.2f}%)",
                "severity": "info",
                "signal": "neutral",
                "detail": (
                    f"La expectativa de rendimiento BCP5 a 2 meses ({eof_val:.2f}%) esta "
                    f"alineada con el rendimiento actual ({bcp5_val:.2f}%). El mercado "
                    f"no anticipa cambios significativos en la curva de rendimiento."
                ),
                "simple": (
                    "Los expertos financieros creen que los bonos van a seguir pagando "
                    "mas o menos lo mismo que hoy. Es señal de estabilidad — nadie espera "
                    "grandes sorpresas en el mercado de deuda."
                ),
                "indicators": ["bcp_5y", "eof_5y_2m"],
            })
    # Si EOF BCP5 está obsoleto, no generar insight redundante.
    # Rules 20 y 26 ya cubren expectativas TPM con datos actuales.

    # ─────────────────────────────────────────────
    # REGLA 10: Cobre y Fisco
    # ─────────────────────────────────────────────
    if cobre and cobre["value"] is not None:
        cobre_val = cobre["value"]
        cobre_6m = _pct_change("cobre", 6)
        exp_mineras = _latest("export_mineras")

        if cobre_6m is not None and cobre_6m > 15:
            insights.append({
                "category": "COMMODITIES",
                "title": f"Cobre en fuerte tendencia alcista: US${cobre_val:.2f}/lb ({cobre_6m:+.1f}% en 6M)",
                "severity": "info",
                "signal": "bullish",
                "detail": (
                    f"El cobre acumula {cobre_6m:+.1f}% en 6 meses. Chile produce ~27% "
                    f"del cobre mundial. Cada centavo de dolar que sube la libra de cobre "
                    f"son ~US$120M extras al ano para Chile. "
                    + (f"Exportaciones mineras en US${exp_mineras['value']:,.0f}M." if exp_mineras and exp_mineras.get('value') else "")
                ),
                "simple": (
                    f"El cobre esta carísimo y Chile es el mayor productor del mundo. "
                    f"Es como si vendieras limonada y de repente todos quisieran limonada "
                    f"— ganas mucha mas plata. Eso llena las arcas del gobierno (impuestos "
                    f"a mineras), fortalece al peso, y le da a Chile poder de negociacion. "
                    f"Cuando el cobre anda bien, Chile anda bien."
                ),
                "indicators": ["cobre", "export_mineras"],
            })
        elif cobre_6m is not None and cobre_6m < -15:
            insights.append({
                "category": "COMMODITIES",
                "title": f"Cobre en caida libre ({cobre_6m:+.1f}% en 6M)",
                "severity": "critical",
                "signal": "bearish",
                "detail": (
                    f"El cobre pierde {cobre_6m:+.1f}% en 6 meses. Esto impacta "
                    f"directamente ingresos fiscales, tipo de cambio, y empleo en "
                    f"regiones mineras."
                ),
                "simple": (
                    f"El producto estrella de Chile esta perdiendo valor. Como el cobre "
                    f"es tan importante para el pais (imagina que el 50% de lo que exportas "
                    f"es una sola cosa), cuando baja, TODO se ve afectado: el gobierno "
                    f"recauda menos, el dolar sube, y las regiones mineras sufren."
                ),
                "indicators": ["cobre", "export_mineras"],
            })

    # ─────────────────────────────────────────────
    # REGLA 11: Impacto del Dólar en la Vida Cotidiana
    # ─────────────────────────────────────────────
    if usd and usd["value"] is not None:
        usd_val = usd["value"]
        usd_1m = _pct_change("usd_clp", 1)
        usd_12m = _pct_change("usd_clp", 12)

        if usd_1m is not None and usd_1m > 3:
            insights.append({
                "category": "COSTO DE VIDA",
                "title": f"Dolar dispara costos importados ({usd_1m:+.1f}% en 1 mes)",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"El dolar sube {usd_1m:+.1f}% en solo 1 mes (${usd_val:.0f}). "
                    f"Chile importa el 100% de su petroleo, gran parte de sus alimentos "
                    f"procesados, tecnologia, y medicamentos. Cada $10 que sube el dolar "
                    f"se traduce en ~$5 mas por litro de bencina en semanas (antes de estabilizacion MEPCO)."
                ),
                "simple": (
                    "Cuando el dolar sube rapido, sube el precio de la bencina (porque "
                    "Chile compra todo el petroleo afuera), sube el precio de los "
                    "computadores, celulares, muchos remedios, y hasta algunos alimentos. "
                    "Es como si todo lo que viene de afuera subiera de precio de un dia "
                    "para otro. Eso golpea especialmente a las familias de menores ingresos "
                    "que gastan mas porcentaje de su sueldo en estos productos."
                ),
                "indicators": ["usd_clp"],
            })

        if usd_12m is not None:
            if usd_12m > 10:
                insights.append({
                    "category": "TIPO DE CAMBIO",
                    "title": f"Peso chileno pierde {usd_12m:.0f}% de valor en un ano",
                    "severity": "warning",
                    "signal": "bearish",
                    "detail": (
                        f"El dolar acumula {usd_12m:+.1f}% en 12 meses. Depreciacion "
                        f"sostenida que erosiona el poder adquisitivo, encarece la deuda "
                        f"externa, y presiona la inflacion."
                    ),
                    "simple": (
                        "En un ano, el peso chileno ha perdido mucho valor. Eso significa "
                        "que todo lo que Chile compra afuera es mas caro: viajes, estudiar "
                        "fuera, productos importados. Tambien hace que la deuda que Chile "
                        "tiene en dolares sea mas dificil de pagar. Es como si tu sueldo "
                        "siguiera igual pero todo alrededor subiera de precio."
                    ),
                    "indicators": ["usd_clp"],
                })
            elif usd_12m < -10:
                insights.append({
                    "category": "TIPO DE CAMBIO",
                    "title": f"Peso chileno se fortalece {abs(usd_12m):.0f}% en un ano",
                    "severity": "info",
                    "signal": "bullish",
                    "detail": (
                        f"El dolar cae {usd_12m:+.1f}% en 12 meses. CLP fuerte abarata "
                        f"importaciones, alivia presion inflacionaria, reduce costo de "
                        f"deuda externa."
                    ),
                    "simple": (
                        "El peso chileno se ha puesto mas fuerte. Eso es bueno para tu "
                        "bolsillo: comprar cosas importadas es mas barato, la bencina no "
                        "sube tanto, y si quieres viajar al extranjero, te rinde mas la plata. "
                        "Tambien le conviene al gobierno porque sus deudas en dolares se "
                        "hacen mas chicas."
                    ),
                    "indicators": ["usd_clp"],
                })

    # ─────────────────────────────────────────────
    # REGLA 12: Tasa de Interés Real
    # ─────────────────────────────────────────────
    if tpm and tpm["value"] is not None and ipc and ipc["value"] is not None:
        tpm_val = tpm["value"]
        ipc_anual = _pct_change("uf", 12)  # UF como proxy de inflación acumulada
        if ipc_anual is not None:
            tasa_real = tpm_val - ipc_anual
            insights.append({
                "category": "TASA REAL",
                "title": f"Tasa de interes real: {tasa_real:+.1f}%",
                "severity": "info" if tasa_real > 0 else "warning",
                "signal": "neutral" if 0 < tasa_real < 3 else "risk" if tasa_real < 0 else "safe",
                "detail": (
                    f"TPM en {tpm_val}% menos inflacion anualizada de {ipc_anual:.1f}% "
                    f"(proxy UF) = tasa real de {tasa_real:+.1f}%. "
                    + ("Tasa real positiva: el ahorro tiene retorno real. " if tasa_real > 0 else
                       "Tasa real NEGATIVA: la inflacion se come los ahorros. ")
                    + ("Politica monetaria restrictiva." if tasa_real > 2 else
                       "Politica monetaria neutral." if tasa_real > 0 else
                       "Politica monetaria ultra-expansiva.")
                ),
                "simple": (
                    f"Si pones $1.000.000 en el banco, el banco te paga {tpm_val}% al ano. "
                    f"Pero los precios suben {ipc_anual:.1f}% al ano. "
                    + (f"Entonces realmente ganas {tasa_real:.1f}% — tu plata crece mas rapido "
                       f"que los precios. El ahorro tiene sentido." if tasa_real > 0 else
                       f"Entonces en realidad PIERDES {abs(tasa_real):.1f}% — tu plata en el "
                       f"banco pierde valor porque los precios suben mas rapido que lo que "
                       f"te pagan. Guardar plata bajo el colchon o en el banco es perder plata.")
                ),
                "indicators": ["tpm", "uf"],
            })

    # ─────────────────────────────────────────────
    # REGLA 13: Concentración Exportadora (Riesgo Cobre)
    # ─────────────────────────────────────────────
    exp_min = _latest("export_mineras")
    exp_tot = _latest("export_total")
    exp_cobre = _latest("cobre_export")  # exportaciones de cobre específicamente
    if exp_min and exp_min["value"] is not None and cobre and cobre["value"] is not None:
        exp_val = exp_min["value"]
        exp_cobre_val = exp_cobre["value"] if exp_cobre and exp_cobre.get("value") else exp_val * 0.82
        cobre_val = cobre["value"]
        # Calcular porcentaje real si tenemos exportaciones totales
        pct_mining = None
        if exp_tot and exp_tot["value"] and exp_tot["value"] > 0:
            pct_mining = (exp_val / exp_tot["value"]) * 100
        pct_str = f"{pct_mining:.0f}%" if pct_mining else "una proporcion dominante"

        insights.append({
            "category": "DEPENDENCIA EXPORTADORA",
            "title": f"Exportaciones mineras: US${exp_val:,.0f}M ({pct_str} del total)",
            "severity": "warning" if pct_mining and pct_mining > 60 else "info",
            "signal": "risk" if pct_mining and pct_mining > 65 else "neutral",
            "detail": (
                f"Chile exporta US${exp_val:,.0f}M en mineria al mes"
                + (f", representando {pct_mining:.0f}% de las exportaciones totales (US${exp_tot['value']:,.0f}M)" if pct_mining else "")
                + f". Con el cobre a US${cobre_val:.2f}/lb, "
                f"cada variacion de 10% en el precio del cobre mueve ~US${exp_cobre_val * 0.10:,.0f}M "
                f"mensuales en ingresos. "
                + (f"Concentracion sobre 60% implica alta vulnerabilidad a shocks en commodities." if pct_mining and pct_mining > 60 else "")
            ),
            "simple": (
                "Imagina que Chile es un restaurant que solo vende un plato: cobre. "
                f"Ahora mismo ese plato se vende por US${cobre_val:.2f} y el restaurant "
                f"factura US${exp_val:,.0f} millones al mes"
                + (f" — eso es {pct_mining:.0f} de cada 100 dolares que Chile exporta" if pct_mining else "")
                + f". El problema es que si ese plato baja de precio, todo el restaurant "
                f"se ve afectado. Chile necesita diversificar lo que vende al mundo."
            ),
            "indicators": ["export_mineras", "export_total", "cobre"],
        })

    # ─────────────────────────────────────────────
    # REGLA 14: Crecimiento Económico (IMACEC)
    # ─────────────────────────────────────────────
    if imacec and imacec["value"] is not None:
        imacec_3m = _pct_change("imacec", 3)
        imacec_12m = _pct_change("imacec", 12)
        imacec_trend = _trend("imacec", 6)

        if imacec_12m is not None:
            if imacec_12m > 4:
                insights.append({
                    "category": "CRECIMIENTO",
                    "title": f"Economia crece {imacec_12m:.1f}% anual",
                    "severity": "info",
                    "signal": "bullish",
                    "detail": (
                        f"IMACEC acumula {imacec_12m:+.1f}% en 12 meses. Crecimiento solido "
                        f"que genera empleo, recaudacion fiscal, y optimismo empresarial."
                    ),
                    "simple": (
                        f"La economia chilena esta creciendo {imacec_12m:.1f}% respecto al ano "
                        f"pasado. Eso significa mas actividad: fabricas produciendo mas, tiendas "
                        f"vendiendo mas, mas construccion, mas transporte. Cuando la economia "
                        f"crece, hay mas trabajo y la gente tiene mas plata para gastar."
                    ),
                    "indicators": ["imacec"],
                })
            elif imacec_12m < 0:
                insights.append({
                    "category": "CRECIMIENTO",
                    "title": f"Economia se contrae: {imacec_12m:+.1f}% anual",
                    "severity": "critical" if imacec_12m < -2 else "warning",
                    "signal": "bearish",
                    "detail": (
                        f"IMACEC cae {imacec_12m:+.1f}% en 12 meses. Contraccion economica "
                        f"que reduce empleo, recaudacion, e inversion. "
                        f"{'Tendencia negativa sostenida.' if imacec_trend == 'down' else ''}"
                    ),
                    "simple": (
                        f"La economia chilena se esta achicando — produce menos que hace un "
                        f"ano. Eso significa menos trabajo, negocios que cierran, gente que "
                        f"gasta menos. Es como cuando una ciudad empieza a vaciarse de a poco: "
                        f"primero cierran algunos locales, despues la gente se va, y cada vez "
                        f"hay menos movimiento. El gobierno tiene que actuar rapido para revertirlo."
                    ),
                    "indicators": ["imacec"],
                })
            elif imacec_12m > 2 and imacec_12m <= 4:
                insights.append({
                    "category": "CRECIMIENTO",
                    "title": f"Crecimiento moderado: {imacec_12m:+.1f}% anual",
                    "severity": "info",
                    "signal": "neutral",
                    "detail": (
                        f"IMACEC crece {imacec_12m:+.1f}% en 12 meses. Crecimiento cercano "
                        f"al potencial de Chile (~3%). Suficiente para mantener el empleo "
                        f"estable pero insuficiente para cerrar brechas sociales significativas."
                    ),
                    "simple": (
                        f"La economia crece a un ritmo razonable — no boom, pero tampoco "
                        f"estancamiento. Es como un auto que avanza a velocidad crucero: "
                        f"llega a destino pero no gana carreras. Para que la gente realmente "
                        f"sienta la mejora, Chile necesita crecer un poco mas."
                    ),
                    "indicators": ["imacec"],
                })
            elif imacec_12m >= 0 and imacec_12m <= 2:
                insights.append({
                    "category": "CRECIMIENTO",
                    "title": f"Crecimiento debil: {imacec_12m:+.1f}% anual",
                    "severity": "warning",
                    "signal": "neutral",
                    "detail": (
                        f"IMACEC crece apenas {imacec_12m:+.1f}% en 12 meses. Crecimiento "
                        f"insuficiente para reducir desempleo o mejorar ingresos fiscales "
                        f"significativamente."
                    ),
                    "simple": (
                        f"La economia crece, pero tan poquito que casi no se nota. "
                        f"Es como un auto que se mueve, pero tan lento que no llega a ninguna "
                        f"parte. Con este ritmo no se crean suficientes empleos nuevos ni "
                        f"el gobierno recauda lo que necesita. Chile necesita crecer al "
                        f"menos 3-4% para que la gente lo sienta."
                    ),
                    "indicators": ["imacec"],
                })

    # ─────────────────────────────────────────────
    # REGLA 15: Presión Social (Desempleo + Inflación)
    # ─────────────────────────────────────────────
    if desempleo and ipc and desempleo["value"] is not None and ipc["value"] is not None:
        desemp_val = desempleo["value"]
        ipc_val = ipc["value"]
        # Indice de miseria = desempleo + inflación anualizada (proxy)
        ipc_12m_sum = 0
        ipc_data = _series("ipc_var", (date.today() - timedelta(days=400)).isoformat())
        ipc_vals = [p["value"] for p in ipc_data if p["value"] is not None]
        if len(ipc_vals) >= 12:
            ipc_12m_sum = sum(ipc_vals[-12:])

        misery_index = desemp_val + ipc_12m_sum
        if misery_index > 15:
            insights.append({
                "category": "PRESION SOCIAL",
                "title": f"Indice de miseria alto: {misery_index:.1f}",
                "severity": "critical",
                "signal": "risk",
                "detail": (
                    f"Desempleo ({desemp_val:.1f}%) + inflacion acumulada 12M ({ipc_12m_sum:.1f}%) "
                    f"= indice de miseria de {misery_index:.1f}. Sobre 15 indica fuerte "
                    f"presion social: la gente no tiene trabajo Y los precios suben."
                ),
                "simple": (
                    "El 'indice de miseria' mide que tan mal lo esta pasando la gente "
                    "comun. Se calcula sumando el desempleo con la inflacion. Cuando este "
                    f"numero supera 15 (ahora esta en {misery_index:.1f}), la gente "
                    f"empieza a sentir que no le alcanza la plata, hay descontento, y "
                    f"puede haber protestas. Es cuando la gente dice 'no llego a fin de mes' "
                    f"y busca culpables."
                ),
                "indicators": ["desempleo", "ipc_var"],
            })
        elif misery_index < 10 and desemp_val < 8:
            insights.append({
                "category": "BIENESTAR SOCIAL",
                "title": f"Indice de miseria bajo: {misery_index:.1f}",
                "severity": "info",
                "signal": "safe",
                "detail": (
                    f"Desempleo ({desemp_val:.1f}%) + inflacion acumulada 12M ({ipc_12m_sum:.1f}%) "
                    f"= indice de {misery_index:.1f}. Bajo 10 indica condiciones favorables "
                    f"para el bienestar de la poblacion."
                ),
                "simple": (
                    "La combinacion de empleo e inflacion esta en un buen rango. "
                    "La mayoria de la gente encuentra trabajo y los precios no suben "
                    "demasiado rapido. Es cuando la gente puede planificar: comprar cosas, "
                    "ahorrar, pensar en el futuro. El pais funciona con relativa normalidad."
                ),
                "indicators": ["desempleo", "ipc_var"],
            })
        else:
            # Misery index 10-15: zona de vigilancia
            insights.append({
                "category": "PRESION SOCIAL",
                "title": f"Indice de miseria moderado: {misery_index:.1f}",
                "severity": "info",
                "signal": "neutral",
                "detail": (
                    f"Desempleo ({desemp_val:.1f}%) + inflacion 12M ({ipc_12m_sum:.1f}%) "
                    f"= {misery_index:.1f}. Zona intermedia: no hay crisis pero la gente "
                    f"siente presion. Sobre 12 ya empieza el malestar social."
                ),
                "simple": (
                    f"Sumando desempleo e inflacion da {misery_index:.1f}. No es critico, "
                    f"pero la gente ya empieza a notar que las cosas estan mas apretadas. "
                    f"Algunas familias llegan justo a fin de mes. Si sube un poco mas, "
                    f"el descontento se empieza a sentir en las calles."
                ),
                "indicators": ["desempleo", "ipc_var"],
            })

    # ─────────────────────────────────────────────
    # REGLA 16: Salud de las Reservas
    # ─────────────────────────────────────────────
    if reservas and reservas["value"] is not None:
        reservas_val = reservas["value"]
        reservas_12m = _pct_change("reservas_intl", 12)
        # Usar dato real de importaciones si está disponible
        _imp_for_coverage = _latest("import_total")
        _imp_monthly = _imp_for_coverage["value"] if _imp_for_coverage and _imp_for_coverage.get("value") and _imp_for_coverage["value"] > 0 else 7000

        if reservas_val > 40000:
            months_import = reservas_val / _imp_monthly
            insights.append({
                "category": "RESERVAS INTERNACIONALES",
                "title": f"Reservas solidas: US${reservas_val:,.0f}M (~{months_import:.0f} meses de importaciones)",
                "severity": "info",
                "signal": "safe",
                "detail": (
                    f"Chile tiene US${reservas_val:,.0f}M en reservas internacionales. "
                    f"Eso cubre aproximadamente {months_import:.0f} meses de importaciones. "
                    f"El estandar internacional minimo es 3 meses. "
                    + (f"Variacion 12M: {reservas_12m:+.1f}%." if reservas_12m else "")
                ),
                "simple": (
                    "Las reservas internacionales son como la cuenta de ahorro de emergencia "
                    f"de Chile. Tiene US${reservas_val / 1000:,.0f} mil millones guardados. "
                    f"Si manana Chile no pudiera exportar nada, esos ahorros alcanzarian "
                    f"para seguir comprando lo que necesita por {months_import:.0f} meses. "
                    f"Los paises que tienen pocas reservas quedan vulnerables a crisis "
                    f"cambiarias (como Argentina). Chile esta bien parado en esto."
                ),
                "indicators": ["reservas_intl"],
            })
        elif reservas_val < 30000:
            insights.append({
                "category": "RESERVAS INTERNACIONALES",
                "title": f"Reservas bajo presion: US${reservas_val:,.0f}M",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"Reservas en US${reservas_val:,.0f}M, nivel que podria preocupar "
                    f"si se mantiene la tendencia. "
                    + (f"Caen {reservas_12m:+.1f}% en 12 meses." if reservas_12m and reservas_12m < 0 else "")
                ),
                "simple": (
                    "Los ahorros de emergencia de Chile se estan achicando. Si bajan mucho, "
                    "los inversionistas se ponen nerviosos porque Chile tendria menos "
                    "capacidad de defender su moneda en una crisis. Es como cuando una "
                    "familia ve que sus ahorros bajan mes a mes — genera inseguridad."
                ),
                "indicators": ["reservas_intl"],
            })

    # ─────────────────────────────────────────────
    # REGLA 17: UF y Costo de Vivienda
    # ─────────────────────────────────────────────
    if uf and uf["value"] is not None:
        uf_val = uf["value"]
        uf_12m = _pct_change("uf", 12)

        if uf_12m is not None:
            insights.append({
                "category": "VIVIENDA Y UF",
                "title": f"UF en ${uf_val:,.0f} ({uf_12m:+.1f}% en 12M)",
                "severity": "warning" if uf_12m > 5 else "info",
                "signal": "risk" if uf_12m > 5 else "neutral",
                "detail": (
                    f"La UF sube {uf_12m:+.1f}% en 12 meses (${uf_val:,.0f}). "
                    f"La UF refleja la inflacion acumulada y afecta directamente "
                    f"dividendos hipotecarios, arriendos, y seguros."
                    + (" Subida fuerte que golpea a deudores hipotecarios." if uf_12m > 5 else
                       " Ritmo moderado y manejable." if uf_12m < 4 else "")
                ),
                "simple": (
                    f"La UF esta en ${uf_val:,.0f}. Si tienes credito hipotecario, tu "
                    f"dividendo esta en UF — entonces cada vez que la UF sube, pagas mas "
                    f"en pesos por tu casa. "
                    + (f"Este ano subio {uf_12m:.1f}%, lo que significa que alguien que "
                       f"paga 15 UF de dividendo ahora paga ~${15 * uf_val * uf_12m / 100:,.0f} "
                       f"pesos MAS al mes que hace un ano. " if uf_12m > 0 else "")
                    + "La UF tambien afecta seguros de salud, contratos de arriendo, "
                    "y muchos planes de ahorro. Es la medida invisible que sube el costo "
                    "de vivir en Chile."
                ),
                "indicators": ["uf"],
            })

    # ─────────────────────────────────────────────
    # REGLA 18: Cuenta Corriente y Posición Externa
    # ─────────────────────────────────────────────
    if cc and cc["value"] is not None:
        cc_val = cc["value"]
        if cc_val < -2000:
            insights.append({
                "category": "SECTOR EXTERNO",
                "title": f"Deficit de cuenta corriente: US${cc_val:,.0f}M",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"Chile gasta US${abs(cc_val):,.0f}M mas de lo que recibe del exterior "
                    f"este trimestre. Deficit persistente requiere financiamiento externo "
                    f"(deuda o inversion extranjera) que puede secarse en tiempos de crisis."
                ),
                "simple": (
                    "Chile esta gastando mas plata afuera de la que recibe. Es como una "
                    "familia que compra mas de lo que vende — la diferencia la cubre con "
                    "deuda o vendiendo activos. Si esto sigue mucho tiempo, Chile depende "
                    "de que otros paises le sigan prestando plata. Y cuando hay crisis "
                    "global, esa plata deja de llegar."
                ),
                "indicators": ["cuenta_corriente"],
            })
        elif cc_val > 0:
            insights.append({
                "category": "SECTOR EXTERNO",
                "title": f"Superavit de cuenta corriente: US${cc_val:,.0f}M",
                "severity": "info",
                "signal": "bullish",
                "detail": (
                    f"Chile recibe US${cc_val:,.0f}M mas del exterior de lo que gasta "
                    f"este trimestre. Posicion externa favorable, reduce necesidad de "
                    f"financiamiento externo."
                ),
                "simple": (
                    "Chile esta recibiendo mas plata del extranjero de la que gasta. "
                    "Es como cuando tu negocio vende mas de lo que compra — te sobra plata. "
                    "Eso fortalece la moneda y hace que Chile no necesite pedir prestado afuera."
                ),
                "indicators": ["cuenta_corriente"],
            })

    # ─────────────────────────────────────────────
    # REGLA 19: Base Monetaria y Liquidez
    # ─────────────────────────────────────────────
    base_mon = _latest("base_monetaria")
    if base_mon and base_mon["value"] is not None:
        base_12m = _pct_change("base_monetaria", 12)
        if base_12m is not None and abs(base_12m) > 5:
            expanding = base_12m > 0
            insights.append({
                "category": "LIQUIDEZ MONETARIA",
                "title": f"Base monetaria {'se expande' if expanding else 'se contrae'} {abs(base_12m):.1f}% anual",
                "severity": "info",
                "signal": "neutral",
                "detail": (
                    f"La base monetaria varia {base_12m:+.1f}% en 12 meses. "
                    + ("Expansion: hay mas dinero circulando. Puede estimular la economia "
                       "pero tambien generar inflacion si es excesiva." if expanding else
                       "Contraccion: hay menos dinero circulando. Puede frenar la inflacion "
                       "pero tambien enfriar la economia.")
                ),
                "simple": (
                    "La base monetaria es cuanta plata 'imprime' el Banco Central. "
                    + ("Ahora hay mas pesos circulando que hace un ano. Es como si hubiera "
                       "mas agua en la caneria — las cosas se mueven mas facil, pero si hay "
                       "demasiada agua se puede desbordar (inflacion)." if expanding else
                       "Ahora hay menos pesos circulando. Es como cerrar un poco la llave "
                       "del agua — las cosas se mueven mas lento, pero se controla la presion "
                       "de precios.")
                ),
                "indicators": ["base_monetaria"],
            })

    # ─────────────────────────────────────────────
    # REGLA 20: Credibilidad del BCCh (dispersión de expectativas TPM)
    # ─────────────────────────────────────────────
    # Usa EOF TPM a distintos horizontes (1m, 11m, 23m) — datos confiables y actuales
    eof_tpm_1m_data = _latest("eof_tpm_1m")
    eof_tpm_23m_data = _latest("eof_tpm_23m")
    if (eof_tpm_1m_data and eof_tpm_23m_data
            and not _is_stale(eof_tpm_1m_data, 6) and not _is_stale(eof_tpm_23m_data, 6)
            and eof_tpm_1m_data["value"] is not None and eof_tpm_23m_data["value"] is not None):
        eof_1_val = eof_tpm_1m_data["value"]
        eof_23_val = eof_tpm_23m_data["value"]
        eof_spread = abs(eof_23_val - eof_1_val)

        direction = "recortes" if eof_23_val < eof_1_val else "alzas" if eof_23_val > eof_1_val else "estabilidad"

        if eof_spread > 0.50:
            # Alta divergencia — incertidumbre significativa
            insights.append({
                "category": "CREDIBILIDAD MONETARIA",
                "title": f"Divergencia en expectativas de tasas (spread {eof_spread:.2f}%)",
                "severity": "warning",
                "signal": "neutral",
                "detail": (
                    f"El spread entre expectativas de TPM a corto plazo ({eof_1_val}%) y largo plazo "
                    f"({eof_23_val}%) es de {eof_spread:.2f}%. Los operadores financieros no coinciden "
                    f"sobre la trayectoria de la politica monetaria. Esta incertidumbre encarece el "
                    f"credito y dificulta la planificacion de hogares y empresas."
                ),
                "simple": (
                    "Los expertos financieros no se ponen de acuerdo sobre lo que va a pasar "
                    "con las tasas. Cuando hay desacuerdo, los bancos cobran mas por la duda "
                    "y las empresas no saben si invertir o esperar."
                ),
                "indicators": ["eof_tpm_1m", "eof_tpm_23m"],
            })
        elif eof_spread > 0.15:
            # Consenso razonable — se espera ajuste moderado
            insights.append({
                "category": "CREDIBILIDAD MONETARIA",
                "title": f"Mercado anticipa {direction} moderados de TPM (spread {eof_spread:.2f}%)",
                "severity": "info",
                "signal": "safe",
                "detail": (
                    f"El spread entre expectativas de TPM a corto plazo ({eof_1_val}%) y largo plazo "
                    f"({eof_23_val}%) es de {eof_spread:.2f}%. El mercado anticipa {direction} "
                    f"graduales, con razonable consenso sobre la direccion. Este nivel de previsibilidad "
                    f"reduce la prima por incertidumbre y facilita la planificacion financiera."
                ),
                "simple": (
                    f"Los expertos financieros esperan que las tasas se muevan un poco "
                    f"({direction}), pero estan bastante de acuerdo en la direccion. "
                    f"Cuando hay consenso, los bancos cobran menos por la duda y las empresas "
                    f"pueden planificar con mas certeza."
                ),
                "indicators": ["eof_tpm_1m", "eof_tpm_23m"],
            })
        else:
            # Pleno consenso — el mercado espera estabilidad
            insights.append({
                "category": "CREDIBILIDAD MONETARIA",
                "title": f"Pleno consenso en expectativas de TPM: ~{eof_1_val}%",
                "severity": "info",
                "signal": "safe",
                "detail": (
                    f"EOF TPM a 1 mes ({eof_1_val}%) y a 23 meses ({eof_23_val}%) "
                    f"estan practicamente alineados (spread: {eof_spread:.2f}%). "
                    f"El mercado tiene alta certidumbre sobre la trayectoria de tasas. "
                    f"Eso ancla las expectativas y facilita la planificacion financiera."
                ),
                "simple": (
                    "Los expertos financieros coinciden en que la tasa de interes "
                    "va a mantenerse estable. Cuando hay consenso, las empresas invierten "
                    "con mas confianza y los bancos no necesitan cobrar prima por incertidumbre."
                ),
                "indicators": ["eof_tpm_1m", "eof_tpm_23m"],
            })

    # ─────────────────────────────────────────────
    # REGLA 21: Escenario Stress — Qué pasa si cobre cae 30%
    # ─────────────────────────────────────────────
    if cobre and cobre["value"] is not None and exp_min and exp_min["value"] is not None:
        cobre_val = cobre["value"]
        # Usar exportaciones de cobre (no minería total) para estimar pérdida
        _exp_cobre = exp_cobre["value"] if exp_cobre and exp_cobre.get("value") else exp_min["value"] * 0.82
        cobre_stress = cobre_val * 0.7
        revenue_loss = _exp_cobre * 0.3  # ~30% menos ingresos de cobre

        insights.append({
            "category": "STRESS TEST",
            "title": f"Que pasa si el cobre cae 30% (a US${cobre_stress:.2f}/lb)",
            "severity": "info",
            "signal": "neutral",
            "detail": (
                f"Escenario: cobre baja de US${cobre_val:.2f} a US${cobre_stress:.2f}/lb. "
                f"Impacto estimado: ~US${revenue_loss:,.0f}M menos en exportaciones de cobre "
                f"mensuales. El dolar subiria fuertemente, la recaudacion fiscal caeria, "
                f"y las regiones mineras (Antofagasta, Atacama) sufririan desempleo."
            ),
            "simple": (
                f"Este es un ejercicio de 'que pasaria si'. Si el cobre cayera 30% "
                f"(cosa que ha pasado antes), Chile perderia ~US${revenue_loss:,.0f} "
                f"millones AL MES en exportaciones. El dolar se dispararía, la bencina "
                f"subiria, y miles de personas en el norte perderian su empleo. "
                f"Es el peor escenario para Chile y el motivo por el cual el gobierno "
                f"deberia tener siempre un plan B. Los paises inteligentes ahorran "
                f"cuando el cobre esta caro para gastar cuando esta barato."
            ),
            "indicators": ["cobre", "export_mineras"],
        })

    # ─────────────────────────────────────────────
    # REGLA 22: Deuda/PIB en contexto histórico
    # ─────────────────────────────────────────────
    if deuda and deuda["value"] is not None:
        deuda_val = deuda["value"]
        deuda_trend = _trend("deuda_pib", 12)  # puede ser None si datos anuales

        if deuda_val > 40:
            # Deuda alta — siempre alertar independiente del trend
            insights.append({
                "category": "SOSTENIBILIDAD FISCAL",
                "title": f"Deuda publica en {deuda_val:.1f}% del PIB — maximo historico",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"La deuda bruta del gobierno central esta en {deuda_val:.1f}% del PIB. "
                    f"Hace 10 anos estaba bajo 20%. Chile ha mas que duplicado su deuda "
                    f"relativa en una decada. Si bien es baja vs paises desarrollados "
                    f"(EEUU ~120%, Japon ~260%), la velocidad de crecimiento preocupa. "
                    f"Menos espacio fiscal para enfrentar la proxima crisis."
                ),
                "simple": (
                    f"Chile debe {deuda_val:.0f} centavos por cada peso que produce al año. "
                    f"Hace 10 años debia menos de 20. Se ha mas que duplicado. "
                    f"Comparado con EEUU (120) o Japon (260) no parece tanto, pero Chile "
                    f"no tiene la capacidad de imprimir dolares como ellos. "
                    f"Es como una persona que gana $1 millon y debe $430 mil — suena "
                    f"manejable, pero si cada año debe mas, eventualmente se complica. "
                    f"El gobierno necesita un plan para frenar esta tendencia."
                ),
                "indicators": ["deuda_pib"],
            })
        elif deuda_trend == "up":
            insights.append({
                "category": "SOSTENIBILIDAD FISCAL",
                "title": f"Deuda publica crece: {deuda_val:.1f}% del PIB y subiendo",
                "severity": "warning" if deuda_val > 35 else "info",
                "signal": "risk" if deuda_val > 35 else "neutral",
                "detail": (
                    f"La deuda bruta del gobierno central sube y esta en {deuda_val:.1f}% "
                    f"del PIB. Hace 10 anos estaba bajo 20%. Si bien es baja vs paises "
                    f"desarrollados, la tendencia al alza reduce el espacio para responder "
                    f"a futuras crisis."
                ),
                "simple": (
                    f"Chile debe {deuda_val:.0f} centavos por cada peso que produce. Hace "
                    f"10 anos debia menos de 20. Comparado con otros paises (EEUU debe 120, "
                    f"Japon mas de 200) no parece tanto, pero lo preocupante es la tendencia: "
                    f"cada ano debe mas. Es como una persona que cada mes gasta un poco "
                    f"mas de lo que gana — al principio no pasa nada, pero eventualmente "
                    f"se complica. El gobierno deberia pensar en como frenar esta tendencia "
                    f"antes de que sea un problema real."
                ),
                "indicators": ["deuda_pib"],
            })

    # ─────────────────────────────────────────────
    # REGLA 23: Inflación Desagregada — Dónde Golpea
    # ─────────────────────────────────────────────
    ipc_alim = _latest("ipc_alimentos")
    ipc_viv = _latest("ipc_vivienda")
    ipc_trans = _latest("ipc_transables")
    ipc_anual = _latest("ipc_anual")
    components = []
    if ipc_alim and ipc_alim["value"] is not None:
        components.append(("Alimentos", ipc_alim["value"]))
    if ipc_viv and ipc_viv["value"] is not None:
        components.append(("Vivienda", ipc_viv["value"]))
    if ipc_trans and ipc_trans["value"] is not None:
        components.append(("Transables", ipc_trans["value"]))

    if len(components) >= 2:
        worst = max(components, key=lambda x: x[1])
        best = min(components, key=lambda x: x[1])
        comp_detail = ", ".join(f"{c[0]} {c[1]:+.2f}%" for c in components)
        ipc_a_val = ipc_anual["value"] if ipc_anual and ipc_anual["value"] is not None else None

        if worst[1] > 0.3:
            insights.append({
                "category": "INFLACION DESAGREGADA",
                "title": f"{worst[0]} lidera alzas de precios ({worst[1]:+.2f}% mensual)",
                "severity": "warning" if worst[1] > 0.5 else "info",
                "signal": "risk" if worst[1] > 0.5 else "neutral",
                "detail": (
                    f"Desglose IPC mensual: {comp_detail}. "
                    + (f"Inflacion anual acumulada: {ipc_a_val:.1f}%. " if ipc_a_val else "")
                    + f"El componente {worst[0]} lidera las alzas. "
                    + ("Los transables caen, lo que indica que la presion viene de precios internos, "
                       "no importados." if ipc_trans and ipc_trans["value"] is not None and ipc_trans["value"] < 0 else "")
                ),
                "simple": (
                    f"Los precios no suben parejo — lo que mas sube es {worst[0].lower()} "
                    f"({worst[1]:+.2f}%). "
                    + ("Eso significa que el supermercado se pone mas caro. " if worst[0] == "Alimentos" else "")
                    + ("Eso significa que el arriendo, dividendo y cuentas basicas suben. " if worst[0] == "Vivienda" else "")
                    + f"Lo que menos sube (o baja) es {best[0].lower()} ({best[1]:+.2f}%). "
                    + "Saber DONDE suben los precios es clave para decidir politica: no es lo mismo "
                    "que suba la comida (afecta a todos) a que suba la vivienda (afecta a arrendatarios)."
                ),
                "indicators": ["ipc_alimentos", "ipc_vivienda", "ipc_transables", "ipc_anual"],
            })
        else:
            insights.append({
                "category": "INFLACION DESAGREGADA",
                "title": f"Precios estables en todas las categorias ({comp_detail})",
                "severity": "info",
                "signal": "safe",
                "detail": (
                    f"Todos los componentes del IPC se mueven dentro de rangos normales: {comp_detail}. "
                    + (f"Inflacion anual: {ipc_a_val:.1f}%. " if ipc_a_val else "")
                    + "No hay presion focalizada en ningun sector."
                ),
                "simple": (
                    "Los precios estan tranquilos en todas las categorias — comida, vivienda, "
                    "y productos importados. Cuando todo sube poquito y parejo, es senal de "
                    "una economia equilibrada."
                ),
                "indicators": ["ipc_alimentos", "ipc_vivienda", "ipc_transables"],
            })

    # ─────────────────────────────────────────────
    # REGLA 24: Salarios vs Inflación — Poder Adquisitivo
    # ─────────────────────────────────────────────
    rem_real = _latest("remuneraciones_real")
    rem_real_12m = _pct_change("remuneraciones_real", 12)
    rem_nom_12m = _pct_change("remuneraciones_nom", 12)
    # Guardia: si el cambio nominal es extremo (>30% o <-30%), es probable un quiebre
    # estructural por cambio de base del INE, no un cambio real.
    if rem_nom_12m is not None and abs(rem_nom_12m) > 30:
        rem_nom_12m = None

    if rem_real_12m is not None and ipc_anual and ipc_anual["value"] is not None:
        ipc_a = ipc_anual["value"]
        if rem_real_12m < -1:
            insights.append({
                "category": "PODER ADQUISITIVO",
                "title": f"Salarios reales caen {rem_real_12m:+.1f}% — la gente pierde poder de compra",
                "severity": "warning" if rem_real_12m < -2 else "info",
                "signal": "bearish",
                "detail": (
                    f"Remuneraciones reales caen {rem_real_12m:+.1f}% en 12 meses. "
                    + (f"Sueldos nominales suben ~{rem_nom_12m:+.1f}% pero inflacion es {ipc_a:.1f}%. " if rem_nom_12m is not None else f"Inflacion de {ipc_a:.1f}% erosiona el poder adquisitivo. ")
                    + "La inflacion le gana a los sueldos — la gente puede comprar menos con lo que gana."
                ),
                "simple": (
                    f"Los precios suben {ipc_a:.1f}% pero los sueldos no alcanzan a compensar. "
                    f"Como los precios suben MAS que los sueldos, tu plata rinde menos. "
                    f"Imagina que ganas $100 mas al mes pero el super te cobra $150 mas — en la "
                    f"practica, eres mas pobre que antes aunque tu sueldo sea mas alto."
                ),
                "indicators": ["remuneraciones_real", "remuneraciones_nom", "ipc_anual"],
            })
        elif rem_real_12m > 1:
            insights.append({
                "category": "PODER ADQUISITIVO",
                "title": f"Salarios reales suben {rem_real_12m:+.1f}% — mejora el poder de compra",
                "severity": "info",
                "signal": "bullish",
                "detail": (
                    f"Remuneraciones reales crecen {rem_real_12m:+.1f}% en 12 meses. "
                    f"Los sueldos le ganan a la inflacion ({ipc_a:.1f}%). La gente puede comprar "
                    f"mas con lo que gana — motor del consumo interno."
                ),
                "simple": (
                    f"Los sueldos suben mas rapido que los precios. Eso significa que tu plata "
                    f"rinde mas — puedes comprar mas con el mismo sueldo. Es la mejor senal "
                    f"para las familias y para la economia, porque la gente con mas poder de "
                    f"compra consume mas, y eso mueve todo."
                ),
                "indicators": ["remuneraciones_real", "ipc_anual"],
            })
        else:
            insights.append({
                "category": "PODER ADQUISITIVO",
                "title": f"Salarios reales estables ({rem_real_12m:+.1f}%)",
                "severity": "info",
                "signal": "neutral",
                "detail": (
                    f"Remuneraciones reales varian {rem_real_12m:+.1f}% en 12 meses — "
                    f"sueldos y precios se mueven a ritmo similar. Sin ganancia ni perdida "
                    f"significativa de poder adquisitivo."
                ),
                "simple": (
                    "Los sueldos y los precios suben mas o menos parejo — tu poder de compra "
                    "no mejora pero tampoco empeora. Es como correr en una cinta: te mueves "
                    "pero no avanzas."
                ),
                "indicators": ["remuneraciones_real", "ipc_anual"],
            })

    # ─────────────────────────────────────────────
    # REGLA 25: Termómetro País — Confianza Ciudadana + Empresarial
    # ─────────────────────────────────────────────
    icc_data = _latest("icc")
    ipec_data = _latest("ipec")
    imce_data = _latest("imce")

    if icc_data and icc_data["value"] is not None:
        icc_val = icc_data["value"]
        ipec_val = ipec_data["value"] if ipec_data and ipec_data["value"] is not None else None
        imce_val = imce_data["value"] if imce_data and imce_data["value"] is not None else None

        ciudadano_pesimista = icc_val < 50
        empresa_optimista = imce_val is not None and imce_val > 50

        if ciudadano_pesimista and empresa_optimista:
            insights.append({
                "category": "TERMOMETRO PAIS",
                "title": f"Divergencia: ciudadanos pesimistas (ICC {icc_val:.0f}) pero empresas optimistas (IMCE {imce_val:.0f})",
                "severity": "warning",
                "signal": "risk",
                "detail": (
                    f"ICC (confianza consumidor) en {icc_val:.1f} — bajo 50 es pesimismo. "
                    + (f"IPEC (percepcion economica) en {ipec_val:.1f}. " if ipec_val else "")
                    + f"Pero IMCE (confianza empresarial) en {imce_val:.1f} — sobre 50 es optimismo. "
                    f"Las empresas ven oportunidades que la gente comun no percibe. Esta "
                    f"divergencia puede indicar que el crecimiento no se distribuye, o que "
                    f"las expectativas empresariales aun no se traducen en empleo y salarios."
                ),
                "simple": (
                    f"Las empresas estan optimistas (IMCE {imce_val:.0f}/100), pero la gente "
                    f"comun no lo siente (ICC {icc_val:.0f}/100). Es como si los duenos de "
                    f"restaurantes dijeran 'el negocio anda bien' pero los clientes dijeran "
                    f"'todo esta caro y no me alcanza'. Cuando esta brecha es grande, hay "
                    f"riesgo de descontento social — la economia crece pero la gente no lo nota."
                ),
                "indicators": ["icc", "ipec", "imce"],
            })
        elif ciudadano_pesimista and not empresa_optimista:
            insights.append({
                "category": "TERMOMETRO PAIS",
                "title": f"Pesimismo generalizado: ciudadanos (ICC {icc_val:.0f}) y empresas "
                         + (f"(IMCE {imce_val:.0f})" if imce_val else ""),
                "severity": "warning",
                "signal": "bearish",
                "detail": (
                    f"Tanto consumidores (ICC {icc_val:.1f}) como empresarios "
                    + (f"(IMCE {imce_val:.1f}) " if imce_val else "")
                    + "muestran pesimismo. Cuando ambos sectores desconfian, la economia "
                    "entra en un circulo vicioso: la gente no gasta, las empresas no invierten, "
                    "y la recesion se profundiza."
                ),
                "simple": (
                    "Ni la gente ni las empresas creen que la economia va a mejorar. Es la "
                    "peor combinacion: nadie quiere arriesgar, nadie quiere gastar, nadie "
                    "quiere invertir. La economia se congela. Romper este ciclo requiere "
                    "senales claras del gobierno y del Banco Central."
                ),
                "indicators": ["icc", "ipec", "imce"],
            })
        elif not ciudadano_pesimista:
            insights.append({
                "category": "TERMOMETRO PAIS",
                "title": f"Confianza ciudadana positiva (ICC {icc_val:.0f})"
                         + (f", empresarial tambien (IMCE {imce_val:.0f})" if empresa_optimista else ""),
                "severity": "info",
                "signal": "bullish",
                "detail": (
                    f"ICC en {icc_val:.1f} — sobre 50, los consumidores son optimistas. "
                    + (f"IMCE en {imce_val:.1f}. " if imce_val else "")
                    + "Cuando la gente tiene confianza, gasta mas, lo que impulsa la economia."
                ),
                "simple": (
                    "La gente cree que las cosas van a mejorar. Cuando hay confianza, la gente "
                    "se atreve a comprar, a pedir creditos, a invertir en su futuro. Eso mueve "
                    "la economia hacia arriba. Es el combustible invisible del crecimiento."
                ),
                "indicators": ["icc", "ipec", "imce"],
            })

    # ─────────────────────────────────────────────
    # REGLA 26: Expectativas TPM Directas (EOF vs TPM real)
    # ─────────────────────────────────────────────
    eof_tpm_1 = _latest("eof_tpm_1m")
    eof_tpm_11 = _latest("eof_tpm_11m")
    eof_tpm_23 = _latest("eof_tpm_23m")

    if tpm and tpm["value"] is not None and eof_tpm_11 and eof_tpm_11["value"] is not None:
        tpm_val = tpm["value"]
        eof_11 = eof_tpm_11["value"]
        eof_23 = eof_tpm_23["value"] if eof_tpm_23 and eof_tpm_23["value"] is not None else None
        diff_11 = eof_11 - tpm_val

        trayectoria = "bajadas" if diff_11 < -0.1 else "subidas" if diff_11 > 0.1 else "estabilidad"
        insights.append({
            "category": "TRAYECTORIA MONETARIA",
            "title": f"Mercado anticipa {trayectoria}: TPM {tpm_val}% → EOF {eof_11:.2f}% (11m)"
                     + (f" → {eof_23:.2f}% (23m)" if eof_23 else ""),
            "severity": "info",
            "signal": "bullish" if diff_11 < -0.2 else "risk" if diff_11 > 0.2 else "neutral",
            "detail": (
                f"TPM actual: {tpm_val}%. EOF a 11 meses: {eof_11:.2f}% (diff: {diff_11:+.2f}%). "
                + (f"EOF a 23 meses: {eof_23:.2f}%. " if eof_23 else "")
                + ("El mercado espera recortes — creditos mas baratos, economia mas dinamica. " if diff_11 < -0.2 else "")
                + ("El mercado espera subidas — creditos mas caros, freno economico. " if diff_11 > 0.2 else "")
                + ("Expectativas ancladas en torno al nivel actual." if abs(diff_11) <= 0.2 else "")
            ),
            "simple": (
                f"Los traders que mueven billones de pesos todos los dias creen que la tasa "
                f"de interes ira de {tpm_val}% a {eof_11:.1f}% en un ano"
                + (f" y a {eof_23:.1f}% en dos anos" if eof_23 else "")
                + ". "
                + ("Eso significa creditos hipotecarios y de consumo mas baratos. Buena "
                   "noticia para quien quiere comprar casa o auto." if diff_11 < -0.2 else "")
                + ("Eso significa creditos mas caros. Mala noticia para deudores." if diff_11 > 0.2 else "")
                + ("Ni mas caro ni mas barato — estabilidad." if abs(diff_11) <= 0.2 else "")
            ),
            "indicators": ["tpm", "eof_tpm_1m", "eof_tpm_11m", "eof_tpm_23m"],
        })

    # ─────────────────────────────────────────────
    # REGLA 27: Expectativas de Crecimiento PIB
    # ─────────────────────────────────────────────
    pib_26 = _latest("eof_pib_2026")
    pib_27 = _latest("eof_pib_2027")

    if pib_26 and pib_26["value"] is not None:
        pib_26_val = pib_26["value"]
        pib_27_val = pib_27["value"] if pib_27 and pib_27["value"] is not None else None

        # Detectar revisiones: comparar con valor de hace 3 meses
        pib_prev = _series("eof_pib_2026",
                           (date.today() - timedelta(days=120)).isoformat(),
                           (date.today() - timedelta(days=60)).isoformat())
        revision = None
        if pib_prev:
            valid_prev = [p for p in pib_prev if p["value"] is not None]
            if valid_prev:
                revision = pib_26_val - valid_prev[-1]["value"]

        insights.append({
            "category": "EXPECTATIVAS CRECIMIENTO",
            "title": f"Chile creceria {pib_26_val:.1f}% en 2026"
                     + (f" y {pib_27_val:.1f}% en 2027" if pib_27_val else "")
                     + (f" (revisado {revision:+.1f}pp)" if revision and abs(revision) > 0.05 else ""),
            "severity": "warning" if pib_26_val < 2 else "info",
            "signal": "bearish" if pib_26_val < 1.5 else "neutral" if pib_26_val < 3 else "bullish",
            "detail": (
                f"La Encuesta de Operadores Financieros proyecta un crecimiento de {pib_26_val:.1f}% "
                f"para Chile en 2026"
                + (f" y {pib_27_val:.1f}% en 2027" if pib_27_val else "")
                + ". "
                + (f"Revision de {revision:+.2f}pp respecto a hace 3 meses. " if revision and abs(revision) > 0.05 else "")
                + ("Crecimiento insuficiente para reducir desempleo significativamente. " if pib_26_val < 2.5 else "")
                + ("Chile necesita crecer sobre 3% sostenidamente para mejorar indicadores sociales." if pib_26_val < 3 else "")
            ),
            "simple": (
                f"Los expertos creen que la economia chilena crecera {pib_26_val:.1f}% este ano. "
                + ("Eso es muy poco — a ese ritmo no se crean suficientes empleos ni se "
                   "recauda lo necesario. Chile necesita crecer al menos 3% para que la "
                   "gente lo sienta." if pib_26_val < 2.5 else "")
                + ("Es un ritmo moderado — la economia se mueve, pero no rapido." if 2.5 <= pib_26_val < 3.5 else "")
                + ("Buen ritmo de crecimiento — genera empleo y mejora los ingresos." if pib_26_val >= 3.5 else "")
                + (f" Para 2027, la proyeccion es {pib_27_val:.1f}%." if pib_27_val else "")
            ),
            "indicators": ["eof_pib_2026", "eof_pib_2027"],
        })

    # ─────────────────────────────────────────────
    # REGLA 28: Balanza Comercial y Diversificación
    # ─────────────────────────────────────────────
    bc = _latest("balanza_comercial")
    exp_tot = _latest("export_total")
    imp_tot = _latest("import_total")
    exp_lit = _latest("export_litio")

    if bc and bc["value"] is not None and exp_tot and exp_tot["value"] is not None:
        bc_val = bc["value"]
        exp_val = exp_tot["value"]
        imp_val = imp_tot["value"] if imp_tot and imp_tot["value"] is not None else None
        lit_val = exp_lit["value"] if exp_lit and exp_lit["value"] is not None else None
        min_val = exp_min["value"] if exp_min and exp_min["value"] is not None else None

        # Concentración: % mineras sobre total
        conc_pct = (min_val / exp_val * 100) if min_val and exp_val > 0 else None

        insights.append({
            "category": "COMERCIO EXTERIOR",
            "title": (f"Superavit comercial US${bc_val:,.0f}M" if bc_val > 0
                      else f"Deficit comercial US${abs(bc_val):,.0f}M")
                     + (f" — mineria es {conc_pct:.0f}% del total" if conc_pct else ""),
            "severity": "info" if bc_val > 0 else "warning",
            "signal": "bullish" if bc_val > 500 else "bearish" if bc_val < -500 else "neutral",
            "detail": (
                f"Exportaciones: US${exp_val:,.0f}M"
                + (f", Importaciones: US${imp_val:,.0f}M" if imp_val else "")
                + f". Saldo: US${bc_val:+,.0f}M. "
                + (f"Mineria representa {conc_pct:.0f}% de las exportaciones. " if conc_pct else "")
                + (f"Litio: US${lit_val:,.0f}M ({lit_val/exp_val*100:.1f}% del total). " if lit_val and exp_val > 0 else "")
                + ("Chile vende mas al mundo de lo que compra — posicion externa solida." if bc_val > 0 else
                   "Chile compra mas de lo que vende — necesita financiamiento externo.")
            ),
            "simple": (
                f"Chile exporta US${exp_val/1000:,.1f} mil millones al mes"
                + (f" y compra US${imp_val/1000:,.1f} mil millones" if imp_val else "")
                + ". "
                + (f"Le sobran US${bc_val/1000:,.1f} mil millones — buen negocio. " if bc_val > 0 else
                   f"Le faltan US${abs(bc_val)/1000:,.1f} mil millones — tiene que pedir prestado. ")
                + (f"Del total que vende, {conc_pct:.0f}% es mineria. " if conc_pct else "")
                + (f"El litio (el 'oro blanco') ya aporta US${lit_val:,.0f}M al mes — "
                   f"es la apuesta de Chile para depender menos del cobre." if lit_val and lit_val > 50 else "")
            ),
            "indicators": ["balanza_comercial", "export_total", "import_total", "export_litio", "export_mineras"],
        })

    # ─────────────────────────────────────────────
    # REGLA 29: Crédito Bancario — Pulso del Sistema Financiero
    # ─────────────────────────────────────────────
    col = _latest("colocaciones")
    col_12m = _pct_change("colocaciones", 12)
    spr = _latest("spread_bancario")
    cap = _latest("tasa_captacion")

    if col and col["value"] is not None and spr and spr["value"] is not None:
        col_val = col["value"]
        spr_val = spr["value"]
        cap_val = cap["value"] if cap and cap["value"] is not None else None
        tasa_col = (cap_val + spr_val) if cap_val else None

        insights.append({
            "category": "SISTEMA FINANCIERO",
            "title": f"Credito bancario: ${col_val/1000:,.0f}B"
                     + (f" ({col_12m:+.1f}% anual)" if col_12m else "")
                     + f" | spread {spr_val:.1f}%",
            "severity": "warning" if (col_12m and col_12m < 0) or spr_val > 5 else "info",
            "signal": "risk" if (col_12m and col_12m < -3) or spr_val > 5 else
                      "bullish" if col_12m and col_12m > 5 else "neutral",
            "detail": (
                f"Colocaciones totales: ${col_val:,.0f}MM. "
                + (f"Crecimiento 12M: {col_12m:+.1f}%. " if col_12m else "")
                + f"Spread bancario: {spr_val:.2f}% (diferencia entre tasa de prestamo y deposito). "
                + (f"Tasa de captacion: {cap_val:.2f}%. " if cap_val else "")
                + (f"Tasa implicita de credito: ~{tasa_col:.1f}%. " if tasa_col else "")
                + ("Spread alto encarece el credito y frena la economia. " if spr_val > 4.5 else "")
                + ("Credito cayendo — los bancos prestan menos o la demanda de prestamos baja." if col_12m and col_12m < 0 else "")
            ),
            "simple": (
                f"Los bancos tienen ${col_val/1000:,.0f} billones de pesos prestados. "
                + ("Estan prestando menos que hace un ano — senal de que la economia se enfria "
                   "o que los bancos tienen miedo de no cobrar." if col_12m and col_12m < 0 else "")
                + ("Estan prestando mas — la gente y las empresas piden creditos, lo que "
                   "significa que creen en el futuro." if col_12m and col_12m > 3 else "")
                + f" Los bancos ganan {spr_val:.1f}% de diferencia entre lo que pagan por "
                f"depositos y lo que cobran por prestamos. "
                + ("Eso es bastante — el credito es caro para la gente." if spr_val > 4 else
                   "Eso es normal." if spr_val > 2.5 else "Spread bajo — credito barato.")
            ),
            "indicators": ["colocaciones", "spread_bancario", "tasa_captacion"],
        })

    # ─────────────────────────────────────────────
    # REGLA 30: Liquidez — M1 vs M2 y Velocidad del Dinero
    # ─────────────────────────────────────────────
    m1_data = _latest("m1")
    m2_data = _latest("m2")
    m1_12m = _pct_change("m1", 12)
    m2_12m = _pct_change("m2", 12)

    if m1_data and m1_data["value"] is not None and m2_data and m2_data["value"] is not None:
        m1_val = m1_data["value"]
        m2_val = m2_data["value"]
        ratio_m1_m2 = m1_val / m2_val * 100 if m2_val > 0 else None
        _m1_str = f"{m1_12m:+.1f}%" if m1_12m is not None else "N/D"
        _m2_str = f"{m2_12m:+.1f}%" if m2_12m is not None else "N/D"

        insights.append({
            "category": "LIQUIDEZ MONETARIA",
            "title": f"M1 {_m1_str}, M2 {_m2_str} anual"
                     + (f" — ratio M1/M2: {ratio_m1_m2:.0f}%" if ratio_m1_m2 else ""),
            "severity": "warning" if (m1_12m and abs(m1_12m) > 15) else "info",
            "signal": "risk" if (m1_12m and m1_12m > 15) else
                      "neutral",
            "detail": (
                f"M1 (dinero liquido): ${m1_val:,.0f}MM ({_m1_str} 12M). "
                f"M2 (incluye plazo): ${m2_val:,.0f}MM ({_m2_str} 12M). "
                + (f"Ratio M1/M2: {ratio_m1_m2:.1f}%. " if ratio_m1_m2 else "")
                + ("Alto ratio indica preferencia por liquidez (gente no ahorra a plazo, "
                   "desconfia o necesita el dinero a mano)." if ratio_m1_m2 and ratio_m1_m2 > 35 else "")
                + ("Ratio bajo indica que el dinero esta en depositos a plazo (ahorro "
                   "funciona, tasas de captacion atractivas)." if ratio_m1_m2 and ratio_m1_m2 < 25 else "")
                + ("Ratio en rango normal — el equilibrio entre dinero liquido y depositos "
                   "a plazo es saludable." if ratio_m1_m2 and 25 <= ratio_m1_m2 <= 35 else "")
            ),
            "simple": (
                "M1 es la plata 'en el bolsillo' — efectivo y cuentas corrientes. "
                "M2 suma los depositos a plazo (plata guardada en el banco). "
                + (f"M1 crece {m1_12m:+.1f}% — hay mas plata circulando, lo que puede estimular "
                   "la economia pero tambien generar inflacion." if m1_12m and m1_12m > 5 else "")
                + (f"M1 cae {m1_12m:+.1f}% — hay menos plata en la calle, la economia se "
                   "puede enfriar." if m1_12m and m1_12m < -5 else "")
                + (" La plata se mueve a ritmo normal." if m1_12m and abs(m1_12m) <= 5 else "")
            ),
            "indicators": ["m1", "m2"],
        })

    # ─────────────────────────────────────────────
    # REGLA 31: Tipo de Cambio Real — Competitividad Precio
    # ─────────────────────────────────────────────
    tcr_data = _latest("tcr")
    tcr_12m = _pct_change("tcr", 12)

    if tcr_data and tcr_data["value"] is not None:
        tcr_val = tcr_data["value"]
        insights.append({
            "category": "COMPETITIVIDAD PRECIO",
            "title": f"Tipo cambio real: {tcr_val:.1f} "
                     + ("(Chile barato para exportar)" if tcr_val > 100 else
                        "(Chile caro para exportar)" if tcr_val < 90 else "(rango normal)"),
            "severity": "info" if 85 < tcr_val < 110 else "warning",
            "signal": "bullish" if tcr_val > 100 else "bearish" if tcr_val < 85 else "neutral",
            "detail": (
                f"TCR en {tcr_val:.1f} (base 100 = promedio historico). "
                + (f"Variacion 12M: {tcr_12m:+.1f}%. " if tcr_12m else "")
                + ("TCR alto: los productos chilenos son baratos en el exterior — bueno para "
                   "exportaciones, malo para importaciones." if tcr_val > 100 else "")
                + ("TCR bajo: Chile es caro en dolares — las exportaciones pierden "
                   "competitividad pero importar es mas barato." if tcr_val < 90 else "")
                + ("TCR en equilibrio." if 90 <= tcr_val <= 100 else "")
            ),
            "simple": (
                f"El tipo de cambio real ({tcr_val:.0f}) mide si Chile es 'caro' o 'barato' "
                f"comparado con otros paises. 100 es el promedio historico. "
                + ("Ahora Chile es relativamente barato — eso ayuda a exportar porque nuestros "
                   "productos son mas competitivos. Pero tambien significa que importar es caro." if tcr_val > 100 else "")
                + ("Chile esta en su promedio historico." if 90 <= tcr_val <= 100 else "")
                + ("Chile esta caro — nuestras exportaciones (fuera de cobre) son menos "
                   "competitivas. Pero los viajes al exterior son mas baratos." if tcr_val < 90 else "")
            ),
            "indicators": ["tcr"],
        })

    # ─────────────────────────────────────────────
    # REGLA 32: Deuda Externa Total
    # ─────────────────────────────────────────────
    dext_cp = _latest("deuda_ext_cp")
    dext_lp = _latest("deuda_ext_lp")

    if dext_cp and dext_cp["value"] is not None and dext_lp and dext_lp["value"] is not None:
        cp_val = dext_cp["value"]
        lp_val = dext_lp["value"]
        total_ext = cp_val + lp_val
        cp_pct = cp_val / total_ext * 100 if total_ext > 0 else 0
        # Ratio deuda externa / reservas
        res_val = reservas["value"] if reservas and reservas["value"] is not None else None
        ratio_cp_res = cp_val / res_val if res_val and res_val > 0 else None

        insights.append({
            "category": "DEUDA EXTERNA",
            "title": f"Deuda externa total: US${total_ext/1000:,.0f}B (CP: {cp_pct:.0f}%)",
            "severity": "warning" if (ratio_cp_res and ratio_cp_res > 0.8) else "info",
            "signal": "risk" if (ratio_cp_res and ratio_cp_res > 1.0) else "neutral",
            "detail": (
                f"Deuda externa corto plazo: US${cp_val:,.0f}M. "
                f"Largo plazo: US${lp_val:,.0f}M. "
                f"Total: US${total_ext:,.0f}M (US${total_ext/1000:,.0f}B). "
                + (f"Ratio deuda CP / reservas: {ratio_cp_res:.2f}x. "
                   + ("Las reservas cubren holgadamente la deuda de corto plazo." if ratio_cp_res < 0.6 else "")
                   + ("Las reservas cubren la deuda CP pero sin mucho margen." if 0.6 <= ratio_cp_res < 1.0 else "")
                   + ("La deuda CP supera las reservas — posicion vulnerable." if ratio_cp_res >= 1.0 else "")
                   if ratio_cp_res else "")
            ),
            "simple": (
                f"Chile le debe al mundo US${total_ext/1000:,.0f} mil millones en total. "
                f"De eso, US${cp_val/1000:,.0f}B hay que pagarlos pronto (corto plazo) "
                f"y US${lp_val/1000:,.0f}B son a largo plazo. "
                + (f"Chile tiene US${res_val/1000:,.0f}B en reservas, lo que "
                   + ("cubre la deuda de corto plazo con holgura. " if ratio_cp_res and ratio_cp_res < 0.7 else
                      "apenas cubre la deuda de corto plazo. " if ratio_cp_res and ratio_cp_res < 1.0 else
                      "NO alcanza a cubrir la deuda de corto plazo — riesgo real. ")
                   if res_val else "")
                + "La deuda a largo plazo no preocupa tanto porque se paga en cuotas. "
                "Lo critico es siempre la de corto plazo."
            ),
            "indicators": ["deuda_ext_cp", "deuda_ext_lp", "reservas_intl"],
        })

    # ─────────────────────────────────────────────
    # REGLA 33: Litio — El Nuevo Pilar Exportador
    # ─────────────────────────────────────────────
    if exp_lit and exp_lit["value"] is not None and exp_lit["value"] > 0:
        lit_val = exp_lit["value"]
        lit_12m = _pct_change("export_litio", 12)
        lit_pct_exp = (lit_val / exp_tot["value"] * 100) if exp_tot and exp_tot["value"] else None

        insights.append({
            "category": "DIVERSIFICACION",
            "title": f"Litio: US${lit_val:,.0f}M/mes"
                     + (f" ({lit_12m:+.0f}% anual)" if lit_12m else "")
                     + (f" — {lit_pct_exp:.1f}% de exportaciones" if lit_pct_exp else ""),
            "severity": "info",
            "signal": "bullish" if (lit_12m and lit_12m > 20) else "neutral",
            "detail": (
                f"Chile exporta US${lit_val:,.0f}M mensuales en carbonato de litio. "
                + (f"Variacion anual: {lit_12m:+.1f}%. " if lit_12m else "")
                + (f"Representa {lit_pct_exp:.1f}% del total exportado. " if lit_pct_exp else "")
                + "Chile tiene las mayores reservas de litio del mundo. La demanda global "
                "crece por la electrificacion del transporte y almacenamiento de energia. "
                "Es la principal apuesta de diversificacion para reducir la dependencia del cobre."
            ),
            "simple": (
                f"El litio es el 'oro blanco' — se usa en baterias de autos electricos, "
                f"celulares, y almacenamiento de energia solar. Chile tiene las mayores "
                f"reservas del mundo y exporta US${lit_val:,.0f} millones al mes. "
                + ("Esta creciendo fuerte — cada vez es mas importante para Chile. " if lit_12m and lit_12m > 10 else "")
                + (f"Ya es {lit_pct_exp:.1f}% de todo lo que Chile exporta. " if lit_pct_exp else "")
                + "Mientras el mundo se electrifica, el litio chileno sera cada vez mas valioso. "
                "Es la mejor carta de Chile para no depender solo del cobre."
            ),
            "indicators": ["export_litio", "export_total"],
        })

    # Si no se generó ningún insight, agregar uno default
    if not insights:
        insights.append({
            "category": "RESUMEN",
            "title": "Economia en rango normal",
            "severity": "info",
            "signal": "neutral",
            "detail": "No se detectan divergencias, alertas ni senales significativas en este momento.",
            "simple": "Todo parece estar funcionando dentro de lo esperado. Sin alarmas ni sorpresas.",
            "indicators": [],
        })

    return insights
