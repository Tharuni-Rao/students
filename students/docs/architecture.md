# Architecture Overview

## Layers

- Frontend: React + Vite + TypeScript dashboard
- Backend: FastAPI REST API with analytics and validation
- Data layer: SQLite-ready JSON/CSV integration and synthetic student seed data
- Analytics engine: weighted scoring, risk rules, segmentation, and what-if simulation

## Flow

1. Seeded synthetic records are generated from a reproducible algorithm.
2. The backend computes score components and risk rules for each student.
3. The dashboard filters, aggregates, and visualizes the data.
4. Students can be inspected individually and scenario changes can be simulated.
5. Import validation accepts CSV and JSON while applying basic schema checks.

## Security note

This is a demo prototype. The current role access is a mock control layer and not a production-grade authorization system.
