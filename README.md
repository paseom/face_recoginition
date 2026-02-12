# Face Access System

Sistem akses pintu dan crowd recognition berbasis wajah menggunakan InsightFace (RetinaFace + ArcFace), OpenCV, dan MySQL.

## 1) Deskripsi Program

Program ini punya 3 fungsi utama:

- **Pendaftaran Pegawai (Enrollment)**: menyimpan data pegawai (`nama`, `nip`) dan embedding wajah ke database.
- **Face Recognition Akses Pintu**: verifikasi wajah real-time dari webcam untuk menentukan `GRANTED` / `DENIED`.
- **Crowd Recognition (Upload Video/Gambar/Webcam)**: deteksi banyak wajah dalam satu frame, lakukan filtering kualitas, lalu cocokkan ke database dan simpan ke `crowd_log`.

Pipeline inti:

1. Deteksi wajah (RetinaFace via InsightFace)
2. Validasi kualitas wajah (ukuran, blur, pose, landmark)
3. Ekstraksi embedding (ArcFace)
4. Pencocokan embedding (cosine similarity)
5. Logging hasil ke database

---

## 2) Kegunaan

- Kontrol akses pintu berbasis identitas wajah pegawai
- Monitoring kerumunan untuk melihat siapa saja yang terdeteksi
- Pencatatan histori akses dan crowd detection sebagai audit trail

---

## 3) Struktur Program

Root aplikasi utama ada di folder `face_access/`.

```text
face_access/
├─ app.py                    # UI Streamlit
├─ main.py                   # Orkestrasi komponen sistem
├─ requirements.txt          # Dependensi Python
├─ config/
│  └─ settings.py            # Konfigurasi threshold, kamera, DB
├─ core/
│  ├─ camera.py              # Handler webcam
│  ├─ detector.py            # Face detector (InsightFace)
│  ├─ embedding.py           # Ekstraksi embedding
│  ├─ matcher.py             # Pencocokan embedding
│  ├─ quality.py             # Validasi kualitas wajah
│  └─ liveness.py            # Placeholder liveness
├─ db/
│  ├─ database.py            # Koneksi MySQL
│  ├─ pegawai_repo.py        # CRUD tabel pegawai
│  ├─ embedding_repo.py      # Simpan/muat embedding
│  └─ log_repo.py            # access_log + crowd_log
├─ enrollment/
│  └─ enroll.py              # Alur pendaftaran pegawai
├─ recognition/
│  ├─ recognize.py           # Recognition akses pintu
│  └─ crowd_recognize.py     # Recognition dari crowd
└─ utils/
   ├─ logger.py              # Logging sederhana
   ├─ math_utils.py          # Cosine similarity utilities
   └─ camera_detector.py     # Auto-detect kamera
```

---

## 4) Struktur Database

Database: `pegawai_bpk`  
Referensi schema: file `database SQL`

### Tabel `pegawai`
- `id_pegawai` 
- `nama` 
- `nip` 
- `created_at` 

### Tabel `face_embedding`
- `embedding_id` 
- `id_pegawai` 
- `embedding_vector`
- `created_at` 

### Tabel `access_log`
- `log_id` 
- `id_pegawai` 
- `status` 
- `reason` 
- `created_at`

### Tabel `crowd_log`
- `id_log`
- `id_pegawai` 
- `nama`
- `nip` 
- `source_type`
- `created_at`

---

## 5) Spesifikasi Komputasi
- CPU: Intel Core i7 Gen 10+ / Ryzen 7 3700X+
- RAM: 16 GB
- Storage: SSD NVMe
- Kamera: 1080p webcam
- GPU: NVIDIA GTX 1660 / RTX 2060

### Untuk crowd video
- CPU: 8 core+ modern
- RAM: 32 GB
- GPU: NVIDIA RTX 3060 12GB atau lebih baik
- Disarankan optimasi resolusi input dan sampling frame

---

## 6) Dependensi Utama

- `opencv-contrib-python`
- `numpy`
- `insightface`
- `onnxruntime`
- `mysql-connector-python`
