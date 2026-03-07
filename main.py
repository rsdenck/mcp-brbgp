from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
from loguru import logger

from db.api import (
    get_statistics,
    search_asns,
    get_asn_details,
    get_top_operators,
    get_country_distribution,
    get_traffic_data,
    get_global_operators,
)

app = FastAPI(title="Bradar API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent / "frontend-nuxt" / ".output" / "public"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    return {"message": "Bradar API v2.0 - BGP Intelligence"}


@app.get("/api/stats")
async def api_stats():
    return get_statistics()


@app.get("/api/search")
async def api_search(q: str, limit: int = 20):
    return search_asns(q, limit)


@app.get("/api/asn/{asn}")
async def api_asn(asn: int):
    return get_asn_details(asn)


@app.get("/api/operators")
async def api_operators(limit: int = 50):
    return get_top_operators(limit)


@app.get("/api/countries")
async def api_countries():
    return get_country_distribution()


@app.get("/api/traffic")
async def api_traffic():
    return get_traffic_data()


@app.get("/api/global/operators")
async def api_global_ops():
    return get_global_operators()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
