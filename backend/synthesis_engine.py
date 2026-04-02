"""
Motor de Síntesis Narrativa — Bloomberg Chile

Pipeline de 7 etapas que transforma insights algorítmicos en un informe
narrativo completo. SIN IA, SIN APIs externas. 100% determinístico y portable.

Etapas:
  1. Clasificar insights por sección temática
  2. Detectar contradicciones entre señales
  3. Computar macro-score (-100 a +100)
  4. Agrupar en secciones narrativas
  5. Generar párrafos por sección
  6. Generar resumen ejecutivo
  7. Generar recomendaciones de monitoreo

Cada párrafo es trazable a los insights que lo generan.
DERIVADO: todo lo producido aquí es cálculo propio sobre datos del BCCh.
"""

from datetime import date

import storage
from config import SERIES_CATALOG

# Mapa de acentos para normalizar texto procedente de analysis_engine (ASCII)
# al español correcto para presentación formal.
_ACCENT_MAP = {
    # Sustantivos y adjetivos comunes
    "inflacion": "inflación", "economia": "economía", "economica": "económica",
    "economico": "económico", "politica": "política", "politico": "político",
    "publico": "público", "publica": "pública", "analisis": "análisis",
    "superavit": "superávit", "deficit": "déficit", "credito": "crédito",
    "creditos": "créditos",
    "historico": "histórico", "historica": "histórica", "maximo": "máximo",
    "minimo": "mínimo", "basica": "básica", "basico": "básico",
    "algoritmica": "algorítmica", "algoritmico": "algorítmico",
    "regimen": "régimen", "atencion": "atención", "direccion": "dirección",
    "recesion": "recesión", "inversion": "inversión", "depreciacion": "depreciación",
    "apreciacion": "apreciación", "produccion": "producción", "contraccion": "contracción",
    "diversificacion": "diversificación", "concentracion": "concentración",
    "variacion": "variación", "correlacion": "correlación",
    # Palabras adicionales detectadas en narrativas de insights
    "mas": "más", "ano": "año", "anos": "años",
    "pais": "país", "paises": "países",
    "interes": "interés", "petroleo": "petróleo",
    "tecnologia": "tecnología", "energia": "energía",
    "presion": "presión", "expansion": "expansión",
    "recaudacion": "recaudación", "dinamica": "dinámica",
    "rapido": "rápido", "tambien": "también",
    "solida": "sólida", "implicita": "implícita",
    "proxima": "próxima", "proximo": "próximo",
    # Segunda ronda de detección
    "planificacion": "planificación", "estabilizacion": "estabilización",
    "percepcion": "percepción", "posicion": "posición",
    "electrificacion": "electrificación", "comun": "común",
    "especifico": "específico", "despues": "después",
    "podria": "podría", "deposito": "depósito",
    "prestamo": "préstamo", "liquido": "líquido",
    "decada": "década", "estandar": "estándar",
    "senal": "señal", "brasileno": "brasileño",
    "millon": "millón", "dolares": "dólares",
    "dolar": "dólar", "mineria": "minería",
    "subiria": "subiría", "caeria": "caería",
    "sufririan": "sufrirían", "dia": "día",
    "critico": "crítico", "duenos": "dueños",
    "debia": "debía", "aun": "aún",
    "estan": "están", "creceria": "crecería",
    "bajara": "bajará", "captacion": "captación",
    "desaceleracion": "desaceleración", "reactivacion": "reactivación",
    "depositos": "depósitos", "prestamos": "préstamos",
}


import re as _re

# Pre-compilar patrones de acentos para rendimiento
_ACCENT_PATTERNS = []
for _plain, _accented in _ACCENT_MAP.items():
    _pat = _re.compile(r'\b' + _re.escape(_plain) + r'\b', _re.IGNORECASE)
    _ACCENT_PATTERNS.append((_pat, _accented))


def _fix_accents(text: str) -> str:
    """Normaliza acentos en texto mixto para presentación formal."""
    result = text
    for pattern, accented in _ACCENT_PATTERNS:
        def _replacer(m: _re.Match, _acc=accented) -> str:
            orig = m.group()
            if orig.isupper():
                return _acc.upper()
            if orig[0].isupper():
                return _acc.capitalize()
            return _acc
        result = pattern.sub(_replacer, result)
    # Contextual: "esta" → "está" antes de gerundios (-ando/-endo/-iendo)
    # y participios (-ado/-ido/-ada/-ida), donde siempre es verbo.
    result = _ESTA_GERUND_PAT.sub(_esta_replacer, result)
    result = _ESTA_PREP_PAT.sub(_esta_replacer, result)
    return result


# Patrones contextuales para "esta" → "está" (solo cuando es verbo)
_ESTA_GERUND_PAT = _re.compile(
    r'\b(esta)(\s+\w+(?:ando|endo|iendo|ado|ido|ada|ida)\b)',
    _re.IGNORECASE,
)
_ESTA_PREP_PAT = _re.compile(
    r'\b(esta)(\s+(?:en|casi|bajo|sobre|entre|más)\b)',
    _re.IGNORECASE,
)


def _esta_replacer(m: _re.Match) -> str:
    orig = m.group(1)
    rest = m.group(2)
    if orig.isupper():
        return "ESTÁ" + rest
    if orig[0].isupper():
        return "Está" + rest
    return "está" + rest


# ═══════════════════════════════════════════════════════════════════════
# 1. DEFINICIÓN DE SECCIONES
# ═══════════════════════════════════════════════════════════════════════

SECTIONS = [
    {
        "id": "monetary",
        "title": "PULSO MONETARIO",
        "subtitle": "Tasas, curva de rendimiento y expectativas",
        "categories": [
            "POLITICA MONETARIA", "CURVA DE RENDIMIENTO", "EXPECTATIVAS",
            "TASA REAL", "CREDIBILIDAD MONETARIA", "TRAYECTORIA MONETARIA",
            "SENAL DE RECESION",
        ],
    },
    {
        "id": "prices",
        "title": "PRECIOS Y PODER ADQUISITIVO",
        "subtitle": "Inflación, componentes, salarios y costo de vida",
        "categories": [
            "INFLACION", "INFLACION DESAGREGADA", "VIVIENDA Y UF",
            "PODER ADQUISITIVO", "COSTO DE VIDA",
        ],
    },
    {
        "id": "growth",
        "title": "MOTOR PRODUCTIVO",
        "subtitle": "Actividad económica, empleo, confianza y expectativas de crecimiento",
        "categories": [
            "CRECIMIENTO", "RENTA VARIABLE", "MERCADO LABORAL",
            "PRESION SOCIAL", "EXPECTATIVAS CRECIMIENTO", "TERMOMETRO PAIS",
            "BIENESTAR SOCIAL", "FAVORABLE",
        ],
    },
    {
        "id": "external",
        "title": "VENTANA AL MUNDO",
        "subtitle": "Commodities, comercio exterior, tipo de cambio y cuentas externas",
        "categories": [
            "COBRE Y DOLAR", "COMMODITIES", "COMPETITIVIDAD REGIONAL",
            "SECTOR EXTERNO", "RESERVAS INTERNACIONALES",
            "COMERCIO EXTERIOR", "DIVERSIFICACION", "DEPENDENCIA EXPORTADORA",
            "DIVERGENCIA", "TIPO DE CAMBIO",
        ],
    },
    {
        "id": "financial",
        "title": "SISTEMA FINANCIERO",
        "subtitle": "Crédito bancario, liquidez y agregados monetarios",
        "categories": ["SISTEMA FINANCIERO", "LIQUIDEZ MONETARIA"],
    },
    {
        "id": "sustainability",
        "title": "SOSTENIBILIDAD Y RIESGO",
        "subtitle": "Deuda pública y externa, posición fiscal, competitividad y estrés",
        "categories": [
            "SALUD FISCAL", "SOSTENIBILIDAD FISCAL", "DEUDA EXTERNA",
            "STRESS TEST", "COMPETITIVIDAD PRECIO",
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════
# 2. PUNTAJES Y RANGOS
# ═══════════════════════════════════════════════════════════════════════

SIGNAL_SCORES = {
    "bullish": {"info": 5, "warning": 8, "critical": 12},
    "bearish": {"info": -5, "warning": -8, "critical": -12},
    "risk":    {"info": -3, "warning": -5, "critical": -8},
    "safe":    {"info": 3, "warning": 5, "critical": 8},
    "neutral": {"info": 0, "warning": 0, "critical": 0},
}

SCORE_RANGES = [
    (60, 100,  "EXPANSION",   "La economía chilena muestra señales generalizadas de auge",                "#3BBA13"),
    (30, 59,   "CRECIMIENTO", "Condiciones macroeconómicas favorables con riesgos acotados",              "#3BBA13"),
    (10, 29,   "ESTABILIDAD", "Equilibrio macroeconómico con sesgo levemente positivo",                   "#FF9900"),
    (-9, 9,    "NEUTRAL",     "Señales mixtas sin tendencia definida — la economía busca dirección",      "#FF9900"),
    (-29, -10, "CAUTELA",     "Señales incipientes de debilitamiento en múltiples indicadores",           "#FF9900"),
    (-59, -30, "DETERIORO",   "Condiciones desfavorables que requieren atención prioritaria",              "#FF433D"),
    (-100, -60,"CRISIS",      "Señales generalizadas de riesgo sistémico — alerta máxima",                "#FF433D"),
]

SIGNAL_LABELS = {
    "bullish": "FAVORABLE",
    "bearish": "ADVERSO",
    "risk": "RIESGO",
    "safe": "ESTABLE",
    "neutral": "MIXTO",
}

# ═══════════════════════════════════════════════════════════════════════
# 3. CONECTORES NARRATIVOS
# ═══════════════════════════════════════════════════════════════════════

# (señal_previa, señal_actual) → lista de conectores posibles
CONNECTORS = {
    ("bullish", "bullish"):  ["Además, ", "Sumado a esto, ", "En la misma línea, "],
    ("bullish", "risk"):     ["Sin embargo, ", "No obstante, ", "A pesar de esto, "],
    ("bullish", "neutral"):  ["En tanto, ", "Por otro lado, ", "Paralelamente, "],
    ("bullish", "bearish"):  ["En contraste directo, ", "Sin embargo, ", "A contramano, "],
    ("bullish", "safe"):     ["Reforzando este escenario, ", "Contribuyendo a la estabilidad, "],
    ("risk", "risk"):        ["Agravando la situación, ", "En el mismo sentido, ", "Sumando presión, "],
    ("risk", "bullish"):     ["Como contrapeso, ", "Parcialmente compensando, ", "En contraste positivo, "],
    ("risk", "neutral"):     ["Moderando la preocupación, ", "En un plano más neutral, "],
    ("risk", "bearish"):     ["Confirmando la tendencia negativa, ", "En línea con esto, "],
    ("risk", "safe"):        ["Mitigando parcialmente este riesgo, ", "Como factor estabilizador, "],
    ("neutral", "bullish"):  ["En el frente positivo, ", "Como señal alentadora, "],
    ("neutral", "risk"):     ["Como factor de riesgo, ", "Generando preocupación, "],
    ("neutral", "neutral"):  ["Adicionalmente, ", "Respecto a otro indicador, ", "En paralelo, "],
    ("neutral", "bearish"):  ["En terreno negativo, ", "Preocupantemente, "],
    ("neutral", "safe"):     ["Como elemento favorable, ", "En positivo, "],
    ("bearish", "bullish"):  ["No obstante, como contrapunto, ", "En el lado positivo, "],
    ("bearish", "risk"):     ["Incrementando la preocupación, ", "Sumando factores adversos, "],
    ("bearish", "neutral"):  ["Matizando el panorama, ", "En un plano intermedio, "],
    ("bearish", "bearish"):  ["Agravando el cuadro, ", "En la misma dirección, "],
    ("bearish", "safe"):     ["Ofreciendo algo de alivio, ", "Como contrapeso parcial, "],
    ("safe", "bullish"):     ["Reforzando el panorama, ", "Además, "],
    ("safe", "risk"):        ["Sin embargo, ", "Pero atención: ", "No obstante, "],
    ("safe", "neutral"):     ["En tanto, ", "Por otro lado, "],
    ("safe", "bearish"):     ["En contraste, ", "A pesar de esto, "],
    ("safe", "safe"):        ["Igualmente, ", "Sumado a esto, ", "También, "],
}

# ═══════════════════════════════════════════════════════════════════════
# 4. APERTURAS Y CIERRES DE SECCIÓN
# ═══════════════════════════════════════════════════════════════════════

SECTION_OPENINGS = {
    "monetary": {
        "bullish": "La política monetaria chilena transita un ciclo expansivo que favorece la reactivación.",
        "bearish": "El frente monetario presenta condiciones restrictivas que presionan la actividad.",
        "risk":    "Las condiciones monetarias exhiben tensiones que merecen seguimiento cercano.",
        "neutral": "La política monetaria se encuentra en transición, con señales que apuntan en distintas direcciones.",
        "safe":    "Las condiciones monetarias son estables y favorecen un entorno predecible.",
    },
    "prices": {
        "bullish": "El frente de precios opera a favor de la economía y del poder adquisitivo de los hogares.",
        "bearish": "La dinámica de precios genera presión negativa sobre el costo de vida.",
        "risk":    "Los precios encienden señales de alerta que requieren vigilancia.",
        "neutral": "Los precios mantienen una dinámica estable, sin presiones significativas en ninguna dirección.",
        "safe":    "La inflación se mantiene controlada, aliviando la carga sobre hogares y política monetaria.",
    },
    "growth": {
        "bullish": "El motor productivo chileno muestra señales de vigor y dinamismo.",
        "bearish": "La actividad económica se debilita, con señales preocupantes en múltiples frentes.",
        "risk":    "El sector real presenta vulnerabilidades que podrían profundizarse.",
        "neutral": "La actividad económica navega en aguas intermedias, sin tendencia clara.",
        "safe":    "Los indicadores de actividad reflejan estabilidad, con bases sólidas para el crecimiento.",
    },
    "external": {
        "bullish": "El sector externo chileno muestra fortaleza impulsada por commodities y comercio.",
        "bearish": "La posición externa se deteriora, con presión sobre cuentas y tipo de cambio.",
        "risk":    "El frente externo presenta focos de riesgo que demandan atención.",
        "neutral": "El sector externo opera dentro de parámetros normales, sin alarmas generalizadas.",
        "safe":    "La posición externa es sólida, con reservas robustas y balanza comercial favorable.",
    },
    "financial": {
        "bullish": "El sistema financiero opera con dinamismo, canalizando crédito hacia la economía.",
        "bearish": "Las condiciones financieras se endurecen, restringiendo el flujo de crédito.",
        "risk":    "El sistema financiero muestra señales que requieren monitoreo prudencial.",
        "neutral": "El sistema financiero opera dentro de parámetros normales.",
        "safe":    "Las condiciones financieras son saludables y propicias para la intermediación.",
    },
    "sustainability": {
        "bullish": "Los indicadores de sostenibilidad fiscal y externa operan en zona de confort.",
        "bearish": "La sostenibilidad fiscal y externa enfrenta desafíos estructurales significativos.",
        "risk":    "Existen señales de alerta en materia de sostenibilidad que merecen seguimiento.",
        "neutral": "Los indicadores de sostenibilidad se mantienen en rangos manejables, con focos de atención.",
        "safe":    "La posición fiscal y externa es sólida, con márgenes de maniobra adecuados.",
    },
}

SECTION_CLOSINGS = {
    "monetary": {
        "bullish": "En conjunto, las condiciones monetarias favorecen una recuperación sostenida de la demanda interna.",
        "bearish": "El cuadro monetario sugiere condiciones que podrían frenar la inversión y el consumo.",
        "risk":    "Es necesario monitorear de cerca la evolución de las expectativas de tasas y la curva de rendimiento.",
        "neutral": "La dirección final de la política monetaria dependerá de cómo evolucionen la inflación y la actividad.",
        "safe":    "La estabilidad monetaria actual proporciona un ancla para la planificación económica.",
    },
    "prices": {
        "bullish": "La dinámica de precios actual es compatible con una mejora sostenida del bienestar.",
        "bearish": "La erosión del poder adquisitivo podría traducirse en menor consumo y mayor presión social.",
        "risk":    "La evolución de los componentes del IPC será determinante para la política monetaria de los próximos meses.",
        "neutral": "Sin presiones inflacionarias significativas, el foco se mantiene en la evolución de componentes específicos.",
        "safe":    "Los precios contenidos otorgan margen al Banco Central y alivio a los presupuestos familiares.",
    },
    "growth": {
        "bullish": "Los fundamentales de la actividad apuntan a una fase de expansión con bases razonables.",
        "bearish": "El debilitamiento productivo requiere políticas activas para evitar una profundización de la desaceleración.",
        "risk":    "La brecha entre percepción y datos reales es un factor que podría amplificar la desaceleración vía canal de confianza.",
        "neutral": "Las señales mixtas en el sector real reflejan una economía en transición, donde las fuerzas positivas y negativas se equilibran sin definir una tendencia clara.",
        "safe":    "Las bases productivas se mantienen firmes, proporcionando resiliencia ante shocks externos.",
    },
    "external": {
        "bullish": "El sector externo es un pilar de fortaleza para la economía chilena en la coyuntura actual.",
        "bearish": "La vulnerabilidad externa exige cautela en la política económica y diversificación acelerada.",
        "risk":    "La concentración en commodities sigue siendo el principal flanco de vulnerabilidad del sector externo.",
        "neutral": "El balance externo es manejable, pero sensible a movimientos bruscos en el precio del cobre.",
        "safe":    "La solidez externa proporciona colchón ante eventuales turbulencias en los mercados globales.",
    },
    "financial": {
        "bullish": "El dinamismo del crédito es consistente con una economía en fase de recuperación.",
        "bearish": "La contracción del crédito podría amplificar la desaceleración si se prolonga.",
        "risk":    "Conviene vigilar la evolución de los spreads bancarios como indicador adelantado de estrés financiero.",
        "neutral": "El sistema financiero cumple su función intermediadora sin señales de estrés sistémico.",
        "safe":    "La solidez del sistema financiero es un activo para la estabilidad macroeconómica.",
    },
    "sustainability": {
        "bullish": "Los márgenes fiscales y externos actuales permiten absorber shocks sin comprometer la estabilidad.",
        "bearish": "La trayectoria de la deuda requiere correcciones de política para ser sostenible en el mediano plazo.",
        "risk":    "La combinación de deuda elevada y dependencia de commodities configura un escenario que requiere vigilancia permanente.",
        "neutral": "Los indicadores de sostenibilidad se mantienen en zona de manejo, pero sin holgura significativa.",
        "safe":    "La posición fiscal y externa otorga credibilidad y margen de maniobra ante escenarios adversos.",
    },
}

# ═══════════════════════════════════════════════════════════════════════
# 5. DEFINICIONES DE CONTRADICCIONES
# ═══════════════════════════════════════════════════════════════════════

CONTRADICTION_DEFS = [
    {
        "id": "monetary_dilemma",
        "name": "Dilema Monetario",
        "cat_a": "POLITICA MONETARIA",
        "condition_a": lambda i: i["signal"] == "bullish",
        "cat_b": "COSTO DE VIDA",
        "condition_b": lambda i: i["signal"] == "risk",
        "severity": "alta",
        "narrative": (
            "El Banco Central mantiene una postura expansiva (recortando tasas), pero el encarecimiento "
            "del dólar presiona los costos importados. Si bien el IPC mensual está contenido, la "
            "depreciación del CLP encarece combustibles, tecnología y alimentos importados con rezago "
            "de 2-3 meses. Si esta presión de costos se transmite a la inflación general, el BCCh "
            "enfrentará el dilema de elegir entre apoyar el crecimiento (mantener recortes) o "
            "contener precios (pausar o revertir). Este tipo de inflación importada es particularmente "
            "difícil de manejar porque subir tasas fortalece el CLP pero enfría la economía."
        ),
        "simple": (
            "El Banco Central está bajando las tasas para que la economía se mueva, pero el dólar "
            "caro está encareciendo todo lo que Chile importa: bencina, remedios, tecnología. "
            "Si esos precios importados contagian al resto, el Central tendrá que elegir entre "
            "ayudar a la economía o frenar la inflación — no puede hacer las dos cosas."
        ),
    },
    {
        "id": "copper_peso_break",
        "name": "Quiebre Cobre-Peso",
        "cat_a": "COMMODITIES",
        "condition_a": lambda i: i["signal"] == "bullish",
        "cat_b": "COBRE Y DOLAR",
        "condition_b": lambda i: i["signal"] == "risk",
        "severity": "alta",
        "narrative": (
            "El cobre sube con fuerza, pero el peso chileno no se fortalece como dicta la correlación histórica. "
            "Este quiebre sugiere que factores idiosincráticos — riesgo político, flujos de capital, "
            "o percepción de riesgo país — están dominando la dinámica cambiaria por encima de los fundamentales "
            "de términos de intercambio. Es una señal de que algo más profundo está operando."
        ),
        "simple": (
            "Normalmente cuando el cobre sube, el peso chileno se fortalece porque Chile gana más dólares. "
            "Pero ahora el cobre sube y el dólar sigue caro. Algo no está funcionando como debería."
        ),
    },
    {
        "id": "perception_gap",
        "name": "Brecha de Percepción Ciudadana",
        "cat_a": "TERMOMETRO PAIS",
        "condition_a": lambda i: i["signal"] == "risk",
        "cat_b": "EXPECTATIVAS CRECIMIENTO",
        "condition_b": lambda i: i["signal"] in ("bullish", "neutral"),
        "severity": "media",
        "narrative": (
            "Los ciudadanos perciben la economía peor de lo que indican los datos duros y las proyecciones "
            "de crecimiento. Esta brecha de percepción es peligrosa: puede convertirse en una profecía "
            "autocumplida si el pesimismo inhibe el consumo y la inversión. La confianza es un activo "
            "frágil que tarda en recuperarse."
        ),
        "simple": (
            "La gente siente que la economía va mal, pero los números dicen que no está tan mal. "
            "El problema es que si la gente cree que va mal, dejan de comprar y gastar, "
            "y entonces sí empeora de verdad."
        ),
    },
    {
        "id": "trade_fx_disconnect",
        "name": "Desconexión Comercio-Tipo de Cambio",
        "cat_a": "COMERCIO EXTERIOR",
        "condition_a": lambda i: i["signal"] == "bullish",
        "cat_b": "COBRE Y DOLAR",
        "condition_b": lambda i: i["signal"] == "risk",
        "severity": "media",
        "narrative": (
            "Chile registra superávit comercial, lo que normalmente aprecia la moneda. Sin embargo, "
            "el tipo de cambio se mueve en dirección contraria. Esto puede explicarse por salidas "
            "de capital financiero que superan los flujos comerciales, o por un deterioro en la "
            "cuenta financiera que compensa el saldo positivo de bienes."
        ),
        "simple": (
            "Chile vende más de lo que compra al mundo (eso es bueno), pero el dólar sigue subiendo. "
            "Significa que la plata que entra por exportaciones se va por otro lado — inversiones "
            "que se van del país."
        ),
    },
    {
        "id": "credit_contraction_growth",
        "name": "Crédito sin Tracción Productiva",
        "cat_a": "SISTEMA FINANCIERO",
        "condition_a": lambda i: i["signal"] in ("neutral", "bullish"),
        "cat_b": "CRECIMIENTO",
        "condition_b": lambda i: i["signal"] == "bearish",
        "severity": "media",
        "narrative": (
            "El sistema financiero mantiene el flujo de crédito, pero la actividad económica no responde. "
            "Esto puede indicar que el crédito se destina a refinanciamiento o consumo de corto plazo "
            "en lugar de inversión productiva, o que existen restricciones no financieras (regulatorias, "
            "de confianza) que bloquean la transmisión del estímulo crediticio a la economía real."
        ),
        "simple": (
            "Los bancos están prestando plata, pero la economía no crece. El dinero no está "
            "llegando a donde genera empleo y producción — posiblemente se usa para pagar deudas "
            "antiguas, no para crear negocios nuevos."
        ),
    },
    {
        "id": "wage_employment_divergence",
        "name": "Salarios vs Empleo",
        "cat_a": "PODER ADQUISITIVO",
        "condition_a": lambda i: i["signal"] == "bullish",
        "cat_b": "MERCADO LABORAL",
        "condition_b": lambda i: "sube" in i.get("title", "").lower() or i["signal"] == "bearish",
        "severity": "media",
        "narrative": (
            "Los salarios reales mejoran, pero el mercado laboral no acompaña con generación de empleo. "
            "Esto sugiere una recuperación selectiva: los que tienen trabajo ganan más, pero hay menos "
            "personas empleadas. El beneficio se concentra en lugar de distribuirse."
        ),
        "simple": (
            "Los sueldos suben para los que tienen trabajo, pero el desempleo sigue alto. "
            "La mejora económica está llegando solo a una parte de la gente."
        ),
    },
    {
        "id": "business_stock_disconnect",
        "name": "Confianza Empresarial vs Bolsa",
        "cat_a": "TERMOMETRO PAIS",
        "condition_a": lambda i: "optimistas" in i.get("title", "").lower() or "IMCE" in i.get("detail", ""),
        "cat_b": "RENTA VARIABLE",
        "condition_b": lambda i: i["signal"] == "bearish" or "cae" in i.get("title", "").lower(),
        "severity": "baja",
        "narrative": (
            "Las empresas reportan optimismo en sus encuestas de confianza, pero la bolsa no lo refleja. "
            "El mercado de capitales puede estar incorporando información que las encuestas no capturan, "
            "o el optimismo empresarial es selectivo (sectores específicos) y no se traduce en "
            "valorización bursátil amplia."
        ),
        "simple": (
            "Los empresarios dicen estar optimistas, pero la bolsa baja. O los empresarios "
            "se equivocan, o el mercado ve algo que ellos no."
        ),
    },
    {
        "id": "m1_inflation_puzzle",
        "name": "Expansión Monetaria sin Inflación",
        "cat_a": "LIQUIDEZ MONETARIA",
        "condition_a": lambda i: "expan" in i.get("title", "").lower() or i["signal"] == "risk",
        "cat_b": "INFLACION",
        "condition_b": lambda i: i["signal"] == "safe",
        "severity": "baja",
        "narrative": (
            "La base monetaria y los agregados se expanden, pero la inflación permanece contenida. "
            "Este 'rompecabezas de velocidad' sugiere que el dinero adicional no está circulando "
            "activamente en la economía — posiblemente atrapado en el sistema financiero o en "
            "ahorro precautorio de hogares. Si la velocidad del dinero se normaliza, la inflación "
            "podría repuntar con rezago."
        ),
        "simple": (
            "Hay más dinero en la economía, pero los precios no suben. La gente y las empresas "
            "guardan la plata en vez de gastarla. Pero si empiezan a gastar de golpe, "
            "los precios podrían subir rápido."
        ),
    },
    {
        "id": "external_debt_reserves",
        "name": "Deuda Externa vs Reservas",
        "cat_a": "DEUDA EXTERNA",
        "condition_a": lambda i: "crece" in i.get("title", "").lower() or i["signal"] == "risk",
        "cat_b": "RESERVAS INTERNACIONALES",
        "condition_b": lambda i: i["signal"] == "safe",
        "severity": "baja",
        "narrative": (
            "La deuda externa crece pero las reservas se mantienen sólidas, lo que por ahora "
            "preserva la cobertura. Sin embargo, la ratio de cobertura se deteriora gradualmente. "
            "Un shock externo que reduzca las reservas podría cambiar rápidamente la percepción "
            "de solvencia."
        ),
        "simple": (
            "Chile debe más plata al exterior, pero tiene reservas de respaldo. "
            "Por ahora alcanza, pero el colchón se achica lentamente."
        ),
    },
    {
        "id": "fiscal_rate_pressure",
        "name": "Deuda Pública + Tasas Altas",
        "cat_a": "SOSTENIBILIDAD FISCAL",
        "condition_a": lambda i: i["signal"] == "risk",
        "cat_b": "TASA REAL",
        "condition_b": lambda i: i.get("detail", "").find("positiv") >= 0 or i["signal"] == "neutral",
        "severity": "alta",
        "narrative": (
            "La deuda pública crece en un entorno de tasas reales positivas, lo que encarece "
            "significativamente el servicio de la deuda. Cada punto de tasa adicional tiene un "
            "efecto multiplicado sobre el gasto en intereses del fisco, reduciendo el espacio "
            "para inversión pública y programas sociales. Es la combinación más peligrosa "
            "para la sostenibilidad fiscal."
        ),
        "simple": (
            "El gobierno debe más y la deuda le sale más cara porque las tasas están altas. "
            "Más plata se va en pagar intereses y menos queda para lo que la gente necesita."
        ),
    },
    {
        "id": "market_overoptimism",
        "name": "Mercado Demasiado Optimista",
        "cat_a": "TRAYECTORIA MONETARIA",
        "condition_a": lambda i: i["signal"] == "bullish",
        "cat_b": "EXPECTATIVAS",
        "condition_b": lambda i: i["signal"] == "risk",
        "severity": "media",
        "narrative": (
            "El mercado anticipa recortes agresivos de tasas, pero las expectativas de los bonos "
            "sugieren incertidumbre significativa. Si el BCCh no cumple con la trayectoria esperada "
            "por el mercado, podría producirse un repricing brusco en la curva de rendimiento, "
            "con impacto en bonos, crédito y tipo de cambio."
        ),
        "simple": (
            "Los inversionistas apuestan a que el Banco Central va a bajar mucho las tasas. "
            "Pero si no lo hace, los mercados se van a ajustar bruscamente — bonos caen, "
            "el dólar sube, y los créditos se encarecen."
        ),
    },
    {
        "id": "copper_concentration",
        "name": "Superciclo con Dependencia",
        "cat_a": "COMMODITIES",
        "condition_a": lambda i: i["signal"] == "bullish",
        "cat_b": "COMERCIO EXTERIOR",
        "condition_b": lambda i: "mineria" in i.get("title", "").lower() or "63%" in i.get("title", "") or "60%" in i.get("title", ""),
        "severity": "media",
        "narrative": (
            "El superciclo del cobre beneficia a Chile, pero la alta concentración exportadora en "
            "minería (más del 60% del total) es un arma de doble filo. Cada peso de superávit "
            "comercial depende excesivamente de un solo commodity. El litio emerge como diversificación, "
            "pero aún representa una fracción menor del total exportado."
        ),
        "simple": (
            "El cobre nos va bien ahora, pero casi todo lo que Chile exporta es minería. "
            "Si mañana el cobre baja, no tenemos plan B suficiente. El litio ayuda pero es chico todavía."
        ),
    },
]

# ═══════════════════════════════════════════════════════════════════════
# 6. FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════


def _get_data_freshness() -> date | None:
    """Obtiene la fecha más reciente entre las series clave del BCCh."""
    key_series = ["usd_clp", "tpm", "cobre", "ipc_var", "imacec", "ipsa"]
    latest = None
    for panel_id in key_series:
        info = SERIES_CATALOG.get(panel_id)
        if not info:
            continue
        row = storage.get_latest_value(info["bcch_id"])
        if row and row.get("date"):
            try:
                dt = date.fromisoformat(row["date"])
                if latest is None or dt > latest:
                    latest = dt
            except (ValueError, TypeError):
                pass
    return latest


def _find(insights: list[dict], category: str) -> dict | None:
    """Busca un insight por categoría (retorna el primero)."""
    for i in insights:
        if i.get("category") == category:
            return i
    return None


def _find_all(insights: list[dict], category: str) -> list[dict]:
    """Busca TODOS los insights de una categoría."""
    return [i for i in insights if i.get("category") == category]


def _dominant_signal(insights: list[dict]) -> str:
    """Calcula la señal dominante de un grupo de insights."""
    if not insights:
        return "neutral"
    counts = {}
    for i in insights:
        sig = i.get("signal", "neutral")
        weight = 1
        if i.get("severity") == "warning":
            weight = 2
        elif i.get("severity") == "critical":
            weight = 3
        counts[sig] = counts.get(sig, 0) + weight
    return max(counts, key=counts.get)


def _pick(options: list[str], seed: int) -> str:
    """Selección determinística de una opción basada en seed."""
    if not options:
        return ""
    return options[seed % len(options)]


def _get_connector(prev_signal: str | None, current_signal: str, seed: int = 0) -> str:
    """Obtiene conector narrativo entre dos señales consecutivas.

    Usa seed para variar la selección determinísticamente y evitar
    repetición de conectores cuando la misma transición ocurre varias veces.
    """
    if prev_signal is None:
        return ""
    key = (prev_signal, current_signal)
    options = CONNECTORS.get(key, ["Adicionalmente, "])
    return _pick(options, seed)


def _severity_sort_key(insight: dict) -> int:
    """Clave de ordenamiento por severidad (crítico primero)."""
    return {"critical": 0, "warning": 1, "info": 2}.get(insight.get("severity", "info"), 2)


def _count_signals(insights: list[dict]) -> dict[str, int]:
    """Cuenta señales en una lista de insights."""
    counts = {"bullish": 0, "bearish": 0, "risk": 0, "safe": 0, "neutral": 0}
    for i in insights:
        sig = i.get("signal", "neutral")
        if sig in counts:
            counts[sig] += 1
    return counts


# ═══════════════════════════════════════════════════════════════════════
# 7. ETAPA 1: CLASIFICACIÓN
# ═══════════════════════════════════════════════════════════════════════


def classify_insights(insights: list[dict]) -> dict[str, list[dict]]:
    """Clasifica insights en secciones temáticas."""
    classified = {s["id"]: [] for s in SECTIONS}
    cat_to_section = {}
    for s in SECTIONS:
        for cat in s["categories"]:
            cat_to_section[cat] = s["id"]

    for insight in insights:
        cat = insight.get("category", "")
        section_id = cat_to_section.get(cat)
        if section_id:
            classified[section_id].append(insight)

    return classified


# ═══════════════════════════════════════════════════════════════════════
# 8. ETAPA 2: DETECCIÓN DE CONTRADICCIONES
# ═══════════════════════════════════════════════════════════════════════


def detect_contradictions(insights: list[dict]) -> list[dict]:
    """Detecta contradicciones entre insights usando reglas predefinidas.

    Prueba TODAS las combinaciones de insights por categoría para no perder
    contradicciones cuando una categoría genera múltiples insights.
    """
    found = []

    for cdef in CONTRADICTION_DEFS:
        all_a = _find_all(insights, cdef["cat_a"])
        all_b = _find_all(insights, cdef["cat_b"])

        if not all_a or not all_b:
            continue

        cond_a = cdef.get("condition_a")
        cond_b = cdef.get("condition_b")

        # Probar todas las combinaciones, tomar la primera que matchee
        matched = False
        for ia in all_a:
            if matched:
                break
            for ib in all_b:
                a_match = cond_a(ia) if cond_a else True
                b_match = cond_b(ib) if cond_b else True

                if a_match and b_match:
                    found.append({
                        "id": cdef["id"],
                        "name": cdef["name"],
                        "severity": cdef["severity"],
                        "insight_a": {"category": ia["category"], "title": ia["title"], "signal": ia["signal"]},
                        "insight_b": {"category": ib["category"], "title": ib["title"], "signal": ib["signal"]},
                        "narrative": cdef["narrative"],
                        "simple": cdef["simple"],
                    })
                    matched = True
                    break

    return found


# ═══════════════════════════════════════════════════════════════════════
# 9. ETAPA 3: CÓMPUTO DE MACRO-SCORE
# ═══════════════════════════════════════════════════════════════════════


def compute_score(insights: list[dict], contradictions: list[dict]) -> dict:
    """Calcula el macro-score ponderado de -100 a +100."""
    raw_score = 0
    breakdown = []

    for insight in insights:
        signal = insight.get("signal", "neutral")
        severity = insight.get("severity", "info")
        points = SIGNAL_SCORES.get(signal, {}).get(severity, 0)
        raw_score += points
        if points != 0:
            breakdown.append({
                "category": insight["category"],
                "signal": signal,
                "severity": severity,
                "points": points,
            })

    # Penalización por contradicciones: cada una reduce |score| en 3 pts
    contradiction_penalty = len(contradictions) * 3
    if raw_score > 0:
        raw_score = max(0, raw_score - contradiction_penalty)
    elif raw_score < 0:
        raw_score = min(0, raw_score + contradiction_penalty)

    # Normalizar a -100/+100
    max_possible = sum(
        max(abs(v) for v in sev.values())
        for sev in SIGNAL_SCORES.values()
    ) * len(insights) / 5  # factor de escala
    if max_possible > 0:
        normalized = int(round((raw_score / max_possible) * 100))
    else:
        normalized = 0
    normalized = max(-100, min(100, normalized))

    # Determinar rango
    label = "NEUTRAL"
    description = ""
    color = "#FF9900"
    for lo, hi, lbl, desc, clr in SCORE_RANGES:
        if lo <= normalized <= hi:
            label = lbl
            description = desc
            color = clr
            break

    return {
        "value": normalized,
        "raw": raw_score,
        "label": label,
        "description": description,
        "color": color,
        "contradiction_penalty": contradiction_penalty,
        "breakdown": sorted(breakdown, key=lambda b: abs(b["points"]), reverse=True),
    }


# ═══════════════════════════════════════════════════════════════════════
# 10. ETAPA 4-5: GENERACIÓN DE NARRATIVA POR SECCIÓN
# ═══════════════════════════════════════════════════════════════════════


def generate_section_narrative(section_def: dict, section_insights: list[dict],
                                all_insights: list[dict]) -> str:
    """Genera narrativa para una sección del informe."""
    if not section_insights:
        return ""

    section_id = section_def["id"]
    sorted_insights = sorted(section_insights, key=_severity_sort_key)
    dominant = _dominant_signal(section_insights)

    # Apertura
    opening = SECTION_OPENINGS.get(section_id, {}).get(dominant, "")

    # Cuerpo: construir párrafos con los insights
    body_parts = []
    prev_signal = None

    for idx, insight in enumerate(sorted_insights):
        signal = insight.get("signal", "neutral")
        detail = insight.get("detail", "")

        if idx == 0:
            # Primer insight: usar directamente su detalle
            body_parts.append(detail)
        else:
            # Insights subsiguientes: conectar con transición
            connector = _get_connector(prev_signal, signal, seed=idx)
            # Usar primera letra minúscula después del conector si no empieza con nombre propio
            if detail and connector:
                first_char = detail[0]
                if first_char.isupper() and not _is_proper_noun_start(detail):
                    detail_connected = detail[0].lower() + detail[1:]
                else:
                    detail_connected = detail
                body_parts.append(f"{connector}{detail_connected}")
            else:
                body_parts.append(detail)

        prev_signal = signal

    body = " ".join(p.strip() for p in body_parts)

    # Cierre
    closing = SECTION_CLOSINGS.get(section_id, {}).get(dominant, "")

    result = f"{opening} {body} {closing}".strip()
    # Limpiar dobles espacios y normalizar acentos
    while "  " in result:
        result = result.replace("  ", " ")
    return _fix_accents(result)


def _is_proper_noun_start(text: str) -> bool:
    """Verifica si el texto empieza con un nombre propio o acrónimo."""
    proper_starts = [
        "El ", "La ", "Los ", "Las ", "Chile", "BCCh", "BCP", "TPM",
        "IPSA", "IMACEC", "IPC", "USD", "EUR", "UF", "CLP", "PIB",
        "EOF", "SMA", "ICC", "IPEC", "IMCE", "M1", "M2", "M3",
        "Ratio", "TCR", "Spread", "Base", "Colocaciones",
    ]
    return any(text.startswith(p) for p in proper_starts)


# ═══════════════════════════════════════════════════════════════════════
# 11. ETAPA 5b: NARRATIVA DE CONTRADICCIONES
# ═══════════════════════════════════════════════════════════════════════


def generate_contradictions_narrative(contradictions: list[dict]) -> dict:
    """Genera sección narrativa sobre contradicciones detectadas."""
    if not contradictions:
        return {
            "title": "COHERENCIA DE SEÑALES",
            "narrative": (
                "No se detectaron contradicciones significativas entre los indicadores analizados. "
                "Las señales macroeconómicas apuntan en una dirección razonablemente consistente, "
                "lo que aumenta la confianza en el diagnóstico general."
            ),
            "count": 0,
            "items": [],
        }

    # Ordenar por severidad
    sev_order = {"alta": 0, "media": 1, "baja": 2}
    sorted_c = sorted(contradictions, key=lambda c: sev_order.get(c["severity"], 2))

    n = len(sorted_c)
    high = sum(1 for c in sorted_c if c["severity"] == "alta")
    med = sum(1 for c in sorted_c if c["severity"] == "media")

    if high >= 2:
        opening = (
            f"Se detectaron {n} contradicciones entre indicadores, de las cuales {high} son de "
            f"alta severidad. La economía chilena envía señales conflictivas en múltiples frentes, "
            f"lo que dificulta un diagnóstico unívoco y aumenta la incertidumbre de cualquier proyección."
        )
    elif high == 1:
        opening = (
            f"Se identificaron {n} tensiones entre indicadores. Destaca una contradicción de alta "
            f"severidad que merece seguimiento prioritario. Las señales mixtas sugieren que la "
            f"economía está en un punto de inflexión donde distintas fuerzas compiten por la dirección."
        )
    elif med >= 2:
        opening = (
            f"Se detectaron {n} tensiones de severidad moderada entre indicadores. Si bien ninguna "
            f"es crítica por sí sola, su acumulación configura un cuadro de señales mixtas que "
            f"reduce la certeza del panorama."
        )
    else:
        opening = (
            f"Se identificaron {n} discrepancias menores entre indicadores. Son tensiones normales "
            f"en una economía compleja y no alteran significativamente el diagnóstico general."
        )

    items = []
    for c in sorted_c:
        items.append({
            "name": c["name"],
            "severity": c["severity"],
            "narrative": c["narrative"],
            "simple": c["simple"],
            "between": f"{c['insight_a']['category']} ({c['insight_a']['signal']}) vs "
                       f"{c['insight_b']['category']} ({c['insight_b']['signal']})",
        })

    return {
        "title": "TENSIONES Y CONTRADICCIONES",
        "narrative": opening,
        "count": n,
        "high_severity": high,
        "medium_severity": med,
        "items": items,
    }


# ═══════════════════════════════════════════════════════════════════════
# 12. ETAPA 6: RESUMEN EJECUTIVO
# ═══════════════════════════════════════════════════════════════════════


def generate_executive_summary(score: dict, section_narratives: list[dict],
                                contradictions: list[dict], insights: list[dict]) -> str:
    """Genera resumen ejecutivo de 4-6 oraciones."""
    parts = []

    # Oración 1: Score y diagnóstico general
    score_val = score["value"]
    score_label = score["label"]
    score_desc = score["description"]
    parts.append(
        f"El diagnóstico macroeconómico algorítmico arroja un puntaje de {score_val:+d}/100, "
        f"clasificado como \"{score_label}\": {score_desc.lower()}."
    )

    # Oración 2: Señales positivas más fuertes
    bullish_insights = [i for i in insights if i["signal"] == "bullish"]
    if bullish_insights:
        top_bullish = sorted(bullish_insights, key=_severity_sort_key)[:3]
        bulls = ", ".join(_fix_accents(i["title"].split("(")[0].strip().lower()) for i in top_bullish)
        parts.append(f"Las principales señales positivas provienen de: {bulls}.")

    # Oración 3: Señales de riesgo más relevantes
    risk_insights = [i for i in insights if i["signal"] in ("risk", "bearish")]
    if risk_insights:
        top_risk = sorted(risk_insights, key=_severity_sort_key)[:3]
        risks = ", ".join(_fix_accents(i["title"].split("(")[0].strip().lower()) for i in top_risk)
        parts.append(f"Los principales focos de atención: {risks}.")

    # Oración 4: Contradicciones (si las hay)
    high_contradictions = [c for c in contradictions if c["severity"] == "alta"]
    if high_contradictions:
        c_names = " y ".join(c["name"].lower() for c in high_contradictions[:2])
        parts.append(
            f"Se detectaron tensiones significativas ({c_names}), "
            f"lo que añade incertidumbre al panorama y obliga a monitorear con mayor frecuencia."
        )
    elif contradictions:
        parts.append(
            f"Se identificaron {len(contradictions)} tensiones entre indicadores que generan "
            f"señales mixtas en el diagnóstico."
        )

    # Oración 5: Perspectiva
    growth_exp = _find(insights, "EXPECTATIVAS CRECIMIENTO")
    growth_hard = _find(insights, "CRECIMIENTO")
    trajectory = _find(insights, "TRAYECTORIA MONETARIA")

    if growth_exp:
        parts.append(f"De cara al futuro, las expectativas indican que {_fix_accents(growth_exp['title'].lower())}.")
    elif growth_hard:
        parts.append(f"En el frente productivo, {_fix_accents(growth_hard['title'].lower())}.")

    if trajectory and trajectory["signal"] == "bullish":
        parts.append("El mercado descuenta que la TPM seguirá a la baja, lo que debería apoyar la reactivación.")

    # Oración 6: Cierre basado en score
    if score_val >= 30:
        parts.append("En balance, Chile presenta condiciones macroeconómicas que favorecen la inversión y el crecimiento sostenido.")
    elif score_val >= 10:
        parts.append("En balance, la economía opera en equilibrio con sesgo constructivo, pero no exenta de riesgos que ameritan vigilancia.")
    elif score_val >= -9:
        parts.append("El panorama exige cautela: no hay crisis, pero tampoco claridad sobre la dirección, y los riesgos pesan tanto como las oportunidades.")
    elif score_val >= -29:
        parts.append("La balanza se inclina hacia la precaución. Las autoridades y agentes económicos deben preparar contingencias.")
    else:
        parts.append("El diagnóstico es adverso. Se requieren acciones correctivas urgentes para evitar un deterioro mayor.")

    return _fix_accents(" ".join(parts))


# ═══════════════════════════════════════════════════════════════════════
# 13. ETAPA 7: RECOMENDACIONES DE MONITOREO
# ═══════════════════════════════════════════════════════════════════════


def generate_recommendations(score: dict, insights: list[dict],
                              contradictions: list[dict]) -> list[dict]:
    """Genera recomendaciones de monitoreo priorizadas."""
    recs = []

    # Recomendaciones por insights críticos y de warning
    critical_insights = [i for i in insights if i["severity"] == "critical"]
    warning_insights = [i for i in insights if i["severity"] == "warning"]

    for insight in critical_insights:
        recs.append({
            "priority": "ALTA",
            "text": f"ALERTA — {insight['title']}. {insight['simple']}",
            "based_on": [insight["category"]],
            "action": "Monitoreo diario recomendado.",
        })

    # Recomendaciones por contradicciones de alta severidad
    for c in contradictions:
        if c["severity"] == "alta":
            recs.append({
                "priority": "ALTA",
                "text": f"TENSIÓN — {c['name']}: {c['simple']}",
                "based_on": [c["insight_a"]["category"], c["insight_b"]["category"]],
                "action": "Seguir evolución de ambos indicadores simultáneamente.",
            })

    # Recomendaciones por warnings
    for insight in warning_insights:
        recs.append({
            "priority": "MEDIA",
            "text": f"{insight['title']}. {insight['simple']}",
            "based_on": [insight["category"]],
            "action": "Monitoreo semanal recomendado.",
        })

    # Recomendaciones por contradicciones de severidad media
    for c in contradictions:
        if c["severity"] == "media":
            recs.append({
                "priority": "MEDIA",
                "text": f"Tensión entre {c['insight_a']['category']} y {c['insight_b']['category']}: {c['simple']}",
                "based_on": [c["insight_a"]["category"], c["insight_b"]["category"]],
                "action": "Verificar si la divergencia se cierra o se amplía.",
            })

    # Recomendaciones estructurales basadas en score
    score_val = score["value"]
    if score_val < -20:
        recs.append({
            "priority": "ALTA",
            "text": "El macro-score indica deterioro. Evaluar exposición a riesgo Chile y revisar supuestos de crecimiento.",
            "based_on": ["SCORE_MACRO"],
            "action": "Revisión integral de escenarios.",
        })
    elif score_val < 0:
        recs.append({
            "priority": "MEDIA",
            "text": "El macro-score es levemente negativo. Mantener posiciones pero con coberturas activas.",
            "based_on": ["SCORE_MACRO"],
            "action": "Revisión mensual de exposición.",
        })

    # Recomendación de diversificación si hay concentración minera
    ext = _find(insights, "COMERCIO EXTERIOR")
    if ext and "mineria" in ext.get("title", "").lower():
        recs.append({
            "priority": "MEDIA",
            "text": "La dependencia de exportaciones mineras supera el 60%. La diversificación productiva sigue siendo una necesidad estructural.",
            "based_on": ["COMERCIO EXTERIOR", "DIVERSIFICACION"],
            "action": "Monitorear evolución de litio y exportaciones no tradicionales.",
        })

    # Recomendación de confianza si hay brecha
    conf = _find(insights, "TERMOMETRO PAIS")
    if conf and conf["signal"] == "risk":
        recs.append({
            "priority": "MEDIA",
            "text": "La confianza ciudadana está deprimida. El canal de expectativas puede amplificar la desaceleración.",
            "based_on": ["TERMOMETRO PAIS"],
            "action": "Monitorear ICC e IPEC como indicadores adelantados de consumo.",
        })

    # Ordenar por prioridad
    priority_order = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    recs.sort(key=lambda r: priority_order.get(r["priority"], 2))

    # Deduplicar por categorías base
    seen_bases = set()
    unique_recs = []
    for r in recs:
        key = tuple(sorted(r["based_on"]))
        if key not in seen_bases:
            seen_bases.add(key)
            unique_recs.append(r)

    # Normalizar acentos en todos los textos de recomendaciones
    for r in unique_recs:
        r["text"] = _fix_accents(r["text"])
        r["action"] = _fix_accents(r["action"])

    return unique_recs


# ═══════════════════════════════════════════════════════════════════════
# 14. PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════


def synthesize(insights: list[dict]) -> dict:
    """
    Pipeline completo de síntesis narrativa.

    Recibe lista de insights de analysis_engine.run_analysis()
    Retorna informe estructurado con narrativa, score, contradicciones y recomendaciones.
    """
    if not insights:
        return {
            "executive_summary": "No hay datos suficientes para generar un análisis macroeconómico.",
            "macro_score": {"value": 0, "label": "SIN DATOS", "color": "#666666"},
            "sections": [],
            "contradictions": {"count": 0, "items": []},
            "recommendations": [],
            "metadata": {
                "generated": date.today().isoformat(),
                "data_as_of": None,
                "insights_analyzed": 0,
                "derived": True,
                "method": "algorithmic_synthesis_v1",
            },
        }

    # Determinar fecha más reciente de los datos subyacentes
    latest_date = _get_data_freshness()

    # Etapa 1: Clasificar
    classified = classify_insights(insights)

    # Etapa 2: Detectar contradicciones
    contradictions = detect_contradictions(insights)

    # Etapa 3: Computar score
    score = compute_score(insights, contradictions)

    # Etapa 4-5: Generar narrativas por sección
    section_results = []
    for section_def in SECTIONS:
        section_insights = classified.get(section_def["id"], [])
        if not section_insights:
            continue

        narrative = generate_section_narrative(section_def, section_insights, insights)
        dominant = _dominant_signal(section_insights)
        signals = _count_signals(section_insights)

        section_results.append({
            "id": section_def["id"],
            "title": section_def["title"],
            "subtitle": section_def["subtitle"],
            "signal": dominant,
            "signal_label": SIGNAL_LABELS.get(dominant, "MIXTO"),
            "narrative": narrative,
            "insights_count": len(section_insights),
            "categories": list(dict.fromkeys(i["category"] for i in section_insights)),
            "signal_distribution": signals,
        })

    # Etapa 5b: Narrativa de contradicciones
    contradiction_section = generate_contradictions_narrative(contradictions)

    # Etapa 6: Resumen ejecutivo
    executive = generate_executive_summary(score, section_results, contradictions, insights)

    # Etapa 7: Recomendaciones
    recommendations = generate_recommendations(score, insights, contradictions)

    # Compilar informe
    return {
        "executive_summary": executive,
        "macro_score": score,
        "sections": section_results,
        "contradictions": contradiction_section,
        "recommendations": recommendations,
        "signal_summary": {
            "total_insights": len(insights),
            "bullish": sum(1 for i in insights if i["signal"] == "bullish"),
            "bearish": sum(1 for i in insights if i["signal"] == "bearish"),
            "risk": sum(1 for i in insights if i["signal"] == "risk"),
            "safe": sum(1 for i in insights if i["signal"] == "safe"),
            "neutral": sum(1 for i in insights if i["signal"] == "neutral"),
        },
        "metadata": {
            "generated": date.today().isoformat(),
            "data_as_of": latest_date.isoformat() if latest_date else date.today().isoformat(),
            "insights_analyzed": len(insights),
            "contradictions_found": len(contradictions),
            "sections_generated": len(section_results),
            "recommendations_generated": len(recommendations),
            "derived": True,
            "method": "algorithmic_synthesis_v1",
            "note": "Informe generado algorítmicamente a partir de datos del BCCh. No es consejo financiero.",
        },
    }
