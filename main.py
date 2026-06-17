

import pandas as pd


TEMP_LIMIT = 85.0
VIB_LIMIT = 15.0
DATA_FILE = "telemetry_data(in).csv"

def compute_metrics(df):
    metrics = df.groupby('turbine_id').agg(
        mean_temp=('temperature_c', 'mean'),
        max_vib=('vibration_mm_s', 'max'),
    )
    return metrics

def find_anomalies(metrics):
    anomalies = pd.Series((metrics['mean_temp'] > TEMP_LIMIT) | (metrics['max_vib'] > VIB_LIMIT))
    return metrics[anomalies]

def report(anomalies):
    print("=============TURBINES IN NEED OF ATTENTION============")
    for turbine_id in anomalies.index:
        print(turbine_id)
    print("=====================SPECIFICATIONS====================")

    for turbine_id in anomalies.index:
        if anomalies.loc[turbine_id, 'mean_temp'] > TEMP_LIMIT:
            print(
            f"{turbine_id}: Mean temperature "
            f"({anomalies.loc[turbine_id]['mean_temp']:.2f}°C) exceeds 85°C"
        )
        if anomalies.loc[turbine_id, 'max_vib'] > VIB_LIMIT:
            print(
                f"{turbine_id}: Maximum vibration "
                f"({anomalies.loc[turbine_id]['max_vib']:.2f} mm/s) exceeds 15 mm/s"
            )

def main():
    df = pd.read_csv(DATA_FILE)
    metrics = compute_metrics(df)
    report(find_anomalies(metrics))
    
if __name__ == "__main__":
    main()
