import sys
import json
import locale
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


class Utility:
    """Çeşitli yardımcı işlevler."""

    @staticmethod
    def configure_logging(file_name, log_level=logging.INFO):
        """Loglama ayarlarını yapılandırır."""
        file_path = Path(file_name)
        LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(filename)s.%(funcName)-30s] - %(message)s"
        logging.basicConfig(filename=file_path, level=log_level, format=LOG_FORMAT, force=True)

    @staticmethod
    def save_json(file_path, data):
        """Veriyi JSON dosyasına kaydeder."""
        try:
            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=2)
            logging.info(f"Veriler '{file_path}' dosyasına başarıyla kaydedildi.")
        except IOError as e:
            logging.error(f"JSON kaydetme hatası: {e}")
            raise

    @staticmethod
    def load_json(file_path):
        """JSON dosyasından veri yükler."""
        try:
            with open(file_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
            logging.info(f"Veriler '{file_path}' dosyasından başarıyla yüklendi.")
            return data
        except FileNotFoundError:
            logging.error(f"Hata: '{file_path}' dosyası bulunamadı.")
            return None
        except json.JSONDecodeError:
            logging.error(f"Hata: '{file_path}' dosyası geçerli bir JSON değil.")
            return None

    @staticmethod
    def get_working_directory() -> Path:
        """Uygulamanın çalıştığı yolu Path objesi olarak döndürür."""
        logging.debug("Çalışma dizini belirleniyor.")
        if getattr(sys, 'frozen', False):
            path = Path(sys.executable).parent
            logging.debug(f"Uygulama .exe olarak çalıştırılıyor. Çalışma dizini: {path}")
        else:
            try:
                path = Path(__file__).parent.resolve()
                logging.debug(f"Uygulama Python betiği olarak çalıştırılıyor. Çalışma dizini: {path}")
            except NameError:
                path = Path.cwd()
                logging.debug(f"Uygulama interaktif ortamda çalışıyor. Çalışma dizini: {path}")
        return path

class ZamanGetir:
    """Namaz vakitlerini web sitesinden çeken, parse eden ve JSON dosyasına kaydeden sınıf."""
    BASE_URL = "https://namazvakitleri.diyanet.gov.tr/tr-TR/"
    PLAKA_KODU = 'il_plaka.json'

    def __init__(self, file_name="vakitler.json"):
        self.URL = None
        self.file_name = file_name
        self.locale_set = False

    def get_districts(self, state_id: str) -> list:
        """Belirtilen şehre ait ilçeleri API'den getirir."""
        params = {
            'ChangeType': 'state',
            'CountryId': '2',
            'Culture': 'tr-TR',
            'StateId': state_id
        }
        try:
            url = f"{self.BASE_URL}home/GetRegList"
            response = requests.get(url, params=params)
            response.raise_for_status()
            districts = response.json().get('StateRegionList', [])
            logging.info(f"'{state_id}' il koduna ait ilçeler başarıyla çekildi.")
            return districts
        except requests.RequestException as e:
            logging.error(f"API isteği başarısız oldu: {e}")
            raise
        except json.JSONDecodeError:
            logging.error("API yanıtı geçerli bir JSON değil.")
            raise

    def set_locale_once(self):
        """Locale ayarını bir kez yapar."""
        if not self.locale_set:
            try:
                locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")
                logging.info("Locale 'tr_TR.UTF-8' olarak ayarlandı.")
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_TIME, "Turkish_Turkey.1254")
                    logging.info("Locale 'Turkish_Turkey.1254' olarak ayarlandı.")
                except locale.Error:
                    locale.setlocale(locale.LC_TIME, "")
                    logging.warning("Türkçe locale ayarlanamadı. Varsayılan locale kullanılıyor.")
            self.locale_set = True

    def fetch_html(self):
        """Web sitesinden HTML içeriğini çeker."""
        if not self.URL:
            logging.error("URL tanımlı değil.")
            raise ValueError("URL tanımlı değil.")
        try:
            response = requests.get(self.URL, timeout=10)
            response.raise_for_status()
            logging.info(f"HTML içeriği '{self.URL}' adresinden başarıyla çekildi.")
            return response.text
        except requests.RequestException as e:
            logging.error(f"HTML çekme hatası: {e}")
            raise

    def parse_html(self, html_content):
        """HTML içeriğini parse eder ve vakit verilerini döndürür."""
        self.set_locale_once()
        soup = BeautifulSoup(html_content, 'html.parser')
        tablo = soup.select_one("#tab-1 .vakit-table tbody")

        if not tablo:
            logging.error("Namaz vakitleri tablosu bulunamadı.")
            raise ValueError("Namaz vakitleri tablosu bulunamadı.")

        veriler = {}
        for row in tablo.find_all("tr"):
            hucreler = [td.text.strip() for td in row.find_all("td")]
            try:
                tarih = datetime.strptime(hucreler[0], "%d %B %Y %A").strftime("%Y-%m-%d")
                vakitler = hucreler[2:]
                veriler[tarih] = vakitler
            except ValueError as e:
                logging.error(f"Tarih parse hatası: {e}")
                continue

        logging.info("HTML içeriği başarıyla parse edildi.")
        return veriler

    def get_times(self):
        """Vakit verilerini döndürür, güncel değilse günceller."""
        data = Utility.load_json(self.file_name)
        if not data or not self.date_in_file(data):
            logging.info("Vakit verileri güncel değil veya dosya mevcut değil. Güncelleniyor...")
            self.update_times()
            data = Utility.load_json(self.file_name)
        return data

    def date_in_file(self, veriler):
        """Verilen tarihin dosyada olup olmadığını kontrol eder."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return current_date in veriler

    def update_times(self):
        """Vakit verilerini günceller ve kaydeder."""
        try:
            html_content = self.fetch_html()
            vakitler = self.parse_html(html_content)
            Utility.save_json(self.file_name, vakitler)
            logging.info("Vakitler başarıyla güncellendi.")
        except Exception as e:
            logging.error(f"Vakitler güncellenirken hata oluştu: {e}")
            raise


class ZamanHesapla:
    """Namaz vakitleri ile ilgili hesaplamaları yapan sınıf."""
    
    @staticmethod
    def find_next_prayer_time(vakitler):
        """Sonraki namaz vaktini bulur."""
        if not vakitler:
            return None
            
        now = datetime.now()
        today = now.date()
        
        for vakit in vakitler:
            try:
                vakit_zamani = datetime.strptime(vakit, "%H:%M").time()
                vakit_datetime = datetime.combine(today, vakit_zamani)
                if vakit_datetime > now:
                    return vakit_datetime
            except ValueError:
                continue
        return None

    @staticmethod
    def get_countdown(prayer_datetime):
        """Sonraki namaz vaktine kalan süreyi hesaplar."""
        if not prayer_datetime:
            return 0, 0, 0
            
        remaining_time = prayer_datetime - datetime.now()
        total_seconds = max(int(remaining_time.total_seconds()), 0)
        
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return hours, minutes, seconds