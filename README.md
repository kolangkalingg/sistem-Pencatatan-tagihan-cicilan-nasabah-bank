# Billing System Project

## Deskripsi
Aplikasi berbasis web sederhana untuk mencatat dan melacak pembayaran cicilan. Dibangun menggunakan Python (Flask), SQLite, dan Excel (openpyxl).

---

## Langkah Instalasi

### 1. **Clone Repository**
Clone repository proyek ini dari GitHub ke komputer lokal Anda.
```bash
git clone <repository-url>
cd <nama-folder-proyek>
```

### 2. **Install Python**
Pastikan Anda telah menginstal Python 3.7 atau yang lebih baru. Jika belum, download dan install Python dari [python.org](https://www.python.org/).

### 3. **Setup Virtual Environment (Opsional)**
Buat virtual environment untuk menjaga agar dependensi tetap terisolasi.
```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
```

### 4. **Install Dependensi**
Instal semua dependensi yang diperlukan dengan menggunakan `requirements.txt`.

Buat file `requirements.txt` (jika belum ada) dengan isi berikut:
```plaintext
Flask==2.3.3
openpyxl==3.1.2
Werkzeug==2.3.7
```

Kemudian jalankan perintah berikut:
```bash
pip install -r requirements.txt
```

### 5. **Inisialisasi Basis Data**
Proyek ini menggunakan SQLite untuk menyimpan data pengguna dan obrolan. File database akan dibuat secara otomatis oleh fungsi `init_sqlite_db` saat Anda menjalankan proyek.

### 6. **File Excel**
Aplikasi membutuhkan file `data_tagihan.xlsx`. Jika file ini belum ada, fungsi `initialize_excel` akan otomatis membuatnya dengan sheet yang diperlukan. Pastikan direktori proyek memiliki izin untuk membuat atau menulis file.

### 7. **Set Kunci Rahasia**
Ubah atau atur kunci rahasia untuk aplikasi Flask di file Python utama:
```python
app.secret_key = "your_new_secret_key"
```

### 8. **Jalankan Aplikasi**
Jalankan aplikasi Flask dengan perintah berikut:
```bash
python nama_file_anda.py
```

### 9. **Akses Aplikasi**
Buka browser dan akses aplikasi Anda melalui URL:
```
http://127.0.0.1:5000
```

---

## Fitur
1. **Login dan Registrasi**
   - Pengguna dapat mendaftar dan login.
2. **Form Input Cicilan**
   - Tambahkan data cicilan dengan rincian seperti nominal, vendor, durasi, dan status pembayaran.
3. **Laporan**
   - Lihat data cicilan yang belum dibayar dan sudah dibayar.
4. **Chat**
   - Fitur obrolan sederhana untuk diskusi antar pengguna.

---

## Dependensi Utama
- Python 3.7+
- Flask 2.3.3
- openpyxl 3.1.2
- Werkzeug 2.3.7

---

## Struktur Proyek
```
project-folder/
|—— app.py                # File utama aplikasi Flask
|—— templates/           # Folder untuk file HTML
|—— static/              # Folder untuk file CSS, JS, dan aset statis lainnya
|—— data_tagihan.xlsx     # File Excel untuk menyimpan data cicilan
|—— requirements.txt    # Daftar dependensi Python
|—— README.md           # Dokumentasi proyek
```

---

## Lisensi
Tentukan lisensi untuk proyek Anda (misalnya MIT, GPL, atau lisensi lainnya).
