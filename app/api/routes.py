from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.services.tv_engine import tv_engine
from app.services.symbol_store import symbol_store
from app.services.search_engine import search_tradingview_symbols

api_router = APIRouter()

class UpdateNameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Kullanıcının belirleyeceği yeni görünen isim")

class AddSymbolRequest(BaseModel):
    tv_ticker: str = Field(..., description="TradingView Ticker formatı (örn. BIST:THYAO, NASDAQ:AAPL)")
    display_name: Optional[str] = Field(None, description="Özel görünen isim")
    original_name: Optional[str] = Field(None, description="Orijinal isim veya sembol")
    category: Optional[str] = Field("Stock", description="Kategori (Stock, Crypto, Forex, Commodity, Index)")
    description: Optional[str] = Field("", description="Açıklama")

# ----------------- GENEL FİYAT API'LERİ (RENDER ÜZERİNDEN YAYINLANACAK) -----------------

@api_router.get("/api/prices", summary="Tüm hisse ve varlıkların güncel fiyatları")
async def get_all_prices():
    """
    Her 10 saniyede bir güncellenen tüm hisselerin gerçek zamanlı fiyatları.
    Kullanıcının admin panelinden değiştirdiği özel isimlerle yayınlanır.
    Borsa kapandığında en son kapanış fiyatları korunur.
    """
    prices = tv_engine.get_all_prices()
    status = tv_engine.get_status_info()
    return {
        "success": True,
        "count": len(prices),
        "last_updated": status.get("last_updated"),
        "interval_seconds": status.get("interval_seconds"),
        "data": prices
    }

@api_router.get("/api/prices/{query}", summary="Tek bir hisse/varlığın fiyatını sorgula")
async def get_single_price(query: str):
    """
    ID, görünen isim veya TradingView sembolü ile tek bir hissenin anlık fiyatını döner.
    Örnek: /api/prices/thy veya /api/prices/bmw veya /api/prices/golds
    """
    price_info = tv_engine.get_price_by_id_or_name(query)
    if not price_info:
        raise HTTPException(status_code=404, detail=f"'{query}' için fiyat bulunamadı.")
    return {
        "success": True,
        "data": price_info
    }

# ----------------- ADMİN PANELİ YÖNETİM VE ARAMA API'LERİ -----------------

@api_router.get("/api/search", summary="TradingView üzerinde canlı hisse/sembol ara")
async def search_symbols(q: str = Query(..., min_length=1, description="Arama terimi örn: thy, btc, thyao")):
    """
    TradingView arama API'si üzerinden sembol arar.
    Kullanıcı admin panelinden 'thy' yazdığında TradingView'deki gerçek ticker'ı döner.
    """
    results = await search_tradingview_symbols(q)
    return {
        "success": True,
        "query": q,
        "count": len(results),
        "results": results
    }

@api_router.post("/api/symbols", summary="Listeye yeni hisse/sembol ekle")
async def add_symbol(payload: AddSymbolRequest):
    """
    TradingView'den bulunan yeni hisseyi listeye ekler ve anında fiyat çekmeye başlar.
    """
    item = symbol_store.add_symbol(
        tv_ticker=payload.tv_ticker,
        display_name=payload.display_name,
        original_name=payload.original_name,
        category=payload.category or "Stock",
        description=payload.description or ""
    )
    # Hemen yeni sembolün fiyatını çek
    await tv_engine.refresh_prices()
    return {
        "success": True,
        "message": f"'{item['display_name']}' ({item['tv_ticker']}) başarıyla listeye eklendi.",
        "symbol": item
    }

@api_router.put("/api/symbols/{symbol_id}/name", summary="Hisse ismini değiştir")
async def update_symbol_name(symbol_id: str, payload: UpdateNameRequest):
    """
    Hissenin admin panelinde ve API'de görünen adını (display_name) değiştirir.
    ÖNEMLİ: TradingView ticker'ı ASLA DEĞİŞMEZ, fiyat çekilmeye kesintisiz devam edilir!
    """
    item = symbol_store.update_name(symbol_id, payload.name)
    if not item:
        raise HTTPException(status_code=404, detail="Sembol bulunamadı.")
    return {
        "success": True,
        "message": f"İsim başarıyla güncellendi: {item['display_name']}",
        "symbol": item
    }

@api_router.delete("/api/symbols/{symbol_id}", summary="Listeden hisse kaldır")
async def remove_symbol(symbol_id: str):
    """Listeden hisseyi kaldırır."""
    deleted = symbol_store.remove_symbol(symbol_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sembol bulunamadı.")
    return {
        "success": True,
        "message": "Sembol listeden kaldırıldı."
    }

@api_router.post("/api/refresh", summary="Fiyatları hemen yenile")
async def manual_refresh():
    """Fiyat çekme işlemini manuel olarak anında tetikler."""
    await tv_engine.refresh_prices()
    return {
        "success": True,
        "message": "Fiyatlar güncellendi.",
        "status": tv_engine.get_status_info()
    }

@api_router.post("/api/symbols/reset", summary="Varsayılan 171 hisse listesine sıfırla")
async def reset_symbols():
    """Videodan çıkarılan orijinal 171 hisselik listeye geri döndürür."""
    success = symbol_store.reset_to_defaults()
    if not success:
        raise HTTPException(status_code=500, detail="Varsayılan liste yüklenemedi.")
    await tv_engine.refresh_prices()
    return {
        "success": True,
        "message": "Liste videodaki orijinal 171 sembole sıfırlandı."
    }

@api_router.get("/api/status", summary="Sistem durumu")
async def get_system_status():
    return {
        "success": True,
        "engine": tv_engine.get_status_info()
    }

@api_router.get("/health", summary="Render Health Check")
async def health_check():
    return {"status": "ok", "timestamp": tv_engine.get_status_info().get("last_updated")}
