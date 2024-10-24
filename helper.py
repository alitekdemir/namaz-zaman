import json
import locale
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


def configure_logging(file_name, log_level=logging.INFO):
    """ Loglama yapılandırmasını başlatır.
    Dökümantasyon: https://docs.python.org/3/library/logging.html#logging.Formatter.formatTime
    """
    LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(filename)s.%(funcName)-30s] - %(message)s"
    file_path = Utility.get_working_directory() / file_name
    logging.basicConfig(filename=file_path, level=log_level, format=LOG_FORMAT, force=True)


class ZamanGetir:
    """Namaz vakitlerini web sitesinden çeken, parse eden ve JSON dosyasına kaydeden sınıf."""
    def __init__(self, file_name="vakitler.json"):
        self.BASE_URL = "https://namazvakitleri.diyanet.gov.tr/tr-TR/"
        self.URL = None
        self.PLAKA_KODU = 'il_plaka.json'

        # self.url = self.URL
        self.file_name = file_name
        self.locale_set = False

    # --------------------- District Information Methods ---------------------

    def save_json(self, file_name, veriler):
        """Parse edilen vakitleri JSON dosyasına kaydeder."""
        try:
            with open(file_name, "w", encoding="utf-8") as json_dosya:
                json.dump(veriler, json_dosya, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"JSON kaydetme hatası: {e}")
            raise

    def load_json(self, file_name):
        """JSON dosyasını yükler."""
        try:
            with open(file_name, "r", encoding="utf-8") as json_dosya:
                return json.load(json_dosya)
        except FileNotFoundError:
            print(f"Hata: '{file_name}' dosyası bulunamadı.")
            return None
        except json.JSONDecodeError:
            print(f"Hata: '{file_name}' dosyası geçerli bir JSON değil.")
            return None

    def get_il_id_by_plaka(self, cities: list) -> tuple:
        """Kullanıcıdan plaka no alarak ilgili il_id'yi döndürür."""
        while True:
            plaka_no = input("Plaka No giriniz: ")
            for city in cities:
                if city['PlakaNo'] == plaka_no:
                    return city['il_adi'], city['il_id']
            print(f"Hata: {plaka_no} plaka koduna sahip bir şehir bulunamadı. Tekrar deneyin.")

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
            return response.json().get('StateRegionList', [])
        except requests.RequestException as e:
            print(f"Hata: API isteği başarısız oldu: {e}")
            raise
        except json.JSONDecodeError:
            print("Hata: API yanıtı geçerli bir JSON değil.")
            raise

    def display_districts(self, districts: list) -> None:
        """İlçeleri ekrana yazdırır."""
        for n, district in enumerate(districts, 1):
            print(f"{n}. {district['IlceAdi']}")

    def ask_districts(self, districts: list) -> tuple:
        """Kullanıcıya ilçeleri gösterir ve seçim yapmasını ister."""
        while True:
            try:
                select_no = int(input("Lütfen bir ilçe seçiniz: "))
                if 1 <= select_no <= len(districts):
                    selected_district = districts[select_no - 1]
                    return selected_district['IlceID'], selected_district['IlceAdi']
                else:
                    print("Hata: Geçersiz seçim. Lütfen geçerli bir sayı giriniz.")
            except ValueError:
                print("Hata: Sayısal bir değer giriniz.")

    # --------------------- Namaz Times Methods ---------------------

    def fetch_html(self):
        """Web sitesinden HTML içeriğini çeker."""
        try:
            response = requests.get(self.URL, timeout=10)
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
        veriler = self.load_json(self.file_name)

        # if not all([veriler, self.date_in_file(veriler)]):
        if not veriler or not self.date_in_file(veriler):
            self.update_times()
            veriler = self.load_json(self.file_name)

        return veriler

    def date_in_file(self, veriler):
        """JSON dosyasındaki verilerin güncel olup olmadığını kontrol eder."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return current_date in veriler

    def update_times(self):
        """Web sitesinden vakitleri çekip JSON dosyasına kaydeder."""
        html_content = self.fetch_html()
        veriler = self.parse_html(html_content)
        self.save_json(self.file_name, veriler)

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


def show_times(vakitler):
    if vakitler:
        print("Güncel namaz vakitleri:")
        for tarih, vakit in vakitler.items():
            print(f"{tarih}: {', '.join(vakit)}")
    else:
        print("Namaz vakitleri yüklenemedi.")

def main():
    manager = ZamanGetir()
    iller = manager.load_json(manager.PLAKA_KODU)
    il, il_id = manager.get_il_id_by_plaka(iller)
    print(f"{il} için şehir kodu: {il_id}")

    districts = manager.get_districts(il_id)
    print(f"{il_id} il koduna sahip şehirdeki ilçeler:")

    manager.display_districts(districts)
    ilce_id, ilce_adi = manager.ask_districts(districts)
    print(f"Seçilen bölge: {ilce_adi}, İlçe kodu: {ilce_id}")

    data = {'il': il, 'il_id': il_id, 'ilce_adi': ilce_adi, 'ilce_id': ilce_id}
    manager.save_json("ayarlar.json", data)
    print(f"{il} için seçilen ilçe bilgileri kaydedildi.")

    manager.URL = f"{manager.BASE_URL}{ilce_id}"

    vakitler = manager.get_times()
    manager.save_json("vakitler.json", vakitler)
    show_times(vakitler)



# Kullanım Örneği
if __name__ == "__main__":
    main()
