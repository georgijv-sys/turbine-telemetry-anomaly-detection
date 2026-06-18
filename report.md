# Engineering Report — Turbine Telemetry Analysis & Proposed Monitoring Platform

**To:** Chief Technology Officer, AeroGrid
**From:** Data Engineering
**Re:** Failing turbines and a resilient real-time pipeline

This report summarises the telemetry analysis and proposes an architecture to prevent further undetected failures.

## Findings
Analysis of the 24-hour sample (5,000 readings across 10 turbines) identified **two turbines requiring urgent maintenance**, each breaching a separate safety threshold:

- **T-04** — mean temperature **90.6 °C**, above the 85.0 °C limit (sustained overheating).
- **T-07** — vibration spike of **25.0 mm/s**, above the 15.0 mm/s limit.

The other eight turbines operated within safe limits; results were independently verified against the raw data.

## Architecture Justification
The current single server fails because sensors write straight to it — any spike or outage loses data. The proposed pipeline removes this fragility. Readings first enter a **message queue** (e.g., AWS Kinesis), which buffers bursts and decouples ingestion from processing, so no data is lost if a downstream component slows or restarts. A **stream-processing layer** (e.g., AWS Lambda) then applies the anomaly rules in real time and raises an immediate alert. Because the queue is replicated across availability zones, there is **no single point of failure**, directly solving the crashing issue.

## Cost Optimisation
Storage is split by access pattern. Only recent data sits in the fast, costlier **time-series database** for live dashboards; all history is archived in a low-cost **data lake** (Amazon S3). Applying **lifecycle policies** that automatically shift ageing data into cheaper cold tiers (e.g., S3 Glacier) minimises long-term cost while retaining full history, which is essential for a continuous, high-volume pipeline.
