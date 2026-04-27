# ChemStream

Real-time chemical process monitoring and anomaly detection pipeline.

## Overview

ChemStream is an end-to-end streaming data engineering project that ingests
continuous sensor data from a simulated chemical plant (Tennessee Eastman
Process), processes it in real time, stores it in a time-series database,
detects anomalies using machine learning, and surfaces everything on a live
operator dashboard.

## Architecture
TEP CSV → Python Producer → Kafka → Faust Processor → TimescaleDB → Streamlit
→ ML Scorer (Isolation Forest) ↗

## Tech Stack

- **Ingestion:** Python + kafka-python
- **Transport:** Apache Kafka
- **Processing:** Faust (Python stream processor)
- **Storage:** TimescaleDB (PostgreSQL extension)
- **ML:** scikit-learn Isolation Forest
- **Dashboard:** Streamlit
- **Orchestration:** Docker Compose

## Dataset

Tennessee Eastman Process (TEP) benchmark dataset.
Download from [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/6C3JR1)
and place the `.RData` files in the `data/` directory.

## Project Status

- [x] Phase 0 — Exploratory Data Analysis
- [ ] Phase 1 — Pipeline backbone (Kafka + TimescaleDB + Producer + Faust)
- [ ] Phase 2 — Streamlit dashboard
- [ ] Phase 3 — Anomaly detection (Isolation Forest)
- [ ] Phase 4 — Polish and documentation

## Author

Rabiai Abdelouahed