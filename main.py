

import pandas as pd

df = pd.read_csv("telemetry_data(in).csv")

metrics = df.groupby('turbine_id').agg(
    mean_temp = ('temperature_c', 'mean'),
    max_vib=('vibration_mm_s', 'max'),
)

mask = pd.Series((metrics['mean_temp'] > 85) | (metrics['max_vib'] > 15.0))


print("Turbine in need of attention: ")
for turbine_id in metrics[mask].index:

    print("Turbine: ", turbine_id)

for turbine_id in metrics[mask].index:
    if metrics.loc[turbine_id, 'mean_temp'] > 85:
        print(
            f"{turbine_id}: Mean temperature "
            f"({metrics.loc[turbine_id, 'mean_temp']:.2f}°C) exceeds 85°C"
        )

    if metrics.loc[turbine_id, 'max_vib'] > 15:
        print(
            f"{turbine_id}: Maximum vibration "
            f"({metrics.loc[turbine_id, 'max_vib']:.2f} mm/s) exceeds 15 mm/s"
        )