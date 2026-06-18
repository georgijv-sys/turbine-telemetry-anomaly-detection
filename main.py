

"""AeroGrid turbine telemetry — anomaly detection (IEUK 2026 Engineering, Artefact 1).

Reads a sample of offshore wind-turbine IoT telemetry and reports which turbines
require urgent maintenance. A turbine is flagged if EITHER rule is breached (OR):

    * mean temperature  > 85.0 C     -- sustained overheating  (an average)
    * peak vibration    > 15.0 mm/s  -- a single dangerous spike (a maximum)

This is a batch job over a fixed CSV sample; the continuous, real-time version
is described in the system architecture diagram (Artefact 3).

Usage:
    python main.py        # telemetry_data.csv must sit in the same folder
"""
import pandas as pd


TEMP_LIMIT = 85.0
VIB_LIMIT = 15.0
DATA_FILE = "telemetry_data.csv"

def compute_metrics(df):
    """Aggregate readings to one row per turbine: mean temperature and max vibration."""
    metrics = df.groupby('turbine_id').agg(
        mean_temp=('temperature_c', 'mean'),
        max_vib=('vibration_mm_s', 'max'),
    )
    return metrics

def find_anomalies(metrics):
    """Return the metrics rows for turbines breaching either anomaly rule."""
    anomalies = ((metrics['mean_temp'] > TEMP_LIMIT) | (metrics['max_vib'] > VIB_LIMIT))
    return metrics[anomalies]

def report(anomalies):
    """Print each failing turbine and the specific rule(s) it breached, with values."""
    print("=============TURBINES IN NEED OF ATTENTION============")
    for turbine_id in anomalies.index:
        print(turbine_id)
    print("=====================SPECIFICATIONS====================")

    for turbine_id in anomalies.index:
        if anomalies.loc[turbine_id, 'mean_temp'] > TEMP_LIMIT:
            print(
            f"{turbine_id}: Mean temperature "
            f"({anomalies.loc[turbine_id, 'mean_temp']:.2f}°C) exceeds {TEMP_LIMIT}°C"
        )
        if anomalies.loc[turbine_id, 'max_vib'] > VIB_LIMIT:
            print(
                f"{turbine_id}: Maximum vibration "
                f"({anomalies.loc[turbine_id, 'max_vib']:.2f} mm/s) exceeds {VIB_LIMIT} mm/s"
            )

def main():
    """Load the telemetry CSV, detect anomalies, and print the report."""
    df = pd.read_csv(DATA_FILE)
    metrics = compute_metrics(df)
    report(find_anomalies(metrics))
    
if __name__ == "__main__":
    main()
