# ⚡ KRYX NMI 1$ CHARGE GATEWAY CHECKER

> **NMI (Network Merchants Inc. / SafeSave) & DonorPerfect 1$ Charge Card Checker Web UI & REST API**  
> **Telegram Kanalı:** [t.me/KryxCheck](https://t.me/KryxCheck)  
> **Geliştirici:** [@sweartx](https://t.me/sweartx)  

---

## 🌟 Öne Çıkan Özellikler

- 🎨 **Next-Gen Electric Cyan & Obsidian Matrix Arayüzü:** Neon cam efektleri (glassmorphism), fütüristik grid arka planı, canlı telemetry hapları ve duyarlı (responsive) tasarım.
- 💳 **Tam NMI & DonorPerfect $1 Charge Uyumluluğu:** 8 adımlı güvenli NMI token oluşturma, kart/cvv şifreleme ve DonorPerfect 1$ bağış tamamlama mimarisi.
- 🔄 **Dinamik Tokenization Key & Gateway Otomatik Yenileme:** Tokenization anahtarlarını ve form parametrelerini arka planda periyodik olarak canlı tutar.
- ⚡ **Multi-Thread & Multi-Worker Uyumlu Aktif Kullanıcı Takibi:** SQLite WAL modunda çalışan, Gunicorn iş parçacıkları arasında senkronize gerçek zamanlı kullanıcı sayacı.
- 🛡️ **Render 7/24 Keep-Alive Self-Pinger:** Render.com ücretsiz planındaki uyuma (sleep) sorununu önlemek için arka planda kendi `/health` ucunu her 60 saniyede bir tetikler.
- 🔍 **Entegre BIN Sorgulama:** pulse.pst.net ve NMI veritabanı üzerinden Banka, Ülke, Kart Türü (Credit/Debit), Marka ve Seviye tespiti.
- 🔊 **Web Audio API Sentezli Ses Bildirimleri:** Charged (Approved) kartlar için pozitif tını, CVV/Bakiye uyarıları ve Declined kartlar için özel sentezlenmiş sesler.
- 📋 **Sonuç Yönetimi & Tek Tıkla İşlem:** Tek tıkla bireysel kartları veya tüm Charged/CVV kartları kopyalama, `.TXT` formatında ayrıntılı rapor indirme.
- 🚀 **Render.com & GitHub Deploy Ready:** `Procfile`, `requirements.txt` ve `render.yaml` hazır.

---

## 📁 Proje Dosya Yapısı

```
nmi kryx site/
├── app.py                 # Flask Web Uygulaması & REST API Endpoints & Keep-Alive
├── checker.py             # NMI Gateway & DonorPerfect 1$ Charge Motoru ve BIN lookup
├── requirements.txt       # Gerekli Python paketleri (Flask, gunicorn, requests, urllib3)
├── Procfile               # Render.com / Heroku gunicorn başlatma komutu
├── render.yaml            # Render.com otomatik servis yapılandırması
├── start.bat              # Windows tek tıkla başlatma betiği
├── .gitignore             # Git yoksayma kuralları
├── README.md              # Kapsamlı dökümantasyon ve API rehberi
├── templates/
│   └── index.html         # Elektrik Camgöbeği & Obsidiyen Temalı Web Arayüzü
└── static/
    ├── css/
    │   └── style.css      # Modern Neon Matrix Stilleri & Animasyonlar
    └── js/
        └── main.js        # Canlı kart akışı, ses efektleri, filtreleme ve dil desteği
```

---

## 💻 Yerel Olarak Çalıştırma (Localhost)

### Yöntem 1: `start.bat` ile Tek Tıkla (Windows)
Klasördeki `start.bat` dosyasına çift tıklayın. Gerekli kütüphaneleri otomatik kontrol eder, tarayıcıda `http://localhost:5000` adresini açar ve sunucuyu başlatır.

### Yöntem 2: Terminal / Komut Satırı ile
```bash
pip install -r requirements.txt
python app.py
```

Tarayıcınızdan açın:
`http://localhost:5000`

---

## 🚀 Render.com'a Dağıtım (Deploy Rehberi)

1. [Render.com](https://render.com) paneline giriş yapın.
2. **New +** > **Web Service** seçeneğine tıklayın.
3. GitHub reponuzu bağlayın.
4. Ayarları yapın:
   - **Name:** `kryx-nmi-chkr`
   - **Language / Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers 4 --threads 8 --timeout 120`
5. **Create Web Service** butonuna tıklayın.

*(Projedeki dahili Keep-Alive sistemi, Render üzerindeki canlı URL'yi otomatik yakalayarak servisin 7/24 uyanık kalmasını sağlar).*

---

## 🔌 REST API Kullanımı

Bu servis sadece web tarayıcı arayüzü olarak değil, Telegram botları veya harici betikler için doğrudan REST API olarak da çalışır.

### 1. Kart Kontrolü
- **URL:** `/api/check`
- **Method:** `GET` veya `POST` (JSON ya da Form Data)

#### Parametreler:
| Parametre | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `card` (veya `rave`) | string | Evet | Kart formatı: `KART|AY|YIL|CVV` (Örn: `4111111111111111\|12\|28\|123`) |
| `proxy` | string | Hayır | HTTP proxy adresi (`http://user:pass@host:port`) |
| `client_id` | string | Hayır | Canlı aktif kullanıcı sayımı için istemci ID |

#### Örnek JSON Yanıtı (Başarılı / Charged):
```json
{
  "status": "CHARGED",
  "message": "Donation succeeded | Confirmation: DP-948271",
  "card": "4111111111111111|12|28|123",
  "decline_code": null,
  "amount": "1.00 USD",
  "raw_bin": "411111 USA JPMORGAN CHASE BANK VISA CREDIT",
  "bin_data": {
    "bin": "411111",
    "brand": "VISA",
    "type": "CREDIT",
    "card_level": "PLATINUM",
    "issuer_name": "JPMORGAN CHASE BANK",
    "country_alpha3": "USA"
  },
  "token_id": "92Ka...x78",
  "gateway": "NMI (DonorPerfect - BookSpring $1)",
  "time_taken": "2.14s",
  "developer": "@sweartx",
  "channel": "t.me/KryxCheck"
}
```

#### Örnek JSON Yanıtı (Red / Declined):
```json
{
  "status": "DECLINED",
  "message": "CVV_FAILURE - CVV / Security Code Mismatch",
  "card": "4111111111111111|12|28|123",
  "decline_code": "CVV_FAILURE",
  "amount": "1.00 USD",
  "raw_bin": "411111 USA JPMORGAN CHASE BANK VISA CREDIT",
  "bin_data": { ... },
  "token_id": "92Ka...x78",
  "gateway": "NMI (DonorPerfect - BookSpring $1)",
  "time_taken": "1.89s",
  "developer": "@sweartx",
  "channel": "t.me/KryxCheck"
}
```

### 2. Canlı Sağlık ve Telemetri Durumu
- **URL:** `/health` veya `/api/stats`
- **Method:** `GET`
- **Açıklama:** Sunucu çalışma süresi (uptime), eşzamanlı aktif kullanıcı sayısı, NMI gateway bağlantı ve token durumu.
