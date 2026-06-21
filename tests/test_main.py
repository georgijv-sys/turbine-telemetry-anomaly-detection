"""Unit tests for the turbine anomaly-detection logic in main.py.

These pin down the rules a turbine is flagged on:
    * mean temperature > 85.0 C    (an average across the sample)
    * max  vibration   > 15.0 mm/s (a single spike)
combined with OR. They mirror the edge cases checked by hand during development.
"""
import pandas as pd

from main import compute_metrics, find_anomalies, report, TEMP_LIMIT, VIB_LIMIT


def make_df(rows):
    """Build a telemetry DataFrame from (turbine_id, temperature_c, vibration_mm_s) tuples."""
    return pd.DataFrame(rows, columns=["turbine_id", "temperature_c", "vibration_mm_s"])


def test_compute_metrics_aggregates_per_turbine():
    df = make_df([
        ("T-01", 80.0, 5.0),
        ("T-01", 90.0, 9.0),   # T-01: mean temp 85.0, max vib 9.0
        ("T-02", 50.0, 20.0),  # T-02: mean temp 50.0, max vib 20.0
    ])
    m = compute_metrics(df)
    assert m.loc["T-01", "mean_temp"] == 85.0
    assert m.loc["T-01", "max_vib"] == 9.0
    assert m.loc["T-02", "mean_temp"] == 50.0
    assert m.loc["T-02", "max_vib"] == 20.0


def test_high_mean_temperature_is_flagged():
    df = make_df([("T-01", 90.0, 5.0), ("T-01", 92.0, 6.0)])  # mean 91 > 85
    flagged = find_anomalies(compute_metrics(df))
    assert "T-01" in flagged.index


def test_vibration_spike_is_flagged_even_with_low_average():
    # A single big spike: average vibration is low, but the MAX exceeds the limit.
    df = make_df([("T-07", 60.0, 3.0), ("T-07", 60.0, 25.0), ("T-07", 60.0, 4.0)])
    flagged = find_anomalies(compute_metrics(df))
    assert "T-07" in flagged.index


def test_all_within_limits_returns_no_anomalies():
    df = make_df([("T-01", 60.0, 5.0), ("T-02", 70.0, 10.0)])
    flagged = find_anomalies(compute_metrics(df))
    assert flagged.empty


def test_or_logic_flags_either_rule():
    df = make_df([
        ("T-hot", 90.0, 5.0),     # fails temperature only
        ("T-shake", 60.0, 20.0),  # fails vibration only
        ("T-ok", 60.0, 5.0),      # passes both
    ])
    flagged = find_anomalies(compute_metrics(df))
    assert set(flagged.index) == {"T-hot", "T-shake"}


def test_turbine_failing_both_rules_appears_once():
    df = make_df([("T-bad", 95.0, 25.0)])
    flagged = find_anomalies(compute_metrics(df))
    assert list(flagged.index) == ["T-bad"]


def test_thresholds_are_strict_not_inclusive():
    # Exactly at the limit must NOT be flagged ( > , not >= ).
    df = make_df([("T-edge", TEMP_LIMIT, VIB_LIMIT)])
    flagged = find_anomalies(compute_metrics(df))
    assert flagged.empty


def test_single_reading_turbine_is_still_evaluated():
    df = make_df([("T-solo", 100.0, 2.0)])  # one hot reading
    flagged = find_anomalies(compute_metrics(df))
    assert "T-solo" in flagged.index


def test_empty_input_does_not_crash():
    flagged = find_anomalies(compute_metrics(make_df([])))
    assert flagged.empty


def test_report_prints_failing_turbine_id_and_value(capsys):
    df = make_df([("T-04", 90.0, 5.0)])
    report(find_anomalies(compute_metrics(df)))
    out = capsys.readouterr().out
    assert "T-04" in out
    assert "Mean temperature" in out
