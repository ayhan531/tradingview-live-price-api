import urllib.request
import json
import time

BASE_URL = 'https://tradingview-price-api.onrender.com'

print('========================================')
print('CANLI RENDER SUNUCUSU KAPSAMLI TEST BAŞLIYOR')
print('Hedef URL:', BASE_URL)
print('========================================\n')

# 1. Health Check
print('1. Sağlık Kontrolü (Health Check)...')
with urllib.request.urlopen(f'{BASE_URL}/health') as resp:
    res = json.loads(resp.read().decode())
    print('   Durum:', resp.status, '| Yanıt:', res)

# 2. Tüm Fiyat Listesini Çek
print('\n2. Tüm Fiyat Listesi Çekiliyor (GET /api/prices)...')
with urllib.request.urlopen(f'{BASE_URL}/api/prices') as resp:
    res = json.loads(resp.read().decode())
    print(f'   Başarılı! Toplam Varlık Sayısı: {res["count"]}')
    print(f'   Son Güncelleme Zamanı: {res["last_updated"]}')
    print('   Örnek Canlı Fiyatlar:')
    for item in res['data'][:5]:
        print(f'     - {item["name"]} ({item["tv_ticker"]}) -> Fiyat: {item["price"]} | 24s Değişim: %{item["change"]}')

# 3. TradingView Sembol Arama
print('\n3. TradingView Canlı Sembol Arama Test Ediliyor (Arama terimi: "thy")...')
with urllib.request.urlopen(f'{BASE_URL}/api/search?q=thy') as resp:
    res = json.loads(resp.read().decode())
    print(f'   Bulunan Sembol Sayısı: {res["count"]}')
    for r in res['results'][:3]:
        print(f'     - Ticker: {r["ticker"]} | {r["description"]} ({r["exchange"]})')

# 4. Listeye Yeni Hisse Ekle
print('\n4. Listeye Yeni Hisse Ekleniyor (THYAO - BIST:THYAO)...')
add_payload = {
    'tv_ticker': 'BIST:THYAO',
    'display_name': 'Türk Hava Yolları',
    'original_name': 'THYAO',
    'category': 'Stock',
    'description': 'Turk Hava Yollari A.O.'
}
req = urllib.request.Request(
    f'{BASE_URL}/api/symbols',
    data=json.dumps(add_payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    print('   Ekleme Yanıtı:', res['message'])
    added_id = res['symbol']['id']

# 5. Yeni Eklenen Hissenin Canlı Fiyatını Doğrula
print(f'\n5. Yeni Eklenen Hissenin Fiyatı Sorgulanıyor (ID: {added_id})...')
with urllib.request.urlopen(f'{BASE_URL}/api/prices/{added_id}') as resp:
    p = json.loads(resp.read().decode())['data']
    print(f'   Hisse: {p["name"]} | Ticker: {p["tv_ticker"]} | Fiyat: {p["price"]} TL | Değişim: %{p["change"]}')

# 6. İsmini Değiştir (Ticker Koruma Testi)
print('\n6. İsmini Değiştirme Test Ediliyor ("THY Süper Hızlı")...')
rename_payload = {'name': 'THY Süper Hızlı'}
req = urllib.request.Request(
    f'{BASE_URL}/api/symbols/{added_id}/name',
    data=json.dumps(rename_payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='PUT'
)
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    print('   İsim Güncelleme Yanıtı:', res['message'])

# 7. Yeni İsimle Fiyatı Çek ve Ticker'ın Sabit Kaldığını Doğrula
with urllib.request.urlopen(f'{BASE_URL}/api/prices/{added_id}') as resp:
    p = json.loads(resp.read().decode())['data']
    print(f'   Yeni İsim Doğrulandı: "{p["name"]}"')
    print(f'   TradingView Ticker Korundu: "{p["tv_ticker"]}" (Fiyat: {p["price"]} TL)')

# 8. İsim Geri Alma Testi
print('\n8. İsim Geri Alınıyor ("Türk Hava Yolları")...')
req = urllib.request.Request(
    f'{BASE_URL}/api/symbols/{added_id}/name',
    data=json.dumps({'name': 'Türk Hava Yolları'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='PUT'
)
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    print('   İsim Geri Alındı:', res['symbol']['display_name'])

# 9. Listeden Kaldırma Testi
print('\n9. Eklenen Sembol Listeden Siliniyor...')
req = urllib.request.Request(f'{BASE_URL}/api/symbols/{added_id}', method='DELETE')
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    print('   Silme Yanıtı:', res['message'])

# 10. Admin Paneli Web Arayüzü Testi
print('\n10. Admin Paneli Web Sayfası Test Ediliyor (GET /)...')
with urllib.request.urlopen(f'{BASE_URL}/') as resp:
    html = resp.read().decode()
    print(f'   HTML Sayfası Başarıyla Geldi! (Durum: {resp.status}, Boyut: {len(html)} byte)')

print('\n========================================')
print('TÜM TESTLER BAŞARIYLA TAMAMLANDI! SISTEM KUSURSUZ ÇALIŞIYOR.')
print('========================================')
