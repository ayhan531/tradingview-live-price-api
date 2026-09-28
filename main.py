import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.config import PORT, HOST
from app.services.tv_engine import tv_engine
from app.api.routes import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken: TradingView fiyat motorunu çalıştır
    logger.info("Antigravity Fiyat Sunucusu başlatılıyor...")
    await tv_engine.start()
    yield
    # Uygulama kapanırken: Görevleri temizle
    logger.info("Sunucu kapatılıyor...")
    await tv_engine.stop()

app = FastAPI(
    title="TradingView Canlı Fiyat API & Yönetim Paneli",
    description="Her 10 saniyede bir güncellenen hisse, kripto, emtia ve forex fiyatları API'si.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS ayarları: Herhangi bir web sitesinden veya mobil uygulamadan serbestçe erişilsin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin Paneli Web Arayüzü Ana Sayfası
TEMPLATES_DIR = Path(__file__).resolve().parent / "app" / "templates"
INDEX_HTML_PATH = TEMPLATES_DIR / "index.html"

@app.get("/", response_class=HTMLResponse, summary="Admin Paneli")
async def admin_dashboard():
    if INDEX_HTML_PATH.exists():
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h1>Admin paneli dosyası bulunamadı.</h1>", status_code=500)

# API Rotalarını dahil et
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Sunucu başlatılıyor: http://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
