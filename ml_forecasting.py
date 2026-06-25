"""ml_forecasting.py

Membangun model Random Forest Regressor per negara menggunakan fitur lag
untuk memproyeksikan volume ekspor, serta mengevaluasi performa model
dengan metrik RMSE dan MAE pada data uji.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error

INPUT_FILE = "data_ekspor_clean.csv"
FORECAST_OUTPUT = "data_forecast.csv"
METRICS_OUTPUT = "eval_metrics.csv"

N_LAGS = 3
TEST_YEARS_FROM = 2019
FORECAST_YEARS = [2025, 2026, 2027]


def make_lag_features(series_df, n_lags=N_LAGS):
    """Membuat fitur lag dari DataFrame yang telah diurutkan berdasarkan tahun."""
    df = series_df.copy().reset_index(drop=True)
    for lag in range(1, n_lags + 1):
        df[f"lag{lag}"] = df["volume_ribu_ton"].shift(lag)
    return df


def forecast_country(df_country):
    df_country = df_country.sort_values("tahun").reset_index(drop=True)
    df_lagged = make_lag_features(df_country)
    df_model = df_lagged.dropna(subset=[f"lag{i}" for i in range(1, N_LAGS + 1)])

    feature_cols = [f"lag{i}" for i in range(1, N_LAGS + 1)]
    train = df_model[df_model["tahun"] < TEST_YEARS_FROM]
    test = df_model[df_model["tahun"] >= TEST_YEARS_FROM]

    rmse, mae, n_test = np.nan, np.nan, 0
    if len(train) >= 5 and len(test) >= 1:
        model_eval = RandomForestRegressor(n_estimators=200, random_state=42)
        model_eval.fit(train[feature_cols], train["volume_ribu_ton"])
        pred_test = model_eval.predict(test[feature_cols])
        rmse = float(np.sqrt(mean_squared_error(test["volume_ribu_ton"], pred_test)))
        mae = float(mean_absolute_error(test["volume_ribu_ton"], pred_test))
        n_test = len(test)

    # Melatih ulang model menggunakan seluruh data historis untuk memproyeksikan ke depan
    model_full = RandomForestRegressor(n_estimators=200, random_state=42)
    model_full.fit(df_model[feature_cols], df_model["volume_ribu_ton"])

    last_values = list(df_country["volume_ribu_ton"].tail(N_LAGS))
    forecasts = []
    for year in FORECAST_YEARS:
        lag_input = last_values[-N_LAGS:][::-1]
        lag_df = pd.DataFrame([lag_input], columns=feature_cols)
        pred = model_full.predict(lag_df)[0]
        pred = max(pred, 0)
        forecasts.append((year, pred))
        last_values.append(pred)

    return forecasts, rmse, mae, n_test


def main():
    df = pd.read_csv(INPUT_FILE)
    all_rows = []
    metrics_rows = []

    for negara, group in df.groupby("negara"):
        region, lat, lon = group[["region", "lat", "lon"]].iloc[0]

        # Menyertakan data historis
        for _, r in group.iterrows():
            all_rows.append({
                "negara": negara, "region": region, "lat": lat, "lon": lon,
                "tahun": int(r["tahun"]), "volume_ribu_ton": r["volume_ribu_ton"],
                "tipe": "historis",
            })

        forecasts, rmse, mae, n_test = forecast_country(group)
        for year, pred in forecasts:
            all_rows.append({
                "negara": negara, "region": region, "lat": lat, "lon": lon,
                "tahun": year, "volume_ribu_ton": round(pred, 2),
                "tipe": "prediksi",
            })

        metrics_rows.append({
            "negara": negara, "rmse": round(rmse, 2) if not np.isnan(rmse) else None,
            "mae": round(mae, 2) if not np.isnan(mae) else None, "n_test": n_test,
        })

    df_forecast = pd.DataFrame(all_rows)
    df_metrics = pd.DataFrame(metrics_rows).sort_values("rmse", na_position="last")

    df_forecast.to_csv(FORECAST_OUTPUT, index=False)
    df_metrics.to_csv(METRICS_OUTPUT, index=False)

    valid_metrics = df_metrics.dropna(subset=["rmse"])
    print(f"Negara diproses  : {df_metrics.shape[0]}")
    print(f"Rata-rata RMSE   : {valid_metrics['rmse'].mean():.2f} (ribu ton)")
    print(f"Rata-rata MAE    : {valid_metrics['mae'].mean():.2f} (ribu ton)")
    print(f"Disimpan ke      : {FORECAST_OUTPUT}, {METRICS_OUTPUT}")
    print(df_metrics.head(8))


if __name__ == "__main__":
    main()