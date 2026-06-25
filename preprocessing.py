"""preprocessing.py

Pra-pemrosesan data ekspor BPS dari format wide menjadi format long/tidy
serta penambahan koordinat geografis negara tujuan ekspor.
"""

import pandas as pd
import numpy as np

RAW_FILE = "Volume Ekspor Menurut Negara_Wilayah_Entitas tertentu Tujuan Utama (Berat bersih_ ribu ton), 2000-2024.csv"
OUTPUT_FILE = "data_ekspor_clean.csv"

# Daftar negara tujuan ekspor beserta region dan koordinat centroid.
COUNTRY_COORDS = {
    "Thailand":           ("Asia Tenggara", 15.87, 100.99),
    "Singapura":          ("Asia Tenggara", 1.35, 103.82),
    "Filipina":           ("Asia Tenggara", 12.88, 121.77),
    "Malaysia":           ("Asia Tenggara", 4.21, 101.98),
    "Myanmar":            ("Asia Tenggara", 21.91, 95.96),
    "Kamboja":            ("Asia Tenggara", 12.57, 104.99),
    "Brunei Darussalam":  ("Asia Tenggara", 4.54, 114.73),
    "Laos":               ("Asia Tenggara", 19.86, 102.50),
    "Vietnam":            ("Asia Tenggara", 14.06, 108.28),
    "Jepang":             ("Asia Timur", 36.20, 138.25),
    "Hongkong":           ("Asia Timur", 22.32, 114.17),
    "Korea Selatan":      ("Asia Timur", 35.91, 127.77),
    "Taiwan":             ("Asia Timur", 23.70, 120.96),
    "Tiongkok":           ("Asia Timur", 35.86, 104.20),
    "Australia":          ("Australia & Oceania", -25.27, 133.78),
    "Selandia Baru":      ("Australia & Oceania", -40.90, 174.89),
    "Amerika Serikat":    ("Amerika", 37.09, -95.71),
    "Kanada":             ("Amerika", 56.13, -106.35),
    "Meksiko":            ("Amerika", 23.63, -102.55),
    "Belanda":            ("Eropa", 52.13, 5.29),
    "Perancis":           ("Eropa", 46.23, 2.21),
    "Jerman":             ("Eropa", 51.17, 10.45),
    "Belgia":             ("Eropa", 50.50, 4.47),
    "Denmark":            ("Eropa", 56.26, 9.50),
    "Swedia":             ("Eropa", 60.13, 18.64),
    "Finlandia":          ("Eropa", 61.92, 25.75),
    "Italia":             ("Eropa", 41.87, 12.57),
    "Spanyol":            ("Eropa", 40.46, -3.75),
    "Yunani":             ("Eropa", 39.07, 21.82),
    "Polandia":           ("Eropa", 51.92, 19.15),
}


def clean_numeric(value):
    """Membersihkan format angka dari data BPS dan mengubah nilai kosong menjadi NaN."""
    if pd.isna(value):
        return np.nan
    value = str(value).strip()
    if value in ("-", "", "..", "...", "n/a", "NA"):
        return np.nan
    value = value.replace(",", "")
    try:
        return float(value)
    except ValueError:
        return np.nan


def main():
    # Membaca data mentah dan menyesuaikan nama kolom
    df_raw = pd.read_csv(RAW_FILE, header=2, encoding="utf-8-sig")
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    df_raw = df_raw.rename(columns={df_raw.columns[0]: "negara"})
    df_raw["negara"] = df_raw["negara"].astype(str).str.strip()

    year_cols = [c for c in df_raw.columns if c.isdigit()]

    # Transformasi data dari format wide ke long
    records = []
    for _, row in df_raw.iterrows():
        negara = row["negara"]
        if negara not in COUNTRY_COORDS:
            continue
        region, lat, lon = COUNTRY_COORDS[negara]
        for year in year_cols:
            volume = clean_numeric(row[year])
            records.append({
                "negara": negara,
                "region": region,
                "lat": lat,
                "lon": lon,
                "tahun": int(year),
                "volume_ribu_ton": volume,
            })

    df_long = pd.DataFrame(records)

    # Penanganan missing values dengan mengisi nilai 0
    n_missing = df_long["volume_ribu_ton"].isna().sum()
    df_long["volume_ribu_ton"] = df_long["volume_ribu_ton"].fillna(0)

    # Menghapus data duplikat
    df_long = df_long.drop_duplicates(subset=["negara", "tahun"])

    # Mengurutkan data dan menghitung persentase pertumbuhan tahunan
    df_long = df_long.sort_values(["negara", "tahun"]).reset_index(drop=True)
    df_long["pertumbuhan_persen"] = (
        df_long.groupby("negara")["volume_ribu_ton"].pct_change() * 100
    ).round(2)

    df_long.to_csv(OUTPUT_FILE, index=False)

    # Menampilkan ringkasan hasil pemrosesan data
    print(f"Negara terpetakan : {df_long['negara'].nunique()}")
    print(f"Rentang tahun     : {df_long['tahun'].min()}-{df_long['tahun'].max()}")
    print(f"Total baris       : {len(df_long)}")
    print(f"Nilai '-' diisi 0 : {n_missing}")
    print(f"Disimpan ke       : {OUTPUT_FILE}")
    print(df_long.head(8))


if __name__ == "__main__":
    main()