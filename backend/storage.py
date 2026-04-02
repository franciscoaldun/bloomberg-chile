"""
Capa de almacenamiento SQLite.

Principio "Raw First":
- raw_responses: guarda el JSON completo tal cual viene del API (auditoría)
- series_data: solo parseo mecánico (fecha DD-MM-YYYY → ISO, string → float, NaN → NULL)
- series_meta: metadatos del catálogo

NUNCA se interpola, suaviza, redondea o modifica un valor.
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from config import DB_PATH, SERIES_CATALOG

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Crea las tablas si no existen e inserta metadatos del catálogo."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS raw_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            response_json TEXT NOT NULL,
            http_status INTEGER
        );

        CREATE TABLE IF NOT EXISTS series_data (
            series_id TEXT NOT NULL,
            obs_date TEXT NOT NULL,
            value REAL,
            status_code TEXT,
            PRIMARY KEY (series_id, obs_date)
        );

        CREATE TABLE IF NOT EXISTS series_meta (
            series_id TEXT PRIMARY KEY,
            panel_id TEXT,
            name_es TEXT,
            name_en TEXT,
            frequency TEXT,
            unit TEXT,
            last_updated TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_series_data_date
            ON series_data(series_id, obs_date);

        CREATE INDEX IF NOT EXISTS idx_raw_responses_series
            ON raw_responses(series_id, fetched_at);
    """)

    # Insertar/actualizar metadatos desde el catálogo
    for panel_id, info in SERIES_CATALOG.items():
        cursor.execute(
            """
            INSERT INTO series_meta (series_id, panel_id, name_es, name_en, frequency, unit)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(series_id) DO UPDATE SET
                panel_id = excluded.panel_id,
                name_es = excluded.name_es,
                name_en = excluded.name_en,
                frequency = excluded.frequency,
                unit = excluded.unit
            """,
            (
                info["bcch_id"],
                panel_id,
                info["name_es"],
                info["name_en"],
                info["frequency"],
                info["unit"],
            ),
        )

    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", DB_PATH)


def _parse_bcch_date(date_str: str) -> str | None:
    """
    Parseo mecánico: "DD-MM-YYYY" → "YYYY-MM-DD".
    Si el formato no coincide, retorna None (no inventa).
    """
    try:
        parts = date_str.strip().split("-")
        if len(parts) == 3:
            day, month, year = parts
            return f"{year}-{month}-{day}"
    except (ValueError, AttributeError):
        pass
    return None


def _parse_value(value_str: str) -> float | None:
    """
    Parseo mecánico: string → float.
    "NaN" o cualquier no-numérico → None (NULL en SQLite).
    No redondea. No modifica.
    """
    if value_str is None:
        return None
    try:
        val = float(value_str)
        # float("NaN") es math.nan, lo convertimos a None
        if val != val:  # NaN check sin importar math
            return None
        return val
    except (ValueError, TypeError):
        return None


def store_raw_response(series_id: str, http_status: int, response: dict):
    """Guarda la respuesta cruda del API tal cual, para auditoría."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO raw_responses (series_id, fetched_at, response_json, http_status) VALUES (?, ?, ?, ?)",
        (
            series_id,
            datetime.utcnow().isoformat(),
            json.dumps(response, ensure_ascii=False),
            http_status,
        ),
    )
    conn.commit()
    conn.close()


def store_series_data(series_id: str, response: dict) -> int:
    """
    Parsea observaciones del API y las almacena.

    Solo hace parseo mecánico:
    - Fecha: "DD-MM-YYYY" → "YYYY-MM-DD"
    - Valor: string → float (NaN → NULL)

    Retorna cantidad de observaciones almacenadas.
    """
    series_info = response.get("Series", {})
    observations = series_info.get("Obs")

    if not observations:
        return 0

    conn = get_connection()
    count = 0

    for obs in observations:
        date_iso = _parse_bcch_date(obs.get("indexDateString", ""))
        if date_iso is None:
            continue  # fecha mal formada, la saltamos (no inventamos)

        value = _parse_value(obs.get("value"))
        status = obs.get("statusCode", "")

        conn.execute(
            """
            INSERT INTO series_data (series_id, obs_date, value, status_code)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(series_id, obs_date) DO UPDATE SET
                value = excluded.value,
                status_code = excluded.status_code
            """,
            (series_id, date_iso, value, status),
        )
        count += 1

    # Actualizar timestamp en metadatos
    conn.execute(
        "UPDATE series_meta SET last_updated = ? WHERE series_id = ?",
        (datetime.utcnow().isoformat(), series_id),
    )

    conn.commit()
    conn.close()
    return count


def get_series_data(
    series_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict]:
    """
    Lee datos parseados de la DB.
    Retorna lista de {"date": "YYYY-MM-DD", "value": float|None}.
    Los NULL se retornan como None — el frontend decide cómo mostrarlos.
    """
    conn = get_connection()

    query = "SELECT obs_date, value FROM series_data WHERE series_id = ?"
    params: list = [series_id]

    if from_date:
        query += " AND obs_date >= ?"
        params.append(from_date)
    if to_date:
        query += " AND obs_date <= ?"
        params.append(to_date)

    query += " ORDER BY obs_date ASC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [{"date": row["obs_date"], "value": row["value"]} for row in rows]


def get_latest_value(series_id: str) -> dict | None:
    """Retorna el último valor no-NULL de una serie."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT obs_date, value FROM series_data
        WHERE series_id = ? AND value IS NOT NULL
        ORDER BY obs_date DESC LIMIT 1
        """,
        (series_id,),
    ).fetchone()
    conn.close()

    if row:
        return {"date": row["obs_date"], "value": row["value"]}
    return None


def get_previous_value(series_id: str, before_date: str) -> dict | None:
    """Retorna el valor anterior más reciente (para calcular cambio)."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT obs_date, value FROM series_data
        WHERE series_id = ? AND value IS NOT NULL AND obs_date < ?
        ORDER BY obs_date DESC LIMIT 1
        """,
        (series_id, before_date),
    ).fetchone()
    conn.close()

    if row:
        return {"date": row["obs_date"], "value": row["value"]}
    return None


def get_all_meta() -> list[dict]:
    """Retorna metadatos de todas las series."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM series_meta ORDER BY panel_id").fetchall()
    conn.close()
    return [dict(row) for row in rows]
