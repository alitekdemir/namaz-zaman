import customtkinter as ctk
from tkinter import colorchooser
from tools import Tools
from diyanet_api import DiyanetApi

class SettingsWindow:
    def __init__(self, root):
        self.root = root
        self._settings = Tools.get_settings()
        self.district_mapping = {}
        self.window = self._setup_window()
        self._init_ui()

    def _setup_window(self):
        win = ctk.CTkToplevel(self.root)
        win.title("Ayarlar")
        screen_x, screen_y = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"400x540+{screen_x//2-200}+{screen_y//2-250}")
        return win

    def _init_ui(self):
        # Aktif konum gösterimi
        loc = self._settings['LOCATION']
        ctk.CTkLabel(self.window, 
            text=f"Aktif Konum: {loc['district']['name']} / {loc['city']['name']}",
            font=("Arial", 12, "bold")).pack(pady=5)
        
        # İl-İlçe seçimi bölümü
        select_frame = ctk.CTkFrame(self.window)
        select_frame.pack(fill='x', padx=10, pady=5) # pady genel üst ve alt boşluk
        
        # İl seçimi
        city_frame = ctk.CTkFrame(select_frame)
        city_frame.pack(fill='x', padx=10, pady=10)
        ctk.CTkLabel(city_frame, text="Plaka:", width=60).pack(side='left', padx=5)
        self.city_entry = ctk.CTkEntry(city_frame, width=60)
        self.city_entry.pack(side='left', padx=5)
        
        if current_city := next((c for c in Tools.get_cities() 
                               if c['id'] == loc['city']['id']), None):
            self.city_entry.insert(0, current_city['plaka'])
        
        ctk.CTkButton(city_frame, text="İlçeleri Getir", width=100,
                     command=self._fetch_districts).pack(side='right', padx=5)
        
        # İlçe seçimi
        district_frame = ctk.CTkFrame(select_frame)
        district_frame.pack(fill='x', padx=10, pady=2)
        ctk.CTkLabel(district_frame, text="İlçe:", width=60).pack(side='left', padx=5)
        self.district_combo = ctk.CTkComboBox(district_frame, width=160, values=[])
        self.district_combo.pack(side='left', padx=5)
        self.district_combo.set(loc['district']['name'])
        
        ctk.CTkButton(district_frame, text="Kaydet", width=100,
                     command=self._save_location).pack(side='right', padx=5)


        # # Vakitleri Güncelleme bölümü
        # update_frame = ctk.CTkFrame(select_frame)
        # update_frame.pack(fill='x', padx=10, pady=5)
        ctk.CTkButton(select_frame, text="Vakitleri İndir", command=self._update_times).pack(pady=10)
        # Başlık
        # self.status = ctk.CTkLabel(update_frame, text="Vakitleri güncellemek için ilçe seçiniz",)
        # self.status.pack(side='top', padx=5)


        # Görünüm ayarları
        view_frame = ctk.CTkFrame(self.window)
        view_frame.pack(fill='x', padx=15, pady=(0, 15)) # pady alt boşluk arttırıldı

        self.direction_var = ctk.StringVar(value=self._settings['DISPLAY']['orientation'])
        orient_frame = ctk.CTkFrame(view_frame)
        orient_frame.pack(fill='x', padx=5, pady=(10, 5))
        ctk.CTkLabel(orient_frame, text="Görünüm:", width=70).pack(side='left', padx=(5, 10))
        for text, val in [("Yatay", "horizontal"), ("Dikey", "vertical")]:
            ctk.CTkRadioButton(orient_frame, text=text, variable=self.direction_var,
                             value=val, command=self._save_display).pack(side='left', padx=(0, 10))



        # Saniye Göster/Gizle RadioButton
        seconds_frame = ctk.CTkFrame(view_frame)
        seconds_frame.pack(fill='x', padx=5, pady=(5, 10))
        ctk.CTkLabel(seconds_frame, text="Saniye:", width=70).pack(side='left', padx=5)
        
        self.seconds_var = ctk.StringVar(value="Göster" if self._settings['DISPLAY'].get('show_seconds', True) else "Gizle")
        
        for text, val in [("Göster", "Göster"), ("Gizle", "Gizle")]:
            ctk.CTkRadioButton(seconds_frame, text=text, variable=self.seconds_var,
                     value=val, command=self._save_display).pack(side='left', padx=0)


        # Renk ayarları
        colors_frame = ctk.CTkFrame(self.window)
        colors_frame.pack(fill='x', padx=15, pady=(0, 15))
        ctk.CTkLabel(colors_frame, text="Renk Ayarları", 
                    font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        for name, key in [("Normal", "standard"), ("1. Uyarı", "warning"), ("2. Uyarı", "critical")]:
            row = ctk.CTkFrame(colors_frame)
            row.pack(fill='x', pady=5, padx=10)
            ctk.CTkLabel(row, text=name, width=70).pack(side='left', padx=(5, 10))

            for ctype in ['background', 'text']:
                color = self._settings['COLORS'][key][ctype]
                btn = ctk.CTkButton(row, text='', width=40, height=40, fg_color=color)
                btn.configure(command=lambda key=key, ctype=ctype, button=btn: self._pick_color(key, ctype, button))
                btn.pack(side='left', padx=(0, 5))
            
            if key != "standard":
                e = ctk.CTkEntry(row, width=50, justify='center')
                e.insert(0, str(self._settings['COLORS'][key]['trigger']))
                # e.bind('<FocusIn>', lambda e, key=key: self._show_tooltip(key, e.widget))
                e.bind('<FocusOut>', lambda e, key=key: self._save_trigger(key, e.widget))
                e.pack(side='left', padx=5)

        # Status mesajını gösterecek bir etiket oluşturur
        self.status = ctk.CTkLabel(self.window, text="Vakitleri güncellemek için ilçe seçiniz")
        self.status.pack(side='top', padx=5)

    def _fetch_districts(self):
        city_code = self.city_entry.get().strip()
        if not city_code:
            return self._show_status("Plaka kodu giriniz!", "error")
            
        if city := next((c for c in Tools.get_cities() if c['plaka'] == city_code), None):
            if districts := DiyanetApi().get_districts(city['id']):
                self.district_mapping = districts
                district_names = list(districts.keys())
                self.district_combo.configure(values=district_names)
                self.district_combo.set(district_names[0])
                self._show_status(f"{len(districts)} ilçe bulundu", "success")
            else:
                self._show_status("İlçeler alınamadı!", "error")
        else:
            self._show_status("Geçersiz plaka kodu!", "error")

    def _save_location(self):
        city_code = self.city_entry.get().strip()
        district_name = self.district_combo.get()
        
        if not (city_code and district_name in self.district_mapping):
            return self._show_status("Geçerli il ve ilçe seçiniz!", "error")
            
        if city := next((c for c in Tools.get_cities() if c['plaka'] == city_code), None):
            self._settings['LOCATION'].update({
                'city': {'name': city['il'], 'id': city['id']},
                'district': {'name': district_name, 'id': self.district_mapping[district_name]}
            })
            self._save_settings("Konum kaydedildi")

    def _update_times(self):
        if times := DiyanetApi().fetch_prayer_times(self._settings['LOCATION']['district']['id']):
            Tools.update_prayer_times(times)
            self._show_status("Vakitler güncellendi", "success")
            if hasattr(self.root, 'clock_widget'):
                self.root.clock_widget._prayer_times = Tools.get_prayer_times()
                self.root.clock_widget._next_prayer_time = Tools.find_next_prayer_time(self.root.clock_widget._prayer_times)
                self.root.clock_widget.update_clock()
        else:
            self._show_status("Güncelleme başarısız", "error")

    def _pick_color(self, key, ctype, button):
        if color := colorchooser.askcolor()[1]:
            self._settings['COLORS'][key][ctype] = color
            self._save_settings()
            button.configure(fg_color=color)

    def _save_trigger(self, key, entry):
        try:
            value = max(1, int(entry.get()))
            self._settings['COLORS'][key]['trigger'] = value
            self._save_settings()
        except ValueError:
            entry.delete(0, 'end')
            entry.insert(0, str(self._settings['COLORS'][key]['trigger']))

    def _save_display(self, value=None):  # İsteğe bağlı value parametresi eklendi
        self._settings['DISPLAY'].update({
            # Orientation ayarını kaydetme
            'orientation': self.direction_var.get(),
            # Saniye göster/gizle ayarını kaydetme
            # 'show_seconds': self.seconds_var.get()
            'show_seconds': (self.seconds_var.get() == "Göster")
        })
        self._save_settings()
        if hasattr(self.root, 'clock_widget'):
            self.root.clock_widget.update_orientation()

    def _save_settings(self, msg=None):
        Tools.update_settings(self._settings)
        if msg: self._show_status(msg, "success")
        if hasattr(self.root, 'clock_widget'):
            self.root.clock_widget.update_clock()

    def _show_status(self, msg, level="info"):
        self.status.configure(text=msg, text_color={"info":"gray","success":"green","error":"red"}[level])