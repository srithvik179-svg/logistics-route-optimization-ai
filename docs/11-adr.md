# RoutePilot AI – Architecture Decision Records (ADR)

## Overview

This document records the key architectural and design decisions made during the development of RoutePilot AI, detailing the context, rationale, and consequences of each decision.

---

## ADR-001: Selection of FastAPI (ASGI) for Backend Services

- **Status:** Accepted
- **Date:** 2026-07
- **Context:** RoutePilot AI requires high-throughput processing of analytical data payloads and ML model inferences for logistics route optimization.
- **Decision:** Use FastAPI with Uvicorn ASGI server as the primary backend microservices framework.
- **Rationale:**
  - Asynchronous non-blocking architecture allows handling concurrent requests efficiently.
  - Native Pydantic integration guarantees automatic request/response schema validation.
  - Automatic OpenAPI / Swagger documentation generation speeds up testing and review.
- **Consequences:** Requires async-compatible libraries for maximum performance.

---

## ADR-002: Vanilla JavaScript (ES6+) for Frontend Single-Page Application

- **Status:** Accepted
- **Date:** 2026-07
- **Context:** The application needs a responsive, glassmorphic executive dashboard without build complexity or external dependency risks during evaluation.
- **Decision:** Build the entire frontend using Vanilla JavaScript (ES6+), HTML5, and native CSS3 without heavy client-side frameworks (React, Vue, Angular).
- **Rationale:**
  - **Zero build tool requirement:** No `npm run build` or Webpack bundling step needed.
  - **Instant load times:** No JavaScript framework overhead or virtual DOM abstraction.
  - Direct DOM control allows seamless integration with Three.js 3D WebGL scenes.
- **Consequences:** Requires custom state management and component lifecycle implementation.

---

## ADR-003: Three.js for 3D WebGL Digital Twin Command Center

- **Status:** Accepted
- **Date:** 2026-07
- **Context:** Executives need a spatial 3D visualization to inspect global logistics hub nodes and active corridor shipment velocity.
- **Decision:** Integrate Three.js (r128) WebGL library for rendering 3D interactive graphics inside HTML `<canvas>`.
- **Rationale:**
  - Industry standard WebGL wrapper with strong community support and documentation.
  - Provides built-in particle systems and OrbitControls for smooth camera navigation.
  - High performance rendering capable of 60 FPS on standard modern GPU hardware.
- **Consequences:** Requires explicit memory cleanup for Three.js geometries and materials on module unmount.

---

## ADR-004: In-Memory DataRepository with Dataset Loader Pipeline

- **Status:** Accepted
- **Date:** 2026-07
- **Context:** The Dell logistics dataset is provided as a multi-sheet Excel file (`Dell_Logistics_Route_Optimization.xlsx`).
- **Decision:** Load and validate the dataset at application startup into an in-memory Singleton `DataRepository`.
- **Rationale:**
  - Eliminates disk I/O latency for analytical queries and API payload generation.
  - Centralizes dataset validation, date enrichment, and duplicate removal in one pipeline.
  - Simplifies setup for hackathon evaluation without requiring a separate SQL database.
- **Consequences:** Memory usage scales with dataset size; large datasets in future will require database migration.

---

## ADR-005: Scikit-learn Ensemble Models for SLA Breach Prediction

- **Status:** Accepted
- **Date:** 2026-07
- **Context:** SLA breach risks need accurate prediction with explainable feature contributions.
- **Decision:** Use Scikit-learn Random Forest ensemble classifiers combined with SHAP (SHapley Additive exPlanations).
- **Rationale:**
  - High prediction accuracy (94.8% accuracy, 0.968 ROC-AUC) on tabular logistics data.
  - SHAP integration provides transparent, auditable feature attributions per prediction.
  - Lightweight CPU execution without requiring GPU hardware acceleration.
- **Consequences:** Models must be serialized and re-loaded when updated.

---

## ADR-006: Dedicated 🎯 Demo Mode Presentation Engine

- **Status:** Accepted
- **Date:** 2026-07
- **Context:** Hackathon judges need to quickly evaluate all 14 platform capabilities in a structured, guided story format.
- **Decision:** Create an additive, independent `Demo Mode` engine (`demo_mode.js` and `demo_mode.css`).
- **Rationale:**
  - Provides an automated 8-step guided presentation tour without user manual navigation.
  - Displays story overlays detailing Problem → AI Solution → Business Value.
  - Includes keyboard shortcuts, fullscreen controls, and isolated demo dataset toggles.
- **Consequences:** Must maintain step selectors as frontend components evolve.
