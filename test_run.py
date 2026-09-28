import asyncio
from app.services.tv_engine import tv_engine
from app.services.symbol_store import symbol_store
from app.services.search_engine import search_tradingview_symbols

async def main():
    print("1. Sembol Deposu Test Ediliyor...")
    symbols = symbol_store.get_all()
    print(f"   Yüklü Sembol Sayısı: {len(symbols)}")

    print("\n2. TradingView Fiyat Motoru Test Ediliyor...")
    await tv_engine.refresh_prices()
    prices = tv_engine.get_all_prices()
    non_zero = [p for p in prices if p["price"] > 0]
    print(f"   Fiyatı Çekilen Sembol: {len(non_zero)} / {len(prices)}")

    print("\n   Örnek Çekilen Fiyatlar:")
    for p in prices[:6]:
        print(f"   - {p['name']} ({p['tv_ticker']}): {p['price']} (Değişim: %{p['change']})")

    print("\n3. TradingView Arama Test Ediliyor ('thy')...")
    results = await search_tradingview_symbols("thy")
    print(f"   Arama Sonucu Sayısı: {len(results)}")
    for r in results[:2]:
        print(f"   - {r['ticker']} | {r['description']} ({r['exchange']})")

    print("\n4. İsim Değiştirme Test Ediliyor (TradingView bağlantısı bozulmamalı)...")
    original = symbol_store.get_by_id("bmw")
    print(f"   Orijinal: {original['display_name']} -> Ticker: {original['tv_ticker']}")
    updated = symbol_store.update_name("bmw", "Alman Devi BMW")
    print(f"   Güncellendi: {updated['display_name']} -> Ticker: {updated['tv_ticker']}")
    
    # Geri al
    symbol_store.update_name("bmw", "BMW")
    print("   Test başarıyla tamamlandı!")

if __name__ == "__main__":
    asyncio.run(main())
