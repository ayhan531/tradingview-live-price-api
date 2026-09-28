import json
import logging
import re
from typing import List, Dict, Optional, Any
from app.config import SYMBOLS_FILE, INITIAL_SYMBOLS_FILE

logger = logging.getLogger("symbol_store")

def slugify(text: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9_]', '_', text.strip().lower())
    s = re.sub(r'_+', '_', s).strip('_')
    return s or "item"

class SymbolStore:
    def __init__(self):
        self._symbols: List[Dict[str, Any]] = []
        self._id_map: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        """Kayıtlı sembol listesini JSON dosyasından yükler."""
        target_path = SYMBOLS_FILE if SYMBOLS_FILE.exists() else INITIAL_SYMBOLS_FILE
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._symbols = data
                self._id_map = {item["id"]: item for item in self._symbols}
                logger.info(f"{len(self._symbols)} sembol başarıyla yüklendi ({target_path.name})")
        except Exception as e:
            logger.error(f"Sembol dosyası yüklenirken hata: {e}")
            self._symbols = []
            self._id_map = {}

    def save(self):
        """Sembol listesini kalıcı dosyaya yazar."""
        try:
            SYMBOLS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SYMBOLS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._symbols, f, ensure_ascii=False, indent=2)
            logger.info(f"Sembol listesi kaydedildi ({len(self._symbols)} öğe)")
        except Exception as e:
            logger.error(f"Sembol listesi kaydedilirken hata: {e}")

    def get_all(self) -> List[Dict[str, Any]]:
        """Tüm sembolleri döner."""
        return list(self._symbols)

    def get_by_id(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        return self._id_map.get(symbol_id)

    def update_name(self, symbol_id: str, new_name: str) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının belirlediği özel görünen ismi (display_name) günceller.
        ÖNEMLİ KURAL: tv_ticker ve original_name ASLA değişmez!
        TradingView bağlantısı bozulmaz.
        """
        item = self._id_map.get(symbol_id)
        if not item:
            return None
        
        new_name = new_name.strip()
        if not new_name:
            raise ValueError("İsim boş olamaz!")

        item["display_name"] = new_name
        self.save()
        logger.info(f"Sembol ID {symbol_id} adı '{new_name}' olarak güncellendi. TV Ticker: {item.get('tv_ticker')}")
        return item

    def add_symbol(self, tv_ticker: str, display_name: Optional[str] = None, original_name: Optional[str] = None, category: str = "Stock", description: str = "") -> Dict[str, Any]:
        """
        TradingView'den arama sonucunda bulunan yeni bir hisse/varlığı listeye ekler.
        """
        tv_ticker = tv_ticker.strip().upper()
        # Eğer zaten varsa mevcut olanı döner
        for s in self._symbols:
            if s.get("tv_ticker", "").upper() == tv_ticker:
                return s

        clean_code = tv_ticker.split(":")[-1] if ":" in tv_ticker else tv_ticker
        base_id = slugify(clean_code)
        unique_id = base_id
        counter = 1
        while unique_id in self._id_map:
            unique_id = f"{base_id}_{counter}"
            counter += 1

        disp = (display_name or clean_code).strip()
        orig = (original_name or clean_code).strip()

        new_item = {
            "id": unique_id,
            "original_name": orig,
            "display_name": disp,
            "tv_ticker": tv_ticker,
            "category": category,
            "description": description or f"{disp} ({tv_ticker})"
        }

        self._symbols.append(new_item)
        self._id_map[unique_id] = new_item
        self.save()
        logger.info(f"Yeni sembol eklendi: {unique_id} ({tv_ticker})")
        return new_item

    def remove_symbol(self, symbol_id: str) -> bool:
        """Listeden sembol siler."""
        if symbol_id not in self._id_map:
            return False
        
        self._symbols = [s for s in self._symbols if s["id"] != symbol_id]
        del self._id_map[symbol_id]
        self.save()
        logger.info(f"Sembol silindi: {symbol_id}")
        return True

    def reset_to_defaults(self):
        """Varsayılan 171 sembol listesine geri döner."""
        if INITIAL_SYMBOLS_FILE.exists():
            with open(INITIAL_SYMBOLS_FILE, "r", encoding="utf-8") as f:
                self._symbols = json.load(f)
            self._id_map = {item["id"]: item for item in self._symbols}
            self.save()
            return True
        return False

symbol_store = SymbolStore()
