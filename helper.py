import json
import locale
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


class Utility:
    """JSON dosyalarını yükleme ve kaydetme işlemlerini yönetir."""
    @staticmethod
    def get_working_directory():
        return Path(__file__).parent

    @staticmethod
    def configure_logging(file_name, log_level=logging.INFO):
        LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(filename)s.%(funcName)-30s] - %(message)s"
        file_path = Utility.get_working_directory() / file_name
        logging.basicConfig(filename=file_path, level=log_level, format=LOG_FORMAT, force=True)

    @staticmethod
    def save_json(file_name, data):
        try:
            with open(file_name, "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=2)
            logging.info(f"Veriler '{file_name}' dosyasına başarıyla kaydedildi.")
        except IOError as e:
            logging.error(f"JSON kaydetme hatası: {e}")
            raise

    @staticmethod
    def load_json(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
            logging.info(f"Veriler '{file_name}' dosyasından başarıyla yüklendi.")
            return data
        except FileNotFoundError:
            logging.error(f"Hata: '{file_name}' dosyası bulunamadı.")
            return None
        except json.JSONDecodeError:
            logging.error(f"Hata: '{file_name}' dosyası geçerli bir JSON değil.")
            return None


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
        if not self.locale_set:
            try:
                locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")
                logging.info("Locale 'tr_TR.UTF-8' olarak ayarlandı.")
            except locale.Error:
                locale.setlocale(locale.LC_TIME, "")
                logging.warning("Türkçe locale ayarlanamadı. Varsayılan locale kullanılıyor.")
            self.locale_set = True

    def fetch_html(self):
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
        self.set_locale_once()
        soup = BeautifulSoup(html_content, 'html.parser')
        tablo = soup.select_one("#tab-1 .vakit-table tbody")

        if not tablo:
            logging.error("Namaz vakitleri tablosu bulunamadı.")
            raise ValueError("Namaz vakitleri tablosu bulunamadı.")

        veriler = {}
        for row in tablo.find_all("tr"):
            hucreler = [td.text.strip() for td in row.find_all("td")]
            tarih = datetime.strptime(hucreler[0], "%d %B %Y %A").strftime("%Y-%m-%d")
            vakitler = hucreler[2:]
            veriler[tarih] = vakitler

        logging.info("HTML içeriği başarıyla parse edildi.")
        return veriler

    def get_times(self):
        data = Utility.load_json(self.file_name)
        if not data or not self.date_in_file(data):
            logging.info("Vakit verileri güncel değil veya dosya mevcut değil. Güncelleniyor...")
            self.update_times()
            data = Utility.load_json(self.file_name)
        return data if data else {}

    def date_in_file(self, veriler):
        current_date = datetime.now().strftime("%Y-%m-%d")
        return current_date in veriler

    def update_times(self):
        try:
            html_content = self.fetch_html()
            vakitler = self.parse_html(html_content)
            Utility.save_json(self.file_name, vakitler)
            logging.info("Vakitler başarıyla güncellendi.")
        except Exception as e:
            logging.error(f"Vakitler güncellenirken hata oluştu: {e}")
            raise


class ZamanHesapla:
    @staticmethod
    def find_next_prayer_time(vakitler):
        now = datetime.now()
        for vakit in vakitler:
            vakit_zamani = datetime.strptime(vakit, "%H:%M").time()
            if vakit_zamani > now.time():
                return datetime.combine(now.date(), vakit_zamani)
        return None

    @staticmethod
    def get_countdown(prayer_datetime):
        remaining_time = prayer_datetime - datetime.now()
        hours, remainder = divmod(max(int(remaining_time.total_seconds()), 0), 3600)
        minutes, seconds = divmod(remainder, 60)
        return hours, minutes, seconds
