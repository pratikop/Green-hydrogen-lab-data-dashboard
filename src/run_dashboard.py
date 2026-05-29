
from __future__ import annotations
import argparse, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

COLUMN_MAP = {
    "timestamp": "Unnamed: 0",
    "wind_power_kw": "Wind Turbine Power (kW)",
    "h2_flow": "IVAL_f_FM011_Flow",
    "specific_energy_kwh_per_kg": "Efficiency (kWh/kg)",
    "psu_voltage_vdc": "Power Supply Average Voltage (Vdc)",
    "psu_power_kw": "H2E_n_PSU_A_Power",
    "psu_current_a": "H2E_f_PSU_A_Current",
    "calc_h2_prod_rate": "H2E_f_Elec_CalcProdRate",
    "lfl_percent": "H2E_f_CG220_LFLPer",
    "pressure_pt307": "H2E_f_PT307_Pressure",
    "temp_te218_c": "H2E_f_TE218_Temp",
    "temp_te219_c": "H2E_f_TE219_Temp",
    "experiment": "Experiment",
}

def ensure_dirs():
    for p in ["data/processed","outputs/figures","outputs/reports"]:
        Path(p).mkdir(parents=True, exist_ok=True)

def read_and_clean(input_file):
    df_raw = pd.read_csv(input_file)
    keep = [v for v in COLUMN_MAP.values() if v in df_raw.columns]
    df = df_raw[keep].copy().rename(columns={v:k for k,v in COLUMN_MAP.items()})
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["sample_index"] = np.arange(len(df))
    for col in df.columns:
        if col not in ["timestamp", "experiment"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "experiment" in df.columns:
        df["experiment"] = df["experiment"].fillna("unknown_experiment")
    for col in ["wind_power_kw","h2_flow","specific_energy_kwh_per_kg","psu_voltage_vdc","psu_power_kw","psu_current_a","calc_h2_prod_rate"]:
        if col in df.columns:
            df.loc[df[col] < 0, col] = np.nan
    df["energy_kwh_est"] = df["psu_power_kw"] / 3600.0
    df["h2_mass_kg_est"] = df["energy_kwh_est"] / df["specific_energy_kwh_per_kg"]
    df["power_tracking_ratio"] = df["psu_power_kw"] / df["wind_power_kw"].replace(0, np.nan)
    return df

def summarize(df):
    return {
        "rows": int(len(df)),
        "experiments": int(df["experiment"].nunique()),
        "avg_wind_power_kw": round(float(df["wind_power_kw"].mean()), 2),
        "avg_psu_power_kw": round(float(df["psu_power_kw"].mean()), 2),
        "total_energy_kwh_est": round(float(df["energy_kwh_est"].sum()), 2),
        "total_h2_kg_est": round(float(df["h2_mass_kg_est"].sum()), 4),
        "avg_specific_energy_kwh_per_kg": round(float(df["specific_energy_kwh_per_kg"].mean()), 2),
        "median_specific_energy_kwh_per_kg": round(float(df["specific_energy_kwh_per_kg"].median()), 2),
        "avg_temperature_c": round(float(df["temp_te218_c"].mean()), 2),
        "median_power_tracking_ratio": round(float(df["power_tracking_ratio"].median()), 3),
    }

def savefig(name, saved):
    out = Path("outputs/figures") / name
    plt.tight_layout()
    plt.savefig(out, dpi=180, bbox_inches="tight")
    plt.close()
    saved.append(str(out))

def make_plots(df):
    saved = []
    plot_df = df.iloc[:min(len(df), 5000)]
    plt.figure(figsize=(11,5))
    plt.plot(plot_df["sample_index"], plot_df["wind_power_kw"], label="Wind turbine power (kW)", linewidth=1)
    plt.plot(plot_df["sample_index"], plot_df["psu_power_kw"], label="Electrolyzer PSU power (kW)", linewidth=1)
    plt.title("Wind Input vs Electrolyzer Power Response")
    plt.xlabel("Sample index"); plt.ylabel("Power (kW)")
    plt.legend(); plt.grid(True, alpha=0.3)
    savefig("01_power_response.png", saved)

    s = df["specific_energy_kwh_per_kg"].dropna()
    s = s[(s > 0) & (s < s.quantile(0.99))]
    plt.figure(figsize=(9,5))
    plt.hist(s, bins=40)
    plt.title("Specific Energy Distribution")
    plt.xlabel("kWh per kg H2"); plt.ylabel("Frequency")
    plt.grid(True, alpha=0.3)
    savefig("02_specific_energy_distribution.png", saved)

    plot_df = df.iloc[:min(len(df), 5000)].copy()
    plot_df["h2_cumulative_kg_est"] = plot_df["h2_mass_kg_est"].cumsum()
    plt.figure(figsize=(11,5))
    plt.plot(plot_df["sample_index"], plot_df["h2_cumulative_kg_est"], linewidth=1.5)
    plt.title("Estimated Cumulative Hydrogen Production")
    plt.xlabel("Sample index"); plt.ylabel("Estimated H2 mass (kg)")
    plt.grid(True, alpha=0.3)
    savefig("03_cumulative_h2_production.png", saved)

    plt.figure(figsize=(11,5))
    plt.plot(plot_df["sample_index"], plot_df["temp_te218_c"], label="TE218 temperature", linewidth=1)
    plt.plot(plot_df["sample_index"], plot_df["temp_te219_c"], label="TE219 temperature", linewidth=1)
    plt.title("Selected Lab Temperature Signals")
    plt.xlabel("Sample index"); plt.ylabel("Temperature (°C)")
    plt.legend(); plt.grid(True, alpha=0.3)
    savefig("04_temperature_trends.png", saved)

    exp = df.groupby("experiment").agg(samples=("experiment","size"), avg_power_kw=("psu_power_kw","mean"), avg_kwh_per_kg=("specific_energy_kwh_per_kg","mean"), total_h2_kg=("h2_mass_kg_est","sum")).reset_index()
    exp = exp.sort_values("samples", ascending=False).head(12)
    plt.figure(figsize=(12,6))
    labels = [str(x).replace(".csv","") for x in exp["experiment"]]
    plt.barh(labels, exp["avg_kwh_per_kg"])
    plt.title("Average Specific Energy by Experiment")
    plt.xlabel("Average kWh per kg H2"); plt.ylabel("Experiment")
    plt.grid(True, axis="x", alpha=0.3)
    savefig("05_experiment_efficiency_comparison.png", saved)
    exp.to_csv("outputs/reports/experiment_summary.csv", index=False)
    return saved

def write_reports(metrics, figures):
    rows = "\n".join([f"| {k} | {v} |" for k, v in metrics.items()])
    figs = "\n".join([f"- `{f}`" for f in figures])
    report = f"""# Green Hydrogen Lab Data Analysis Dashboard

## Objective
Analyze public megawatt-scale hydrogen electrolysis time-series data and build a reproducible workflow for cleaning, KPI calculation, visualization, and R&D-style reporting.

## Dataset
Public Reference Data for Megawatt-Scale Hydrogen Electrolysis, combined wind experiments.
Source: https://data.nlr.gov/submissions/305

## Key KPIs
| Metric | Value |
|---|---:|
{rows}

## Figures
{figs}

## Note
Estimated hydrogen mass is calculated from available power and specific-energy columns and should be treated as an analytical estimate, not a certified lab measurement.
"""
    Path("outputs/reports/analysis_report.md").write_text(report, encoding="utf-8")

    cards = "\n".join([f"<div class='card'><h3>{k}</h3><p>{v}</p></div>" for k,v in metrics.items()])
    images = "\n".join([f"<h2>{Path(f).stem.replace('_',' ').title()}</h2><img src='../figures/{Path(f).name}'>" for f in figures])
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Green Hydrogen Dashboard</title>
<style>body{{font-family:Arial,sans-serif;margin:32px;line-height:1.5}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}.card{{border:1px solid #ddd;border-radius:12px;padding:14px;background:#f8f8f8}}.card h3{{font-size:14px;margin:0 0 8px;color:#555}}.card p{{font-size:22px;font-weight:bold;margin:0}}img{{max-width:100%;border:1px solid #ddd;border-radius:8px;margin-bottom:24px}}</style>
</head><body><h1>Green Hydrogen Lab Data Analysis Dashboard</h1><p>Python dashboard using public megawatt-scale electrolysis data.</p><div class='grid'>{cards}</div>{images}</body></html>"""
    Path("outputs/reports/dashboard.html").write_text(html, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/combined_wind_experiments.csv")
    args = parser.parse_args()
    ensure_dirs()
    df = read_and_clean(args.input)
    df.to_csv("data/processed/cleaned_green_hydrogen_lab_data.csv", index=False)
    metrics = summarize(df)
    Path("outputs/reports/kpis.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    figures = make_plots(df)
    write_reports(metrics, figures)
    print("Dashboard complete")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
