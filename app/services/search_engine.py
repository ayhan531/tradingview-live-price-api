import httpx
import logging
import urllib.parse
from typing import List, Dict, Any

logger = logging.getLogger("search_engine")

SEARCH_URL = "https://symbol-search.tradingview.com/symbol_search/v3/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
    "Accept": "application/json"
}

async def search_tradingview_symbols(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    TradingView'in sembol arama motoru üzerinden arama yapar.
    Örnek: "thy" -> BIST:THYAO (Türk Hava Yolları)
    """
    query = (query or "").strip()
    if not query:
        return []

    params = {
        "text": query,
        "hl": "1",
        "lang": "en",
        "domain": "production"
    }

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=8.0) as client:
            resp = await client.get(SEARCH_URL, params=params)
            if resp.status_code != 200:
                logger.warning(f"TradingView search API status {resp.status_code}")
                return []
            
            data = resp.json()
            symbols = data.get("symbols", [])
            results = []

            for item in symbols[:limit]:
                raw_sym = item.get("symbol", "").replace("<em>", "").replace("</em>", "")
                exchange = item.get("exchange", "")
                prefix = item.get("prefix", exchange)
                desc = item.get("description", "").replace("<em>", "").replace("</em>", "")
                sym_type = item.get("type", "stock")

                # Standart ticker formatı: BORSA:SEMBOL (örn. BIST:THYAO, NASDAQ:AAPL)
                tv_ticker = f"{prefix}:{raw_sym}" if prefix else raw_sym

                results.append({
                    "ticker": tv_ticker,
                    "symbol": raw_sym,
                    "exchange": exchange,
                    "description": desc or raw_sym,
                    "type": sym_type,
                    "currency": item.get("currency_code", "USD"),
                    "country": item.get("country", "")
                })

            return results
    except Exception as e:
        logger.error(f"TradingView arama hatası ({query}): {e}")
        return []
