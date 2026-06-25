"""app.py

Dashboard interaktif visualisasi data spasio-temporal:
Peta Folium, slider tahun, dan grafik tren Plotly.
Jalankan dengan perintah: streamlit run app.py
"""

import pandas as pd
import folium
from folium.plugins import HeatMap
import streamlit as st
from streamlit_folium import st_folium
import plotly.express as px
import branca.colormap as cm
import os

st.set_page_config(page_title="Volume Ekspor Indonesia 2000-2024", layout="wide")

DATA_CLEAN = "data_ekspor_clean.csv"
DATA_FORECAST = "data_forecast.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_CLEAN)
    df_forecast = None
    if os.path.exists(DATA_FORECAST):
        df_forecast = pd.read_csv(DATA_FORECAST)
    return df, df_forecast


df, df_forecast = load_data()
has_forecast = df_forecast is not None

# Sidebar: Kontrol temporal dan filter
st.sidebar.title("Kontrol Visualisasi")

mode = "Historis"
if has_forecast:
    mode = st.sidebar.radio("Mode data", ["Historis", "Historis + Proyeksi ML"])

if mode == "Historis + Proyeksi ML":
    data_aktif = df_forecast.copy()
    tahun_min, tahun_max = int(data_aktif["tahun"].min()), int(data_aktif["tahun"].max())
else:
    data_aktif = df.copy()
    data_aktif["tipe"] = "historis"
    tahun_min, tahun_max = int(df["tahun"].min()), int(df["tahun"].max())

tahun_terpilih = st.sidebar.slider(
    "Pilih Tahun", min_value=tahun_min, max_value=tahun_max,
    value=tahun_max, step=1,
)

region_list = ["Semua"] + sorted(df["region"].unique().tolist())
region_terpilih = st.sidebar.selectbox("Filter Wilayah/Region", region_list)

mode_peta = st.sidebar.radio("Tipe Layer Peta", ["Circle Marker (proporsional)", "Heatmap"])

st.sidebar.markdown("---")
st.sidebar.caption(
    "Sumber data: Badan Pusat Statistik (BPS) — Volume Ekspor Menurut "
    "Negara/Wilayah/Entitas Tertentu Tujuan Utama, 2000-2024."
)

# Filter data sesuai pilihan parameter
data_tahun = data_aktif[data_aktif["tahun"] == tahun_terpilih].copy()
if region_terpilih != "Semua":
    data_tahun = data_tahun[data_tahun["region"] == region_terpilih]

# Header utama aplikasi
st.title("Visualisasi Spasio-Temporal Volume Ekspor Indonesia (2000-2024)")

keterangan_tahun = "data historis"
if has_forecast and mode == "Historis + Proyeksi ML" and len(data_tahun) > 0:
    tipe_unik = data_tahun["tipe"].unique()
    if "prediksi" in tipe_unik:
        keterangan_tahun = "hasil proyeksi model Machine Learning"

st.markdown(
    f"Menampilkan data tahun **{tahun_terpilih}** ({keterangan_tahun}) "
    f"untuk **{len(data_tahun)} negara tujuan ekspor**."
)

col1, col2 = st.columns([3, 2])

# Kolom 1: Peta Interaktif
with col1:
    st.subheader("Peta Interaktif")

    m = folium.Map(location=[10, 60], zoom_start=2, tiles="CartoDB positron")

    if len(data_tahun) > 0:
        vmin, vmax = data_tahun["volume_ribu_ton"].min(), data_tahun["volume_ribu_ton"].max()
        colormap = cm.LinearColormap(
            colors=["#fee08b", "#fc8d59", "#d73027"],
            vmin=vmin, vmax=max(vmax, vmin + 1),
        )
        colormap.caption = "Volume Ekspor (ribu ton)"

        if mode_peta == "Heatmap":
            heat_data = [
                [row["lat"], row["lon"], row["volume_ribu_ton"]]
                for _, row in data_tahun.iterrows() if row["volume_ribu_ton"] > 0
            ]
            HeatMap(heat_data, radius=25, blur=18).add_to(m)
        else:
            for _, row in data_tahun.iterrows():
                volume = row["volume_ribu_ton"]
                radius = 4 + (volume / max(vmax, 1)) * 26
                tipe = row.get("tipe", "historis")
                warna = colormap(volume)
                garis = "#1f1f1f" if tipe == "historis" else "#0066ff"

                popup_html = f"""
                <b>{row['negara']}</b><br>
                Region: {row['region']}<br>
                Tahun: {row['tahun']} ({tipe})<br>
                Volume Ekspor: {volume:,.1f} ribu ton
                """
                folium.CircleMarker(
                    location=[row["lat"], row["lon"]],
                    radius=radius,
                    color=garis,
                    weight=2 if tipe == "prediksi" else 1,
                    fill=True,
                    fill_color=warna,
                    fill_opacity=0.75,
                    dash_array="5,5" if tipe == "prediksi" else None,
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{row['negara']}: {volume:,.1f} ribu ton",
                ).add_to(m)

        colormap.add_to(m)

    st_folium(m, width=None, height=520, returned_objects=[])

    st.caption(
        "Lingkaran solid = data historis. Garis putus-putus biru = hasil "
        "proyeksi model Machine Learning (jika mode proyeksi dipilih)."
    )

# Kolom 2: Grafik Tren dan Ranking
with col2:
    st.subheader("Tren & Perbandingan")

    tab1, tab2 = st.tabs(["Tren Negara", "Ranking Tahun Ini"])

    with tab1:
        default_negara = ["Tiongkok", "Amerika Serikat", "Jepang"]
        default_negara = [n for n in default_negara if n in df["negara"].unique()]
        negara_terpilih = st.multiselect(
            "Pilih negara untuk dibandingkan", sorted(df["negara"].unique()),
            default=default_negara,
        )
        if negara_terpilih:
            df_tren = data_aktif[data_aktif["negara"].isin(negara_terpilih)]
            fig = px.line(
                df_tren, x="tahun", y="volume_ribu_ton", color="negara",
                line_dash="tipe" if "tipe" in df_tren.columns else None,
                markers=True,
                labels={"volume_ribu_ton": "Volume (ribu ton)", "tahun": "Tahun"},
            )
            fig.add_vline(x=tahun_terpilih, line_dash="dot", line_color="gray")
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Pilih minimal satu negara untuk menampilkan grafik tren.")

    with tab2:
        top_n = data_tahun.sort_values("volume_ribu_ton", ascending=False).head(10)
        fig_bar = px.bar(
            top_n, x="volume_ribu_ton", y="negara", orientation="h",
            color="region",
            labels={"volume_ribu_ton": "Volume (ribu ton)", "negara": ""},
            title=f"10 Negara Tujuan Ekspor Terbesar — {tahun_terpilih}",
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_bar, width='stretch')

# Tabel Data Mentah
with st.expander("Lihat tabel data mentah tahun terpilih"):
    st.dataframe(
        data_tahun[["negara", "region", "tahun", "volume_ribu_ton"]]
        .sort_values("volume_ribu_ton", ascending=False)
        .reset_index(drop=True)
    )

if has_forecast:
    with st.expander("Evaluasi Model Machine Learning (Forecasting)"):
        if os.path.exists("eval_metrics.csv"):
            df_metrics = pd.read_csv("eval_metrics.csv")
            st.markdown(
                "Model Random Forest Regressor dilatih per negara menggunakan "
                "fitur lag (volume 1-3 tahun sebelumnya), dievaluasi pada data uji "
                "tahun 2019-2024, lalu diproyeksikan untuk 2025-2027."
            )
            st.dataframe(df_metrics)
            st.caption("RMSE dan MAE dalam satuan ribu ton.")