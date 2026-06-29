"""Continuous telemetry simulator — a local stand-in for the streaming pipeline.

Every tick it generates one realistic reading per turbine and rewrites the most
recent window to live_telemetry.csv (atomic, so the dashboard never reads a
half-written file). Faults are injected automatically and worsen gradually,
mimicking real degradation.

In production the sensors would publish to a message queue (Kafka / Kinesis);
this file + simulator are the local equivalent of that producer + channel.

Run it in its own terminal, alongside the dashboard:
    python simulator.py
"""
from __future__ import annotations

import os
import random
import time
from datetime import datetime

import pandas as pd

from main import DATA_FILE  # the historical sample we learn normal behaviour from

LIVE_FILE = "live_telemetry.csv"
WINDOW = 300            # keep only the most recent N readings (the "hot" window)
TICK_SECONDS = 1.0      # how often new readings are produced
FAULT_START_CHANCE = 0.015   # per turbine, per tick: chance a healthy turbine starts failing
FAULT_RECOVER_CHANCE = 0.04  # per tick: chance a failing turbine recovers
MAX_FAULT_LEVEL = 40.0


def learn_profiles(path: str) -> dict:
    """Learn each turbine's normal temperature/vibration spread from the sample."""
    df = pd.read_csv(path)
    profiles = {}
    for tid, g in df.groupby("turbine_id"):
        profiles[tid] = {
            "temp_mean": g["temperature_c"].mean(),
            "temp_std": max(g["temperature_c"].std(), 1.0),
            "vib_mean": g["vibration_mm_s"].mean(),
            "vib_std": max(g["vibration_mm_s"].std(), 0.5),
            "rpm_mean": g["rpm"].mean(),
        }
    return profiles


def make_reading(tid: str, profile: dict, fault: dict | None) -> dict:
    """One realistic reading; a fault adds its (growing) level to the relevant metric."""
    temp = random.gauss(profile["temp_mean"], profile["temp_std"])
    vib = random.gauss(profile["vib_mean"], profile["vib_std"])
    if fault and fault["type"] == "overheat":
        temp += fault["level"]
    elif fault and fault["type"] == "vibration":
        vib += fault["level"]
    return {
        "timestamp": datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        "turbine_id": tid,
        "temperature_c": round(max(temp, 0.0), 1),
        "vibration_mm_s": round(max(vib, 0.0), 1),
        "rpm": round(max(random.gauss(profile["rpm_mean"], 0.5), 0.0), 1),
    }


def atomic_write(df: pd.DataFrame, path: str) -> None:
    """Write the window to a temp file, then atomically swap it into place."""
    tmp = f"{path}.tmp"
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)  # atomic rename -> reader always sees a complete file


def main() -> None:
    profiles = learn_profiles(DATA_FILE)
    faults: dict[str, dict | None] = {tid: None for tid in profiles}
    rows: list[dict] = []
    print(f"Simulating {len(profiles)} turbines -> {LIVE_FILE}  (Ctrl+C to stop)")
    try:
        while True:
            for tid in profiles:
                fault = faults[tid]
                if fault is None:
                    if random.random() < FAULT_START_CHANCE:
                        faults[tid] = {"type": random.choice(["overheat", "vibration"]), "level": 0.0}
                else:
                    fault["level"] = min(fault["level"] + random.uniform(0.8, 1.8), MAX_FAULT_LEVEL)
                    if random.random() < FAULT_RECOVER_CHANCE:
                        faults[tid] = None
                rows.append(make_reading(tid, profiles[tid], faults[tid]))
            rows = rows[-WINDOW:]               # drop the oldest -> bounded "hot" window
            atomic_write(pd.DataFrame(rows), LIVE_FILE)
            time.sleep(TICK_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
