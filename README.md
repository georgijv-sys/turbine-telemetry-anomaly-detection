# AeroGrid Turbine Telemetry — Anomaly Detection

**IEUK 2026 Engineering Sector Skills Project — Artefact 1 (Data Processing)**

A runnable Python script that scans a sample of offshore wind-turbine IoT telemetry and reports which turbines require urgent maintenance.

## What it does

`main.py` reads `telemetry_data(in).csv`, groups every reading by turbine, and applies two anomaly rules. A turbine is flagged if **either** rule is breached (logical **OR**):

| Rule | Condition (per turbine) | Why this metric |
|------|-------------------------|-----------------|
| **High temperature** | **mean** of `temperature_c` &gt; **85.0 °C** | sustained overheating — an average, not a single blip |
| **Vibration spike** | **max** of `vibration_mm_s` &gt; **15.0 mm/s** | a single dangerous spike is enough to flag |

For each failing turbine the script prints the Turbine ID and the specific rule(s) it broke, with the offending value as evidence.

## Requirements

- Python 3.10 or newer
- pandas (pinned in `requirements.txt`; tested on 3.0.3)

## Setup

```bash
# 1. Create an isolated environment
python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows (PowerShell)

# 3. Install dependencies
pip install -r requirements.txt
```

## Running

The script reads the CSV by **relative path**, so `telemetry_data(in).csv` must sit in the **same folder** as `main.py`. Then:

```bash
python main.py
```

## Expected output

```
Turbine in need of attention:
Turbine:  T-04
Turbine:  T-07
T-04: Mean temperature (90.58°C) exceeds 85°C
T-07: Maximum vibration (25.00 mm/s) exceeds 15 mm/s
```

**T-04** is flagged for a mean temperature of 90.58 °C (rule 1); **T-07** for a peak vibration of 25.0 mm/s (rule 2). The other eight turbines are within safe limits.

## Input data

`telemetry_data(in).csv` — 5,000 readings across 10 turbines (`T-01`…`T-10`).

| Column | Type | Notes |
|--------|------|-------|
| `timestamp` | text | reading time |
| `turbine_id` | text | `T-01` … `T-10` |
| `temperature_c` | float | °C |
| `vibration_mm_s` | float | mm/s |
| `rpm` | float | not used by the anomaly rules |
