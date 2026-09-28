from fastapi import APIRouter, HTTPException, Query, Header, Depends, Security
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.config import API_KEY
from app.services.tv_engine import tv_engine
from app.services.symbol_store import symbol_store
from app.services.search_engine import search_tradingview_symbols

api_router = APIRouter()

# Güvenlik Kontrol Fonksiyonu
async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None, alias="authorization"),
    api_key: Optional[str] = Query(None, alias="api_key")
):
    """
    API Anahtarı / Şifre Doğrulaması.
    Desteklenen yöntemler:
    1. Header: x-api-key: 8505050Cc.Mm
    2. Header: Authorization: Bearer 8505050Cc.Mm
    3. Query Param: ?api_key=8505050Cc.Mm
    """
    token_candidate = None
    if x_api_key:
        token_candidate = x_api_key.strip()
    elif authorization:
        parts = authorization.strip().split()
        token_candidate = parts[-1] if parts else None
    elif api_key:
        token_candidate = api_key.strip()

    if not token_candidate or token_candidate != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Yetkisiz Erişim: Geçersiz veya eksik API Anahtarı (API Key)."
        )
    return token_candidate

class UpdateNameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Kullanıcının belirleyeceği yeni görünen isim")

class AddSymbolRequest(BaseModel):
    tv_ticker: str = Field(..., description="TradingView Ticker formatı (örn. BIST:THYAO, NASDAQ:AAPL)")
    display_name: Optional[str] = Field(None, description="Özel görünen isim")
    original_name: Optional[str] = Field(None, description="Orijinal isim veya sembol")
    category: Optional[str] = Field("Stock", description="Kategori (Stock, Crypto, Forex, Commodity, Index)")
    description: Optional[str] = Field("", description="Açıklama")

# ----------------- GENEL FİYAT API'LERİ (ŞİFRELİ / KORUMALI) -----------------

@api_router.get("/api/prices", summary="Tüm hisse ve varlıkların güncel fiyatları (Şifreli)")
async def get_all_prices(_auth: str = Depends(verify_api_key)):
    """
    Her 10 saniyede bir güncellenen tüm hisselerin gerçek zamanlı fiyatları.
    Erişmek için 'x-api-key' başlığı veya '?api_key=' parametresi zorunludur.
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

@api_router.get("/api/prices/{query}", summary="Tek bir hisse/varlığın fiyatını sorgula (Şifreli)")
async def get_single_price(query: str, _auth: str = Depends(verify_api_key)):
    """
    ID, görünen isim veya TradingView sembolü ile tek bir hissenin anlık fiyatını döner.
    """
    price_info = tv_engine.get_price_by_id_or_name(query)
    if not price_info:
        raise HTTPException(status_code=404, detail=f"'{query}' için fiyat bulunamadı.")
    return {
        "success": True,
        "data": price_info
    }

# ----------------- ADMİN PANELİ YÖNETİM VE ARAMA API'LERİ (ŞİFRELİ) -----------------

@api_router.get("/api/search", summary="TradingView üzerinde canlı hisse/sembol ara (Şifreli)")
async def search_symbols(q: str = Query(..., min_length=1), _auth: str = Depends(verify_api_key)):
    results = await search_tradingview_symbols(q)
    return {
        "success": True,
        "query": q,
        "count": len(results),
        "results": results
    }

@api_router.post("/api/symbols", summary="Listeye yeni hisse/sembol ekle (Şifreli)")
async def add_symbol(payload: AddSymbolRequest, _auth: str = Depends(verify_api_key)):
    item = symbol_store.add_symbol(
        tv_ticker=payload.tv_ticker,
        display_name=payload.display_name,
        original_name=payload.original_name,
        category=payload.category or "Stock",
        description=payload.description or ""
    )
    await tv_engine.refresh_prices()
    return {
        "success": True,
        "message": f"'{item['display_name']}' ({item['tv_ticker']}) başarıyla listeye eklendi.",
        "symbol": item
    }

@api_router.put("/api/symbols/{symbol_id}/name", summary="Hisse ismini değiştir (Şifreli)")
async def update_symbol_name(symbol_id: str, payload: UpdateNameRequest, _auth: str = Depends(verify_api_key)):
    item = symbol_store.update_name(symbol_id, payload.name)
    if not item:
        raise HTTPException(status_code=404, detail="Sembol bulunamadı.")
    return {
        "success": True,
        "message": f"İsim başarıyla güncellendi: {item['display_name']}",
        "symbol": item
    }

@api_router.delete("/api/symbols/{symbol_id}", summary="Listeden hisse kaldır (Şifreli)")
async def remove_symbol(symbol_id: str, _auth: str = Depends(verify_api_key)):
    deleted = symbol_store.remove_symbol(symbol_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sembol bulunamadı.")
    return {
        "success": True,
        "message": "Sembol listeden kaldırıldı."
    }

@api_router.post("/api/refresh", summary="Fiyatları hemen yenile (Şifreli)")
async def manual_refresh(_auth: str = Depends(verify_api_key)):
    await tv_engine.refresh_prices()
    return {
        "success": True,
        "message": "Fiyatlar güncellendi.",
        "status": tv_engine.get_status_info()
    }

@api_router.post("/api/symbols/reset", summary="Varsayılan 171 hisse listesine sıfırla (Şifreli)")
async def reset_symbols(_auth: str = Depends(verify_api_key)):
    success = symbol_store.reset_to_defaults()
    if not success:
        raise HTTPException(status_code=500, detail="Varsayılan liste yüklenemedi.")
    await tv_engine.refresh_prices()
    return {
        "success": True,
        "message": "Liste videodaki orijinal 171 sembole sıfırlandı."
    }

@api_router.get("/api/status", summary="Sistem durumu (Şifreli)")
async def get_system_status(_auth: str = Depends(verify_api_key)):
    return {
        "success": True,
        "engine": tv_engine.get_status_info()
    }

# Render sağlık kontrolü (Açık kalmalıdır ki Render servisi ayakta tutabilsin)
@api_router.get("/health", summary="Render Health Check")
async def health_check():
    return {"status": "ok", "timestamp": tv_engine.get_status_info().get("last_updated")}
