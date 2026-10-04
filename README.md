# SuryaSense: Solar Flare Nowcasting & Forecasting with Aditya-L1

> [!WARNING]
> **Academic Project Notice:** SuryaSense is a university semester mini-project developed for ISRO Problem Statement 15. It is **not** an operational space-weather warning system. Outputs should not be relied upon for critical infrastructure or aviation decisions.

---

## Overview

SuryaSense provides an automated pipeline for:
1. **Nowcasting**: Detecting and classifying solar flares in real-time from Aditya-L1 **SoLEXS** (soft X-ray) and **HEL1OS** (hard X-ray) Level-1 data, validated against GOES-19 XRS.
2. **Master Flare Catalogue**: Merged multi-band flare detection database (`soft_only`, `hard_only`, `both`).
3. **Forecasting**: Predicting flare occurrence probability within the next $N=30$ minutes with quantifiable lead time.
4. **Interactive Dashboard**: Visualizing multi-instrument light curves, active flare nowcasts, and forecast watch alerts with offline replay capabilities.

---

## Data Sources

- **Aditya-L1 SoLEXS & HEL1OS**: Level-1 data provided by ISRO via the [ISSDC PRADAN portal](https://pradan.issdc.gov.in/).
- **GOES-19 XRS L2**: 1-minute flux (`avg1m`) and flare summary (`flsum`) provided by NOAA NCEI (used strictly as ground truth for labels and evaluation).

---

## Repository Structure

```text
├── config/              # Pipeline configuration and date windows
├── data/
│   ├── raw/             # Read-only raw data (SoLEXS, HEL1OS, GOES)
│   ├── extracted/       # Extracted light curves only
│   ├── interim/         # Quality control and intermediate grids
│   ├── processed/       # Resampled arrays and feature tables
│   ├── catalog/         # Generated master flare catalogue
│   ├── data_manifest.csv
│   └── coverage_daily.csv
├── docs/                # Architecture, BRD, PRD, Data Dictionary, ADRs
├── scripts/             # Manifest generator, zip inspection tool, downloaders
├── src/solarflare/      # Core package (io, preprocess, nowcast, features, forecast, alerts)
├── tests/               # Unit, synthetic, and leakage tests
├── pyproject.toml       # Dependencies, ruff, mypy, and pytest configs
└── Makefile             # Developer commands
```

---

## Quickstart

### 1. Setup Environment
```bash
python -m venv .venv
# Activate virtual environment:
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate

pip install -e ".[dev]"
```

### 2. Verify Data Manifest & Coverage
```bash
python scripts/make_manifest.py
```

### 3. Run Quality Checks
```bash
make lint
make test
```
