"""
Bloomberg Chile — Backend FastAPI

Punto de entrada. Levanta el servidor, inicializa la DB,
y expone los endpoints de datos.
Auto-refresh cada 30 minutos desde el API del Banco Central.
"""

import sys
import asyncio
import logging
import threading
from datetime import date, datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import storage
import bcch_client
from config import SERIES_CATALOG
from routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SEC = 30 * 60  # 30 minutos

# Estado del scheduler — visible desde /api/health
refresh_state = {
    "last_refresh": None,       # ISO timestamp del último refresh completado
    "last_refresh_ok": None,    # True/False resultado del último refresh
    "last_refresh_series": 0,   # Series actualizadas en último refresh
    "last_refresh_obs": 0,      # Observaciones en último refresh
    "next_refresh": None,       # ISO timestamp del próximo refresh programado
    "refreshing": False,        # True si hay un refresh en curso
    "interval_sec": REFRESH_INTERVAL_SEC,
}

_refresh_lock = threading.Lock()


def ingest_all_series():
    """Descarga todas las series del catálogo y las almacena."""
    today = date.today().isoformat()
    total_obs = 0
    series_ok = 0

    for panel_id, info in SERIES_CATALOG.items():
        bcch_id = info["bcch_id"]
        logger.info("Ingesting %s (%s)...", panel_id, bcch_id)

        result = bcch_client.get_series(bcch_id, info["history_start"], today)
        http_status = result.get("http_status", 0)
        response = result.get("response")

        if response is None:
            logger.error("  FAILED: %s", result.get("error", "unknown"))
            continue

        # Guardar respuesta raw completa (auditoría)
        storage.store_raw_response(bcch_id, http_status, response)

        # Parsear y almacenar datos (solo transformación mecánica)
        if response.get("Codigo") == 0:
            count = storage.store_series_data(bcch_id, response)
            total_obs += count
            series_ok += 1
            logger.info("  OK: %d observations stored", count)
        else:
            logger.warning(
                "  API returned code %s: %s",
                response.get("Codigo"),
                response.get("Descripcion"),
            )

    logger.info("Ingestion complete. Total observations: %d", total_obs)
    return series_ok, total_obs


def _run_refresh():
    """Ejecuta ingesta con tracking de estado."""
    if not _refresh_lock.acquire(blocking=False):
        logger.warning("Refresh already in progress, skipping.")
        return
    try:
        refresh_state["refreshing"] = True
        series_ok, total_obs = ingest_all_series()
        refresh_state["last_refresh"] = datetime.now(timezone.utc).isoformat()
        refresh_state["last_refresh_ok"] = True
        refresh_state["last_refresh_series"] = series_ok
        refresh_state["last_refresh_obs"] = total_obs
    except Exception as e:
        logger.error("Refresh failed: %s", e)
        refresh_state["last_refresh"] = datetime.now(timezone.utc).isoformat()
        refresh_state["last_refresh_ok"] = False
    finally:
        refresh_state["refreshing"] = False
        _refresh_lock.release()


async def _auto_refresh_loop():
    """Loop de auto-refresh que corre en background."""
    while True:
        next_time = datetime.now(timezone.utc).timestamp() + REFRESH_INTERVAL_SEC
        refresh_state["next_refresh"] = datetime.fromtimestamp(
            next_time, tz=timezone.utc
        ).isoformat()
        await asyncio.sleep(REFRESH_INTERVAL_SEC)
        logger.info("Auto-refresh triggered.")
        await asyncio.to_thread(_run_refresh)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa DB, ingesta datos, y arranca el auto-refresh."""
    storage.init_db()
    logger.info("Database initialized.")

    # Verificar si hay datos — si no, hacer ingesta inicial
    meta = storage.get_all_meta()
    has_data = any(m.get("last_updated") for m in meta)

    if not has_data:
        logger.info("No data found. Running initial ingestion...")
        _run_refresh()
    else:
        logger.info("Data already present. Skipping initial ingestion.")

    # Arrancar auto-refresh en background
    refresh_task = asyncio.create_task(_auto_refresh_loop())
    logger.info("Auto-refresh scheduled every %d minutes.", REFRESH_INTERVAL_SEC // 60)

    yield

    refresh_task.cancel()


app = FastAPI(
    title="Bloomberg Chile API",
    description="Panel de datos económicos de Chile — Fuente: Banco Central de Chile",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# Endpoint de refresh manual (separado porque ejecuta ingesta)
@app.post("/api/refresh")
async def refresh_data():
    """Trigger manual de re-ingesta de todas las series."""
    if refresh_state["refreshing"]:
        return {"status": "busy", "message": "Refresh already in progress"}
    await asyncio.to_thread(_run_refresh)
    return {
        "status": "ok",
        "message": "All series refreshed",
        "series": refresh_state["last_refresh_series"],
        "observations": refresh_state["last_refresh_obs"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
