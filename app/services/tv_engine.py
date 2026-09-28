import asyncio
import httpx
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import UPDATE_INTERVAL_SECONDS
from app.services.symbol_store import symbol_store

logger = logging.getLogger("tv_engine")

SCANNER_URL = "https://scanner.tradingview.com/global/scan"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
    "Accept": "application/json"
}

COLUMNS = ["close", "change", "change_abs", "volume", "high", "low", "open"]

class TradingViewEngine:
    def __init__(self):
        # symbol_id -> fiyat verisi
        self._price_cache: Dict[str, Dict[str, Any]] = {}
        # tv_ticker -> son çekilen ham veri
        self._raw_cache: Dict[str, Dict[str, Any]] = {}
        self._is_running = False
        self._last_update: Optional[datetime] = None
        self._update_task: Optional[asyncio.Task] = None
        self._consecutive_errors = 0

    async def start(self):
        """Arka plan fiyat güncelleme döngüsünü başlatır."""
        if self._is_running:
            return
        self._is_running = True
        logger.info(f"TradingView Fiyat Motoru başlatılıyor (Periyot: {UPDATE_INTERVAL_SECONDS} sn)...")
        # İlk güncellemeyi hemen yap
        await self.refresh_prices()
        # Periyodik arka plan görevini başlat
        self._update_task = asyncio.create_task(self._update_loop())

    async def stop(self):
        self._is_running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("TradingView Fiyat Motoru durduruldu.")

    async def _update_loop(self):
        while self._is_running:
            try:
                await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
                await self.refresh_prices()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Fiyat güncelleme döngü hatası: {e}")
                await asyncio.sleep(5)

    async def refresh_prices(self):
        """
        TradingView scanner API'sinden tüm aktif sembollerin fiyatlarını çeker.
        Borsa kapandığında son fiyatlar bozulmadan korunur.
        """
        symbols = symbol_store.get_all()
        if not symbols:
            return

        # Sorgulanacak tekil ticker'lar
        tickers_to_query = set()
        for s in symbols:
            t = s.get("tv_ticker")
            if t and not t.startswith("CALC:"):
                tickers_to_query.add(t)

        # CALC:XAUEUR için gerekenler
        tickers_to_query.add("TVC:GOLD")
        tickers_to_query.add("FX:EURUSD")

        tickers_list = list(tickers_to_query)
        # TradingView scanner tek seferde 200+ sembolü rahatça işler, gerekiyorsa chunk'lara bölelim
        chunk_size = 150
        chunks = [tickers_list[i:i + chunk_size] for i in range(0, len(tickers_list), chunk_size)]

        now_str = datetime.now().strftime("%H:%M:%S")

        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=12.0) as client:
                for chunk in chunks:
                    payload = {
                        "symbols": {"tickers": chunk, "query": {"types": []}},
                        "columns": COLUMNS
                    }
                    resp = await client.post(SCANNER_URL, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        rows = data.get("data", [])
                        for item in rows:
                            ticker = item.get("s")
                            vals = item.get("d", [])
                            if vals and len(vals) >= 3 and vals[0] is not None:
                                close_price = round(float(vals[0]), 6 if vals[0] < 1 else 2)
                                change_pct = round(float(vals[1]), 2) if vals[1] is not None else 0.0
                                change_abs = round(float(vals[2]), 4 if abs(float(vals[2])) < 1 else 2) if vals[2] is not None else 0.0
                                vol = vals[3] if len(vals) > 3 and vals[3] is not None else 0
                                high_val = round(float(vals[4]), 4 if float(vals[4]) < 1 else 2) if len(vals) > 4 and vals[4] is not None else close_price
                                low_val = round(float(vals[5]), 4 if float(vals[5]) < 1 else 2) if len(vals) > 5 and vals[5] is not None else close_price

                                self._raw_cache[ticker] = {
                                    "price": close_price,
                                    "change": change_pct,
                                    "change_abs": change_abs,
                                    "volume": vol,
                                    "high": high_val,
                                    "low": low_val,
                                    "updated_at": now_str,
                                    "raw_ticker": ticker
                                }
            self._consecutive_errors = 0
            self._last_update = datetime.now()

            # Türetilmiş (hesaplanan) semboller: örn. XAUEUR (Altın / Euro)
            if "TVC:GOLD" in self._raw_cache and "FX:EURUSD" in self._raw_cache:
                gold_p = self._raw_cache["TVC:GOLD"]["price"]
                eur_p = self._raw_cache["FX:EURUSD"]["price"]
                if eur_p > 0:
                    xau_eur_price = round(gold_p / eur_p, 2)
                    self._raw_cache["CALC:XAUEUR"] = {
                        "price": xau_eur_price,
                        "change": self._raw_cache["TVC:GOLD"]["change"],
                        "change_abs": round(self._raw_cache["TVC:GOLD"]["change_abs"] / eur_p, 2),
                        "volume": 0,
                        "high": round(self._raw_cache["TVC:GOLD"]["high"] / eur_p, 2),
                        "low": round(self._raw_cache["TVC:GOLD"]["low"] / eur_p, 2),
                        "updated_at": now_str,
                        "raw_ticker": "CALC:XAUEUR"
                    }

            # Şimdi kullanıcı sembolleriyle eşleştirip ana price_cache'e aktar
            for s in symbols:
                sid = s["id"]
                ticker = s.get("tv_ticker")
                raw_info = self._raw_cache.get(ticker)

                # Eğer yeni veri geldiyse güncelle, gelmediyse/borsa kapalıysa MEVCUT SON FİYATI KORU!
                prev_info = self._price_cache.get(sid, {})
                if raw_info:
                    self._price_cache[sid] = {
                        "id": sid,
                        "name": s.get("display_name", s.get("original_name")),
                        "original_name": s.get("original_name"),
                        "tv_ticker": ticker,
                        "category": s.get("category", "General"),
                        "description": s.get("description", ""),
                        "price": raw_info["price"],
                        "change": raw_info["change"],
                        "change_abs": raw_info["change_abs"],
                        "high": raw_info["high"],
                        "low": raw_info["low"],
                        "volume": raw_info["volume"],
                        "updated_at": raw_info["updated_at"],
                        "status": "active"
                    }
                elif sid in self._price_cache:
                    # Borsa kapalı veya sembol verisi aynı: Eski fiyatı aynen tut, sadece isim değişikliği varsa yansıt
                    self._price_cache[sid]["name"] = s.get("display_name", s.get("original_name"))
                    self._price_cache[sid]["status"] = "market_closed_retained"
                else:
                    # Henüz fiyat çekilemediyse beklemede göster
                    self._price_cache[sid] = {
                        "id": sid,
                        "name": s.get("display_name", s.get("original_name")),
                        "original_name": s.get("original_name"),
                        "tv_ticker": ticker,
                        "category": s.get("category", "General"),
                        "description": s.get("description", ""),
                        "price": 0.0,
                        "change": 0.0,
                        "change_abs": 0.0,
                        "high": 0.0,
                        "low": 0.0,
                        "volume": 0,
                        "updated_at": "Bekleniyor",
                        "status": "pending"
                    }

            logger.info(f"Fiyatlar güncellendi ({len(self._price_cache)} sembol, {now_str})")
        except Exception as e:
            self._consecutive_errors += 1
            logger.error(f"Fiyat çekilirken hata oluştu: {e}. Mevcut fiyatlar korundu.")

    def get_all_prices(self) -> List[Dict[str, Any]]:
        """Tüm sembollerin anlık veya son kapanış fiyatlarını döner."""
        symbols = symbol_store.get_all()
        result = []
        for s in symbols:
            sid = s["id"]
            if sid in self._price_cache:
                # İsim değişikliği yapıldıysa en güncel display_name'i ver
                item = dict(self._price_cache[sid])
                item["name"] = s.get("display_name", s.get("original_name"))
                result.append(item)
            else:
                result.append({
                    "id": sid,
                    "name": s.get("display_name", s.get("original_name")),
                    "original_name": s.get("original_name"),
                    "tv_ticker": s.get("tv_ticker"),
                    "category": s.get("category", "General"),
                    "description": s.get("description", ""),
                    "price": 0.0,
                    "change": 0.0,
                    "change_abs": 0.0,
                    "high": 0.0,
                    "low": 0.0,
                    "volume": 0,
                    "updated_at": "Bekleniyor",
                    "status": "pending"
                })
        return result

    def get_price_by_id_or_name(self, query: str) -> Optional[Dict[str, Any]]:
        """ID, isim veya sembol ile tekil fiyat arar."""
        q = query.strip().lower()
        all_prices = self.get_all_prices()
        for p in all_prices:
            if (p["id"].lower() == q or 
                p["name"].lower() == q or 
                p.get("original_name", "").lower() == q or 
                p.get("tv_ticker", "").lower() == q):
                return p
        return None

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "is_running": self._is_running,
            "symbols_count": len(symbol_store.get_all()),
            "cached_prices_count": len(self._price_cache),
            "last_updated": self._last_update.isoformat() if self._last_update else None,
            "interval_seconds": UPDATE_INTERVAL_SECONDS
        }

tv_engine = TradingViewEngine()
