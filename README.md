# Appscrip Trade Opportunities API

This project is a small FastAPI service that takes an Indian market sector (for example, `pharmaceuticals` or `technology`) and returns a Markdown report describing trade opportunities for that sector. It was built as an assignment for the Appscrip AI Engineer role. [file:52]

## 1. Overview

- Exposes one main endpoint: `GET /analyzesector?sector=<name>`.
- Fetches recent sector-related news and information from the web using the `duckduckgo-search` library. [web:71]
- Sends the collected text to the Google Generative Language API (Gemini) over HTTP to generate an analysis report when the model is available. [web:67]
- Returns a structured Markdown report in the `report` field of the JSON response so it can be saved directly as a `.md` file. [file:52]
- Includes simple authentication, input validation, and rate limiting, and uses only in‑memory storage as specified in the assignment. [file:52]

## 2. Tech Stack

- Python 3.x
- FastAPI + Uvicorn
- duckduckgo-search (web/search data) [web:71]
- Google Generative Language API (Gemini HTTP endpoint) [web:67]
- slowapi (rate limiting)
- pydantic (request validation)
- python-dotenv (environment configuration)

## 3. Project Structure

- `main.py`  
  - FastAPI app definition.  
  - Endpoints: `/`, `/login`, `/debug/news`, `/analyzesector`.  
  - Functions:
    - `fetch_sector_news` – uses DuckDuckGo to retrieve recent India‑focused news for a sector. [web:71]
    - `analyze_sector` – main pipeline combining validation, rate limiting, data collection, and AI analysis. [file:52]
- `requirements.txt` – pinned dependencies used to recreate the environment.
- `.env` – local environment variables (`GEMINI_API_KEY`, not checked into version control).

## 4. Setup Instructions
git clone https://github.com/vaishragh03/appscrip-trade-api.git
cd appscrip-trade-api

  2. **Create and activate virtual environment**
  
  python -m venv venv
  venv\Scripts\activate # Windows
  
  3. **Install dependencies**
  pip install -r requirements.txt
  
  
  4. **Configure environment**
  
  Create a `.env` file in the project root with:
  GEMINI_API_KEY=your_gemini_api_key_here
  
  The key can be generated from Google AI Studio for the Generative Language API. [web:67]

## 5. Running the API

Start the development server:

uvicorn main:app --reload

Default URLs:

- API docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Root/health: `GET http://127.0.0.1:8000/`

## 6. Using the Endpoints

  ### 6.1 Get a token (`/login`)
  
  The service uses a very simple guest login to demonstrate authentication.
  POST /login?username=guest&password=appscrip2025
  
  Example response:
  
  {
  "access_token": "Bearer appscrip_guest_173503xxxx",
  "token_type": "bearer"
  }
  
  Use this `access_token` as the `Authorization` header for protected endpoints:
  
  Authorization: Bearer appscrip_guest_173503xxxx
  
  ### 6.2 Inspect sector news (`/debug/news`)
  
  This helper endpoint shows the text snippet collected from DuckDuckGo for a sector.
  
  GET /debug/news?sector=technology
  {
  "sector": "technology",
  "market_data_sample": "- These are the Top 10 Emerging Technologies of 2025 (https://www.weforum.org/...) ..."
  }
  
  
  This is the text that is passed to the Gemini model for analysis. [attached_file:1][web:71]
  
  ### 6.3 Analyze sector (`/analyzesector`)
  
  Main endpoint described in the assignment. [file:52]
  
  GET /analyzesector?sector=pharmaceuticals
  Authorization: Bearer appscrip_guest_173503xxxx
  
  Example response (structure):
  
  {
  "sector": "Pharmaceuticals",
  "report": "## Current Trends\n...\n## Buy Opportunities\n...\n## Sell Risks\n...\n## Trade Summary\n...",
  "timestamp": "2025-12-23 12:30 IST",
  "status": "analysis_complete",
  "requests_used": 1,
  "limit_remaining": 2
  }
  
  - `report` is a Markdown string that can be saved as a `.md` file.
  - `requests_used` and `limit_remaining` reflect in‑memory rate tracking per IP (3 requests / 5 minutes).

## 7. Implementation Notes

- **Validation**: `SectorRequest` (Pydantic) enforces basic rules on the `sector` string before analysis. [file:91]
- **Rate limiting**: implemented with slowapi plus a simple timestamp list per IP to avoid abuse while testing. [file:91]
- **Data collection**: DuckDuckGo search is used instead of a paid market data API to keep the service simple and dependency‑light. [web:71]
- **AI integration**: the service calls the Gemini HTTP API with a prompt that includes the news text and asks for a structured Markdown report. When the configured model is not available for the current key/API version (404), the code logs the error and returns a deterministic fallback Markdown report instead of failing with a server error, which demonstrates robust error handling as requested in the assignment. [file:52][web:67]

## 8. Possible Extensions

If this were extended beyond the assignment:

- Replace placeholder auth with real JWT and a user table.
- Persist requests and reports in a database for history and auditing.
- Swap DuckDuckGo with a financial data API for more structured market metrics.
- Add more endpoints (e.g., compare two sectors, cache recent reports).




1. **Clone the repository**

