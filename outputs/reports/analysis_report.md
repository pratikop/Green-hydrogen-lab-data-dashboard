# Green Hydrogen Lab Data Analysis Dashboard

## Objective
Analyze public megawatt-scale hydrogen electrolysis time-series data and build a reproducible workflow for cleaning, KPI calculation, visualization, and R&D-style reporting.

## Dataset
Public Reference Data for Megawatt-Scale Hydrogen Electrolysis, combined wind experiments.
Source: https://data.nlr.gov/submissions/305

## Key KPIs
| Metric | Value |
|---|---:|
| rows | 61285 |
| experiments | 13 |
| avg_wind_power_kw | 668.42 |
| avg_psu_power_kw | 668.34 |
| total_energy_kwh_est | 11377.58 |
| total_h2_kg_est | 215.7727 |
| avg_specific_energy_kwh_per_kg | 115.77 |
| median_specific_energy_kwh_per_kg | 51.66 |
| avg_temperature_c | 57.23 |
| median_power_tracking_ratio | 1.017 |

## Figures
- `outputs/figures/01_power_response.png`
- `outputs/figures/02_specific_energy_distribution.png`
- `outputs/figures/03_cumulative_h2_production.png`
- `outputs/figures/04_temperature_trends.png`
- `outputs/figures/05_experiment_efficiency_comparison.png`

## Note
Estimated hydrogen mass is calculated from available power and specific-energy columns and should be treated as an analytical estimate, not a certified lab measurement.
