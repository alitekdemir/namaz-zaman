import os
import locale
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class ZamanGetir:
    """Namaz vakitlerini web sitesinden çeken, parse eden ve JSON dosyasına kaydeden sınıf."""
    BASE_URL = "https://namazvakitleri.diyanet.gov.tr/tr-TR/"
    URL = f"{BASE_URL}9541/istanbul-icin-namaz-vakti"

    def __init__(self, file_name="vakitler.json"):
        self.url = self.URL
        self.file_name = file_name
        self.locale_set = False

    def fetch_html(self):
        """Web sitesinden HTML içeriğini çeker."""
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"HTML çekme hatası: {e}")
            raise

    def parse_html(self, html_content):
        """
        Çekilen HTML içeriğinden namaz vakitlerini parse eder.
        Verileri bir sözlük olarak döner: {"tarih": ["imsak", "güneş", ...]}.
        """
        # Locale sadece burada bir defa çalışacak
        self.set_locale_once()
        soup = BeautifulSoup(html_content, 'html.parser')
        tablo = soup.select_one("#tab-1 .vakit-table tbody")

        if not tablo:
            raise ValueError("Namaz vakitleri tablosu bulunamadı.")

        veriler = {}
        for row in tablo.find_all("tr"):
            hucreler = [td.text.strip() for td in row.find_all("td")]
            tarih = datetime.strptime(hucreler[0], "%d %B %Y %A").strftime("%Y-%m-%d")
            vakitler = hucreler[2:]
            veriler[tarih] = vakitler
        
        return veriler

    def save_json(self, veriler):
        """Parse edilen vakitleri JSON dosyasına kaydeder."""
        try:
            with open(self.file_name, "w", encoding="utf-8") as json_dosya:
                json.dump(veriler, json_dosya, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"JSON kaydetme hatası: {e}")
            raise

    def load_json(self):
        """JSON dosyasından vakitleri yükler."""
        try:
            with open(self.file_name, "r", encoding="utf-8") as json_dosya:
                return json.load(json_dosya)
        except (IOError, json.JSONDecodeError) as e:
            print(f"JSON yükleme hatası: {e}")
            return None

    def set_locale_once(self):
        """Yerel ayarları Türkçe'ye bir defa ayarlar."""
        if not self.locale_set:
            try:
                locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")
            except locale.Error:
                locale.setlocale(locale.LC_TIME, "")
            self.locale_set = True

    def get_times(self):
        """Vakitler dosyasını yükler veya günceller."""
        veriler = self.load_json()

        # if not all([veriler, self.date_in_file(veriler)]):
        if not veriler or not self.date_in_file(veriler):
            self.update_times()
            veriler = self.load_json()

        return veriler

    def date_in_file(self, veriler):
        """JSON dosyasındaki verilerin güncel olup olmadığını kontrol eder."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return current_date in veriler

    def update_times(self):
        """Web sitesinden vakitleri çekip JSON dosyasına kaydeder."""
        html_content = self.fetch_html()
        veriler = self.parse_html(html_content)
        self.save_json(veriler)

    def is_data_up_to_date(self, last_updated):
        """JSON dosyasındaki verilerin güncel olup olmadığını kontrol eder."""
        if not last_updated:
            return False  # Eğer tarih bilgisi yoksa veri güncel değildir

        try:
            last_updated_date = datetime.strptime(last_updated, "%Y-%m-%d")
            return datetime.now() - last_updated_date < timedelta(weeks=1)
        except ValueError:
            return False

class ZamanHesapla:
    @staticmethod
    def find_next_prayer_time(vakitler):
        """Verilen vakitler listesinden bir sonraki namaz vaktini bulur."""
        now = datetime.now()
        for vakit in vakitler:
            vakit_zamani = datetime.strptime(vakit, "%H:%M").time()
            if vakit_zamani > now.time():
                return datetime.combine(now.date(), vakit_zamani)
        return None

    @staticmethod
    def timedelta_to_hms(td):
        """Bir timedelta objesini HH:MM:SS formatına çevirir."""
        total_seconds = max(int(td.total_seconds()), 0)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        # return f"{hours:02}:{minutes:02}:{seconds:02}"
        return f"{hours}:{minutes:02}:{seconds:02}"

    @staticmethod
    def get_countdown(prayer_datetime):
        """Bir namaz vakti için geri sayımı hesaplar."""
        remaining_time = prayer_datetime - datetime.now()
        return ZamanHesapla.timedelta_to_hms(remaining_time)



# Kullanım Örneği
if __name__ == "__main__":
    manager = ZamanGetir()
    vakitler = manager.get_times()
    if vakitler:
        print("Güncel namaz vakitleri:")
        for tarih, vakit in vakitler.items():
            print(f"{tarih}: {', '.join(vakit)}")
    else:
        print("Namaz vakitleri yüklenemedi.")
