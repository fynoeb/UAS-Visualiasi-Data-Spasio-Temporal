# Visualisasi Spasio-Temporal Volume Ekspor Indonesia (2000-2024)

Proyek akhir mata kuliah Visualisasi Data Spasio-Temporal. Aplikasi dashboard
interaktif berbasis peta untuk mengeksplorasi tren volume ekspor Indonesia ke
30 negara tujuan utama selama periode 2000-2024, dengan opsi proyeksi 3 tahun
ke depan menggunakan model Random Forest Regressor (komponen bonus ML).

## Sumber Data
Badan Pusat Statistik (BPS) — *Volume Ekspor Menurut Negara/Wilayah/Entitas
Tertentu Tujuan Utama (Berat Bersih: Ribu Ton), 2000-2024*.
https://www.bps.go.id/id/statistics-table/1/MTAwOSMx/

## Struktur Folder
- `Volume_Ekspor_..._2000-2024.csv` — data mentah BPS
- `preprocessing.py` — pembersihan & transformasi data wide → long + koordinat
- `ml_forecasting.py` — (opsional) model Random Forest untuk proyeksi 2025-2027
- `app.py` — dashboard Streamlit + Folium
- `data_ekspor_clean.csv` — output preprocessing
- `data_forecast.csv`, `eval_metrics.csv` — output ML (opsional)

## Instalasi
```bash
pip install -r requirements.txt
```

## Cara Menjalankan
1. Pastikan file CSV mentah BPS ada di folder yang sama.
2. Jalankan preprocessing (wajib):
```bash
   python preprocessing.py
```
3. (Opsional, bonus ML) Jalankan forecasting:
```bash
   python ml_forecasting.py
```
4. Jalankan aplikasi:
```bash
   streamlit run app.py
```
5. Buka browser ke `http://localhost:8501`

## Fitur
- Slider tahun (kontrol temporal) 2000-2024 (+ 2025-2027 jika mode proyeksi aktif)
- Peta interaktif (circle marker proporsional atau heatmap) dengan popup & tooltip
- Legenda warna (skala volume ekspor)
- Grafik tren multi-negara dan ranking 10 negara teratas per tahun
- Filter berdasarkan region
- Proyeksi ML 3 tahun ke depan dengan evaluasi RMSE/MAE per negara

## Catatan Metodologis
Hanya negara dengan data individual (bukan baris agregat seperti "ASEAN",
"Uni Eropa", "Jumlah") yang dipetakan, karena baris agregat tidak
merepresentasikan satu titik koordinat geografis tunggal. Nilai "-" pada data
asli BPS diinterpretasikan sebagai tidak ada aktivitas ekspor tercatat dan
diisi 0.