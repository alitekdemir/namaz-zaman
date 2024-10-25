import tkinter as tk
from tkinter import ttk
from helper import Utility, ZamanGetir

class SettingsWindow:
    """Bölge seçimi için popup pencere sınıfı"""
    
    def __init__(self, parent=None, callback=None):
        self.parent = parent
        self.callback = callback
        self.manager = ZamanGetir()
        
        # Popup penceresi oluştur
        self.popup = tk.Toplevel(parent) if parent else tk.Tk()
        self.popup.title("Bölge Seçimi")
        
        # Pencereyi ortala
        self.center_window()
        
        # Popup ayarları
        self.popup.attributes("-topmost", True)
        self.popup.grab_set()  # Modal pencere yap
        
        self.setup_ui()
        
    def center_window(self):
        """Popup penceresini ekranın ortasına konumlandır"""
        window_width = 300
        window_height = 200
        
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
    def setup_ui(self):
        """Kullanıcı arayüzü elemanlarını oluştur"""
        # Ana frame
        main_frame = ttk.Frame(self.popup, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # İl seçim frame
        city_frame = ttk.LabelFrame(main_frame, text="İl Seçimi", padding="5")
        city_frame.pack(fill=tk.X, pady=5)
        
        # İl giriş alanı
        self.city_entry = ttk.Entry(city_frame)
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
        self.district_button = ttk.Button(district_frame, text="Onayla", 
                                        command=self.confirm_district, 
                                        state="disabled")
        self.district_button.pack(side=tk.LEFT, padx=5)
        
        # Durum mesajı etiketi
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(fill=tk.X, pady=5)
        
        # İl verilerini yükle
        self.cities = Utility.load_json(self.manager.PLAKA_KODU)
        
        # Başlangıç odağı
        self.city_entry.focus()
        
    def show_status(self, message, is_error=False):
        """Durum mesajını göster"""
        self.status_label.configure(
            text=message, 
            foreground="red" if is_error else "black"
        )
        
    def confirm_city(self):
        """İl onayını işle"""
        plaka_no = self.city_entry.get().strip()
        
        # İl kodunu doğrula
        city_info = None
        for city in self.cities:
            if city['PlakaNo'] == plaka_no:
                city_info = city
                break
        
        if not city_info:
            self.show_status(
                f"Hata: {plaka_no} plaka koduna sahip şehir bulunamadı.", 
                True
            )
            return
        
        self.show_status("İlçe listesi getiriliyor...")
        self.popup.update()
        
        try:
            # İlçeleri getir
            self.selected_city = city_info
            districts = self.manager.get_districts(city_info['il_id'])
            
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
            
    def confirm_district(self):
        """İlçe onayını işle"""
        if not hasattr(self, 'districts') or not self.districts:
            return
            
        selected_index = self.district_combo.current()
        if selected_index < 0:
            return
            
        selected_district = self.districts[selected_index]
        
        self.show_status("Namaz vakitleri getiriliyor...")
        self.popup.update()
        
        try:
            # Ayarları kaydet
            settings = {
                'il': self.selected_city['il_adi'],
                'il_id': self.selected_city['il_id'],
                'ilce_adi': selected_district['IlceAdi'],
                'ilce_id': selected_district['IlceID']
            }
            Utility.save_json("ayarlar.json", settings)
            
            # Namaz vakitlerini güncelle
            self.manager.URL = f"{self.manager.BASE_URL}{selected_district['IlceID']}"
            self.manager.update_times()
            
            self.show_status("İşlem tamamlandı.")
            self.popup.after(1000, self.close_popup)
            
            # Callback'i çağır
            if self.callback:
                self.callback(settings)
                
        except Exception as e:
            self.show_status(f"Hata: Vakitler alınamadı - {str(e)}", True)
            
    def close_popup(self):
        """Popup penceresini kapat"""
        self.popup.destroy()
        
    def run(self):
        """Popup penceresini başlat"""
        self.popup.mainloop()
