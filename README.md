# NamazZaman

**NamazZaman** - Windows 10 için hafif ve kullanışlı bir namaz vakti geri sayım widget'ı. Diyanet tarafından sağlanan namaz vakitlerini indirir ve bir sonraki namaza kadar kalan süreyi anlık olarak gösterir. Çalışma veya öğrenme sırasında hızlı bir bakış aracı olarak tasarlanmıştır.

![NamazZaman Screenshot](/screenshots/2024-10-24%20030922.png)
![NamazZaman Screenshot](/screenshots/2024-10-24%20030956.png)
![NamazZaman Screenshot](/screenshots/2024-10-24%20031140.png)
![NamazZaman Screenshot](/screenshots/2024-10-24%20031752.png)


## Özellikler

- **Hafif ve Küçük:** 100x34px boyutunda minimal bir widget.
- **Her Zaman Üstte:** Diğer pencerelerin üzerinde kalır, hızlı erişim sağlar.
- **Geri Sayım:** Bir sonraki namaz vakti için geri sayım gösterir.
- **Kullanıcı Dostu:** Kolay taşınabilir ve konumlandırılabilir.
- **Özelleştirilebilir:** Opaklık ve görüntüleme formatı (yatay/dikey) ayarlanabilir.
- **Manuel Güncelleme:** Namaz vakitlerini manuel olarak güncelleyebilirsiniz.

## Kurulum

### Gereksinimler

- **Python 3.6+**
- Gerekli Python Kütüphaneleri:
  - `tkinter`
  - `requests`
  - `beautifulsoup4`

### Adımlar

1. **Depoyu Klonlayın:**

  ```bash
  git clone https://github.com/kullanici-adi/namaz-zaman.git
  cd namaz-zaman
  ```

2. **Gerekli Kütüphaneleri Yükleyin:**

  `pip install -r requirements.txt`

  Alternatif olarak, aşağıdaki komutu kullanabilirsiniz:

  `pip install requests beautifulsoup4`

3. **Uygulamayı Çalıştırın:**

  `python namaz_zaman.py`

## Kullanım

- **Taşıma:** Widget'a tıklayıp sürükleyerek ekran üzerinde istediğiniz konuma taşıyabilirsiniz.
- **Sağ Tıklama Menüsü:**
  - **Vakitleri Güncelle:** Namaz vakitlerini manuel olarak günceller.
  - **Opacity Değiştir:** Widget'ın opaklığını %50, %75 veya %100 olarak ayarlayabilirsiniz.
  - **Yön:** Zaman görüntüleme biçimini yatay veya dikey olarak değiştirebilirsiniz.
  - **Kapat:** Widget'ı kapatır.
- **Kapatma:** `Escape` tuşuna basarak widget'ı kapatabilirsiniz.

## Lisans

Bu proje [MIT Lisansı](https://opensource.org/licenses/MIT) ile lisanslanmıştır. Daha fazla bilgi için [LICENSE](https://opensource.org/licenses/MIT) dosyasına bakabilirsiniz.
Projeniz için yaygın olarak kullanılan [MIT Lisansı](https://opensource.org/licenses/MIT) önerilmektedir. MIT Lisansı, projenizin açık kaynak olarak paylaşılmasını sağlar ve kullanıcılara geniş kullanım hakları tanır.

Copyright (c) [2024] [Ali Tekdemir]

## İletişim

Proje ile ilgili sorularınız veya önerileriniz için e-mail adresimden bana ulaşabilirsiniz.

## Teşekkürler

Diyanet İşleri Başkanlığı: Namaz vakitlerini sağladıkları için teşekkür ederiz.
Python ve Tkinter: Bu projeyi mümkün kılan güçlü araçlar.

---
