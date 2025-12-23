"""
Appscrip Trade Opportunities API
Author: Vaishnavi Raghavan
Description: FastAPI service that analyzes Indian market sectors and returns Markdown trade reports.
"""


from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import requests
import os
import time
import logging
from typing import Dict, List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS


# ---------------------------------------------------------------------------
# basic app setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Appscrip Trade Opportunities API", version="1.0.0")

security = HTTPBearer()

# in‑memory rate tracking (per IP)
ip_rates: Dict[str, List[float]] = {}

# slowapi limiter configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------

class SectorRequest(BaseModel):
    sector: str = Field(..., min_length=2, max_length=50)


# ---------------------------------------------------------------------------
# root / health
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "Appscrip Trade Opportunities API READY",
        "endpoint": "/analyzesector?sector=pharmaceuticals",
    }


# ---------------------------------------------------------------------------
# simple guest login (token placeholder)
# ---------------------------------------------------------------------------

@app.post("/login")
async def login(request: Request, username: str, password: str):
    """
    Very simple guest login to demonstrate auth.
    In a real system this would be backed by proper user storage and JWT.
    """
    if username == "guest" and password == "appscrip2025":
        token = f"Bearer appscrip_guest_{int(time.time())}"
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="Invalid credentials")


# ---------------------------------------------------------------------------
# data collection: sector news from DuckDuckGo
# ---------------------------------------------------------------------------

async def fetch_sector_news(sector: str) -> str:
    """
    Fetch a short text summary of recent India‑focused news
    for the given sector using DuckDuckGo.
    """
    try:
        query = f"{sector} India stock market news opportunities 2025"

        with DDGS() as ddgs:
            results = ddgs.text(
                query,
                region="in-en",
                safesearch="moderate",
                timelimit="d",
                max_results=8,
            )

        lines: List[str] = []
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            url = r.get("href", r.get("url", ""))
            lines.append(f"- {title} ({url})\n  {body[:200]}...")

        if not lines:
            return f"No recent results found for {sector} in India."

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"DuckDuckGo fetch failed: {e}")
        return f"Could not fetch live market data for {sector} due to an error."


@app.get("/debug/news")
async def debug_news(sector: str = "technology"):
    """
    Debug endpoint to inspect the news text being passed into the model.
    """
    data = await fetch_sector_news(sector)
    return {"sector": sector, "market_data_sample": data[:1000]}


# ---------------------------------------------------------------------------
# main endpoint: analyze sector
# ---------------------------------------------------------------------------

@app.get("/analyzesector")
@limiter.limit("3/5minutes")
async def analyze_sector(
    sector: str,
    token: str = Depends(security),
    request: Request = None,
):
    """
    Analyze a sector and return a Markdown report with trade opportunities.
    Example: GET /analyzesector?sector=pharmaceuticals
    """

    # 1) validate input using pydantic model
    try:
        SectorRequest(sector=sector)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid sector name (2–50 characters).",
        )

    # 2) in‑memory rate limiting per IP (5‑minute window)
    client_ip = get_remote_address(request)
    now = time.time()
    ip_rates.setdefault(client_ip, []).append(now)
    ip_rates[client_ip] = [t for t in ip_rates[client_ip] if now - t < 300]

    if len(ip_rates[client_ip]) > 3:
        raise HTTPException(status_code=429, detail="Rate limit: 3 requests / 5 min per IP")

    logger.info(f"Analyzing sector={sector} from ip={client_ip}")

    # 3) fetch sector news text
    market_data = await fetch_sector_news(sector)

    # 4) call Gemini HTTP API – fall back to static report if not available
    try:
        gemini_url = (
            "https://generativelanguage.googleapis.com/v1/models/"
            "gemini-1.5-flash:generateContent"
            f"?key={os.getenv('GEMINI_API_KEY')}"
        )

        prompt_data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"""Analyze this {sector} India market data for trade opportunities.

MARKET DATA:
{market_data}

Generate a MARKDOWN report with these sections:
## Current Trends
## Buy Opportunities (specific stocks)
## Sell Risks
## Trade Summary (actionable today)

Keep it focused on Indian equities."""
                        }
                    ]
                }
            ]
        }

        response = requests.post(gemini_url, json=prompt_data, timeout=30)

        logger.info(f"Gemini status: {response.status_code}")
        logger.info(f"Gemini raw response: {response.text[:500]}")

        if response.status_code == 200:
            data = response.json()
            report = data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # model/key not available → use fallback summary
            report = (
                f"# {sector.title()} Analysis Fallback\n\n"
                f"**Trends:** Market data unavailable\n"
                f"**Opportunities:** Check Nifty {sector} index\n"
                f"**Generated:** {time.strftime('%Y-%m-%d %H:%M IST')}"
            )

    except Exception as e:
        # network / timeout / parsing failure
        logger.error(f"Gemini failed: {e}")
        report = (
            f"# {sector.title()} Service Temporary Unavailable\n\n"
            f"**Status:** AI analysis temporarily down.\n"
            f"**Manual check:** Search '{sector} India stock news'.\n"
            f"**Time:** {time.strftime('%Y-%m-%d %H:%M IST')}"
        )

    return {
        "sector": sector.title(),
        "report": report,
        "timestamp": time.strftime("%Y-%m-%d %H:%M IST"),
        "status": "analysis_complete",
        "requests_used": len(ip_rates.get(client_ip, [])),
        "limit_remaining": 3 - len(ip_rates.get(client_ip, [])),
    }


# ---------------------------------------------------------------------------
# local run helper
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
