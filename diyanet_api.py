
import requests
import json
import logging as logger
from bs4 import BeautifulSoup


class DiyanetApi:
    BASE_URL = "https://namazvakitleri.diyanet.gov.tr/tr-TR/"

    def _make_request(self, url, params=None):
        try:
            logger.info(f"API isteği yapılıyor: {url}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"API isteği başarısız oldu: {e}")
        except json.JSONDecodeError:
            logger.error("API yanıtı geçerli bir JSON değil.")

    def get_districts(self, city_id):
        url = f"{self.BASE_URL}home/GetRegList"
        params = {'ChangeType': 'state', 'CountryId': '2', 'Culture': 'tr-TR', 'StateId': city_id}
        districts = self._make_request(url, params).json().get('StateRegionList', [])
        return {d.get("IlceAdi"): d.get("IlceID") for d in districts}

    def fetch_prayer_times(self, district_id):
        url = f"{self.BASE_URL}{district_id}"
        response = self._make_request(url)
        return self.parse_times(response.text)

    def parse_times(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        logger.info(f"Soup: {soup.title.string}")
        table = soup.select_one("#tab-1 .vakit-table tbody")

        if not table:
            logger.error("Vakit tablosu bulunamadı")
            return None

        data = {}
        for row in table.find_all("tr"):
            cells = [td.text.strip() for td in row.find_all("td")]
            tarih = cells[0].split()[:3]
            tarih_iso = f"{tarih[2]}-{self.month_to_number(tarih[1])}-{tarih[0]}"
            vakitler = cells[2:]
            data[tarih_iso] = vakitler
        return data

    @staticmethod
    def month_to_number(month_name):
        months = {
            "Ocak": "01", "Şubat": "02", "Mart": "03", "Nisan": "04",
            "Mayıs": "05", "Haziran": "06", "Temmuz": "07", "Ağustos": "08",
            "Eylül": "09", "Ekim": "10", "Kasım": "11", "Aralık": "12"
        }
        return months.get(month_name, None)
