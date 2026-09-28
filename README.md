# 🚀 TradingView Canlı Fiyat API & Yönetim Paneli

Bu proje, videodaki **171 adet hisse, kripto, emtia, forex ve endeks** varlığının TradingView üzerinden her 10 saniyede bir canlı fiyatlarını çeken, isimlerini TradingView ticker'ını bozmadan özelleştirmenize olanak tanıyan, TradingView üzerinden canlı arama yaparak yeni varlıklar ekleyebileceğiniz ve tüm bu verileri **Render.com** üzerinde bir API olarak yayınlayabileceğiniz eksiksiz bir sistemdir.

---

## 🌟 Öne Çıkan Özellikler

1. **Videodaki 171 Varlık Eksiksiz Tanımlandı:**
   - Altın (`GOLDs`), Gümüş (`SILVER.s`), Brent (`UKOILs`), Bitcoin (`BTCUSDs`), Nasdaq (`NASDAQs`), DAX (`DAXs`), BMW, Adidas, Apple, Tesla vb. 171 varlığın tamamı mevcuttur.
2. **TradingView Fiyat Motoru (Her 10 Saniyede Bir):**
   - TradingView Scanner API'si kullanılarak gerçek zamanlı fiyatlar çekilir.
3. **Borsa Kapanış Koruması (En Son Fiyatı Koruma):**
   - Borsa kapandığında veya hafta sonu piyasalar tatil olduğunda TradingView'deki en son kapanış fiyatı hafızada korunur, asla sıfırlanmaz veya silinmez.
4. **Admin Panelinden İsim Değiştirme (Ticker Koruma Garantisi):**
   - Panel üzerinden istediğiniz hissenin görünen adını (örneğin `BMW` -> `Benim BMW'm` veya `THYAO` -> `Türk Hava Yolları`) değiştirebilirsiniz.
   - **Önemli Güvence:** Görünen isim değiştiğinde TradingView sembolü (`tv_ticker`) kesinlikle değişmez. Fiyatlar arka planda TradingView üzerinden kesintisiz çekilmeye devam eder!
5. **TradingView Canlı Arama & Listeye Ekleme:**
   - Paneldeki arama kutusuna `thy`, `eregl`, `btc`, `tesla` vb. yazıp arattığınızda arka planda TradingView API'si sorgulanır.
   - Çıkan sonuçlar tek tıkla listeye eklenir ve anında fiyatı çekilmeye başlar.
6. **Render.com Yayınına Tam Hazır:**
   - `render.yaml`, `Procfile`, `requirements.txt` ve `Dockerfile` hazırlandı.

## 🔐 Güvenlik & API Anahtarı (Şifre Koruması)

Tüm API uç noktaları yetkisiz erişime karşı şifrelenmiştir. API isteklerinde şu üç yöntemden birini kullanmanız gerekmektedir:

- **API Anahtarı / Şifreniz:** `8505050Cc.Mm`

### Nasıl Gönderilir?
1. **HTTP Header (Önerilen):**
   ```http
   x-api-key: 8505050Cc.Mm
   ```
2. **URL Query Parametresi:**
   ```
   https://tradingview-price-api.onrender.com/api/prices?api_key=8505050Cc.Mm
   ```
3. **Bearer Token:**
   ```http
   Authorization: Bearer 8505050Cc.Mm
   ```
*(Geçersiz veya eksik şifre durumunda API `401 Unauthorized` yanıtı döner).*

---

## 🛠️ Yerel Çalıştırma (Localhost)

Projeyi bilgisayarınızda çalıştırmak için:

```bash
# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Sunucuyu başlatın
python main.py
# veya
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- **Admin Paneli:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Canlı Fiyatlar API:** [http://127.0.0.1:8000/api/prices](http://127.0.0.1:8000/api/prices)
- **Swagger API Dokümantasyonu:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ☁️ Render.com Üzerine Deploy Etme Rehberi

Proje Render üzerinde sıfır konfigürasyonla çalışacak şekilde ayarlanmıştır:

1. **GitHub Deposu Oluşturun:**
   - Proje klasörünü bir GitHub deposuna yükleyin (`git init`, `git add .`, `git commit -m "Initial commit"`, `git push`).
2. **Render.com'a Giriş Yapın:**
   - [Render.com](https://render.com) paneline gidin.
   - **New +** -> **Web Service** seçeneğine tıklayın.
   - GitHub deponuzu bağlayın.
3. **Ayarlar (Otomatik Algılanır):**
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Free`
4. **Deploy:**
   - **Create Web Service** butonuna basın. Birkaç dakika içinde yayına girer ve size `https://tradingview-fiyat-api.onrender.com` gibi ücretsiz bir HTTPS adresi verir!

---

## 📡 API Endpoint Dokümantasyonu

### 1. Tüm Fiyatları Çekme (API Yayını)
- **Endpoint:** `GET /api/prices`
- **Açıklama:** Kullanıcının belirlediği yeni isimlerle birlikte tüm varlıkların 10 saniyede bir güncellenen fiyatları.

```json
{
  "success": true,
  "count": 171,
  "last_updated": "2026-09-29T00:23:00",
  "interval_seconds": 10,
  "data": [
    {
      "id": "golds",
      "name": "GOLDs",
      "original_name": "GOLDs",
      "tv_ticker": "TVC:GOLD",
      "category": "Commodity",
      "price": 4115.13,
      "change": -3.95,
      "change_abs": -169.3,
      "high": 4275.32,
      "low": 4110.87,
      "volume": 868960,
      "updated_at": "00:23:00",
      "status": "active"
    }
  ]
}
```

### 2. Tek Bir Varlık Sorgulama
- **Endpoint:** `GET /api/prices/{query}`
- **Örnekler:**
  - `GET /api/prices/bmw`
  - `GET /api/prices/thy`
  - `GET /api/prices/golds`

### 3. TradingView Sembol Arama
- **Endpoint:** `GET /api/search?q=thy`

### 4. Yeni Sembol Ekleme
- **Endpoint:** `POST /api/symbols`
- **Body:**
```json
{
  "tv_ticker": "BIST:THYAO",
  "display_name": "Türk Hava Yolları",
  "category": "Stock"
}
```

### 5. Görünen İsmi Değiştirme
- **Endpoint:** `PUT /api/symbols/{id}/name`
- **Body:**
```json
{
  "name": "Yeni Özel İsim"
}
```

### 6. Sağlık Kontrolü (Render Health Check)
- **Endpoint:** `GET /health`
