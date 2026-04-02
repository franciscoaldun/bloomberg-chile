"""
Cliente API del Banco Central de Chile (BDE).

Principio: este cliente retorna datos RAW del API.
No transforma, no interpola, no redondea. Solo transporta.
"""

import time
import logging
import requests
from config import BCCH_USER, BCCH_PASS, BCCH_API_URL, RATE_LIMIT_DELAY

logger = logging.getLogger(__name__)

_last_request_time = 0.0


def _rate_limit():
    """Espera lo necesario para respetar el rate limit de 3 req/seg."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)
    _last_request_time = time.time()


def get_series(series_id: str, first_date: str, last_date: str) -> dict:
    """
    Obtiene una serie del BCCh.

    Args:
        series_id: Código de la serie (ej: "F022.TPM.TIN.D001.NO.Z.D")
        first_date: Fecha inicio "YYYY-MM-DD"
        last_date: Fecha fin "YYYY-MM-DD"

    Returns:
        dict completo de la respuesta JSON del API, sin modificar.
    """
    _rate_limit()

    params = {
        "user": BCCH_USER,
        "pass": BCCH_PASS,
        "function": "GetSeries",
        "timeseries": series_id,
        "firstdate": first_date,
        "lastdate": last_date,
    }

    try:
        resp = requests.get(BCCH_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("Codigo") != 0:
            logger.error(
                "BCCh API error for %s: [%s] %s",
                series_id,
                data.get("Codigo"),
                data.get("Descripcion"),
            )

        return {
            "http_status": resp.status_code,
            "response": data,
        }

    except requests.exceptions.Timeout:
        logger.error("Timeout fetching %s", series_id)
        return {"http_status": 0, "response": None, "error": "timeout"}

    except requests.exceptions.RequestException as e:
        logger.error("Request error fetching %s: %s", series_id, e)
        return {"http_status": 0, "response": None, "error": str(e)}


def search_series(frequency: str) -> dict:
    """
    Busca series disponibles por frecuencia.

    Args:
        frequency: "DAILY", "MONTHLY", "QUARTERLY", o "ANNUAL"

    Returns:
        dict completo de la respuesta JSON del API, sin modificar.
    """
    _rate_limit()

    params = {
        "user": BCCH_USER,
        "pass": BCCH_PASS,
        "function": "SearchSeries",
        "frequency": frequency,
    }

    try:
        resp = requests.get(BCCH_API_URL, params=params, timeout=60)
        resp.raise_for_status()
        return {"http_status": resp.status_code, "response": resp.json()}

    except requests.exceptions.RequestException as e:
        logger.error("Search error for %s: %s", frequency, e)
        return {"http_status": 0, "response": None, "error": str(e)}
