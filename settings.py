import tkinter as tk
from tkinter import ttk
from helper import Utility, ZamanGetir
from config import ConfigManager
import logging

class SettingsWindow:
    """Bölge seçimi için popup pencere sınıfı"""

    def __init__(self, parent = None, callback = None):
        """
        SettingsWindow sınıfını başlat.
        
        Args:
            parent: Üst pencere referansı
            callback: Seçim tamamlandığında çağrılacak fonksiyon
        """
        self.parent = parent
        self.callback = callback
        self.manager = ZamanGetir()
        self.config = ConfigManager()
        
        # Popup penceresi oluştur
        self.popup = tk.Toplevel(parent) if parent else tk.Tk()
        self.popup.title("Bölge Seçimi")
        
        # Pencere özellikleri
        self.popup.resizable(False, False)
        self.popup.attributes("-topmost", True)
        self.popup.grab_set()  # Modal pencere yap
        
        # UI bileşenleri
        self.city_entry = None
        self.district_combo = None
        self.district_button = None
        self.status_label = None
        
        # Veri değişkenleri
        self.plakalar: list = []
        self.districts: list = []
        self.selected_city = None
        
        self.setup_ui()
        self.center_window()

    def center_window(self) -> None:
        """Popup penceresini ekranın ortasına konumlandır"""
        # Pencereyi pack ile yerleştirdikten sonra güncelle
        self.popup.update_idletasks()
        
        # Pencere boyutlarını al
        window_width = self.popup.winfo_width()
        window_height = self.popup.winfo_height()
        
        # Ekran boyutlarını al
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        
        # Merkez koordinatları hesapla
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Pencereyi konumlandır
        self.popup.geometry(f"+{x}+{y}")

    def setup_ui(self) -> None:
        """Kullanıcı arayüzü elemanlarını oluştur"""
        # Ana frame
        main_frame = ttk.Frame(self.popup, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # İl seçim frame
        city_frame = ttk.LabelFrame(main_frame, text="İl Plaka Kodu", padding="5")
        city_frame.pack(fill=tk.X, pady=5)
        
        # Plaka kodu giriş alanı
        vcmd = (self.popup.register(self.validate_plaka), '%P')
        self.city_entry = ttk.Entry(city_frame, validate='key', validatecommand=vcmd)
        self.city_entry.pack(side=tk.LEFT, padx=5, expand=True)
        self.city_entry.bind('<Return>', lambda e: self.confirm_city())
        
        # İl onay butonu
        city_button = ttk.Button(city_frame, text="Onayla", command=self.confirm_city)
        city_button.pack(side=tk.LEFT, padx=5)
        
        # İlçe seçim frame
        district_frame = ttk.LabelFrame(main_frame, text="İlçe Seçimi", padding="5")
        district_frame.pack(fill=tk.X, pady=5)
        
        # İlçe dropdown
        self.district_combo = ttk.Combobox(district_frame, state="disabled")
        self.district_combo.pack(side=tk.LEFT, padx=5, expand=True)
        
        # İlçe onay butonu
        self.district_button = ttk.Button(
            district_frame, 
            text="Onayla", 
            command=self.confirm_district, 
            state="disabled"
        )
        self.district_button.pack(side=tk.LEFT, padx=5)
        
        # Durum mesajı etiketi
        self.status_label = ttk.Label(main_frame, text="", wraplength=250)
        self.status_label.pack(fill=tk.X, pady=5)
        
        # İl verilerini yükle
        self.plakalar = Utility.load_json(self.manager.PLAKA_KODU)
        if not self.plakalar:
            self.show_status("İl verileri yüklenemedi!", True)
            return
            
        # Başlangıç odağı
        self.city_entry.focus()

    def validate_plaka(self, value: str) -> bool:
        """
        Plaka kodunun geçerliliğini kontrol et.
        
        Args:
            value: Kontrol edilecek değer
            
        Returns:
            bool: Değer geçerliyse True
        """
        if len(value) > 2:
            return False
        return value.isdigit() or value == ""

    def show_status(self, message: str, is_error: bool = False) -> None:
        """
        Durum mesajını göster.
        
        Args:
            message: Gösterilecek mesaj
            is_error: Hata mesajı ise True
        """
        self.status_label.configure(
            text=message, 
            foreground="red" if is_error else "black"
        )
        self.popup.update()

    def confirm_city(self) -> None:
        """İl onayını işle"""
        plaka_no = self.city_entry.get().strip()
        
        # Plaka kodu boş kontrolü
        if not plaka_no:
            self.show_status("Lütfen bir plaka kodu girin!", True)
            return
        
        # İl kodunu doğrula
        city_info = None
        for city in self.plakalar:
            if city['PlakaNo'] == plaka_no:
                city_info = city
                break
        
        if not city_info:
            self.show_status(f"Hata: {plaka_no} plaka koduna sahip şehir bulunamadı.", True)
            return
        
        self.show_status("İlçe listesi getiriliyor...")
        
        try:
            # İlçeleri getir
            self.selected_city = city_info
            districts = self.manager.get_districts(city_info['il_id'])
            
            if not districts:
                self.show_status("İlçe listesi boş!", True)
                return
            
            # İlçe dropdown'ını güncelle
            self.districts = districts
            self.district_combo['values'] = [d['IlceAdi'] for d in districts]
            self.district_combo.current(0)
            
            # İlçe seçimini etkinleştir
            self.district_combo['state'] = 'readonly'
            self.district_button['state'] = 'normal'
            
            self.show_status(f"{city_info['il_adi']} için ilçeler yüklendi.")
            
        except Exception as e:
            self.show_status(f"Hata: İlçeler yüklenemedi - {str(e)}", True)

    def confirm_district(self) -> None:
        """İlçe onayını işle"""
        if not self.selected_city or not self.districts:
            self.show_status("Önce il seçimi yapın!", True)
            return
            
        selected_index = self.district_combo.current()
        if selected_index < 0:
            self.show_status("Lütfen bir ilçe seçin!", True)
            return
            
        selected_district = self.districts[selected_index]
        logging.debug(f"Selected district: {selected_district}")
        
        self.show_status("Namaz vakitleri getiriliyor...")
        
        try:
            # Mevcut ayarları yükle
            current_config = self.config.get_config()
            logging.debug(f"Current config: {current_config}")
            
            # Lokasyon ayarlarını güncelle
            current_config["LOCATION"].update({
                'il_adi': self.selected_city['il_adi'],
                'il_id': self.selected_city['il_id'],
                'ilce_adi': selected_district['IlceAdi'],
                'ilce_id': selected_district['IlceID']
            })
            
            # Tüm ayarları kaydet
            self.config.save_config(current_config)
            logging.info(f"Ayarlar güncellendi. Yeni lokasyon: {current_config['LOCATION']}")
            
            # Namaz vakitlerini güncelle
            self.manager.URL = f"{self.manager.BASE_URL}{selected_district['IlceID']}"
            logging.debug(f"Namaz vakitleri URL: {self.manager.URL}")
            self.manager.update_times()
            
            self.show_status("İşlem tamamlandı.")
            
            # Callback'i çağır ve popup'ı kapat
            if self.callback:
                self.callback(current_config["LOCATION"])
                
            self.popup.after(1000, self.close_popup)
                
        except Exception as e:
            logging.error(f"Error: {e}")
            self.show_status(f"Hata: Vakitler alınamadı - {str(e)}", True)

    def close_popup(self) -> None:
        """Popup penceresini kapat"""
        self.popup.destroy()

    def run(self) -> None:
        """Popup penceresini başlat"""
        self.popup.mainloop()