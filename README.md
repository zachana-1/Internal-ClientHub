# Click Up Implementation

# Enterprise Client Onboarding & PS Automation Engine

## Overview
This repository contains the architecture, frontend interfaces, and service modules for an enterprise client onboarding system. The system ingests executed contracts, parses technical interface scope and billing milestones, captures client questionnaire responses, provisions ClickUp project spaces, and syncs operational data into a unified database (simulating Databricks Unity Catalog for future deployment).

┌─────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  1. SOW / PDF   ├────>│ TechBook HTML App    ├────>│ ClickUp API          │
│     Contract    │     │ • Contract Parser    │     │ • Template Provision │
└─────────────────┘     │ • Client Form        │     │ • Task & Track Setup │
└──────────┬───────────┘     │ • Time Tracking      │
│                 └──────────┬───────────┘
▼                            │
┌──────────────────────┐                │
│ Local DB / DataFrame ├<───────────────┘
│ (DuckDB / Parquet)   │
└──────────┬───────────┘
│
▼
┌──────────────────────┐
│ Databricks (Future)  │
│ • Unity Catalog Delta│
│ • Cross-Tenant Sync  │
└──────────────────────┘


---

## End-to-End System Workflow

### Step 1: Contract Upload & Automated Parsing
* **Action:** The internal project manager uploads or pastes the contract/Statement of Work (SOW) text into the **TechBook HTML Interface**.
* **Engine:** The `ContractParser` module extracts key metadata:
  * Client Name and Target Go-Live Dates.
  * Required technical interfaces (e.g., HL7 feeds, FHIR APIs, SFTP integrations).
  * Scope deliverables and action items.
  * **Billing Milestones:** Payment terms, percentage triggers, deposit amounts, and invoicing conditions.

### Step 2: Hosted Client Questionnaire & Data Staging
* **Action:** The hosted HTML interface dynamically generates an onboarding form based on missing contract fields and required client inputs.
* **Storage:** All captured inputs (client contact details, integration specs, target go-live dates, and milestone criteria) are immediately written to a local **Pandas DataFrame / DuckDB table**.
* **Databricks Readiness:** The local DuckDB/Parquet storage layer acts as a drop-in simulator for **Databricks Unity Catalog Delta tables**. No code re-architecture is required when the Databricks instance goes live.

### Step 3: Automated ClickUp Provisioning & Template Selection
* **Trigger:** Once the questionnaire is completed, the `ClickUpConnector` calls the ClickUp REST API v2.
* **Template Provisioning:** Based on the contract type and detected interfaces, the app provisions a pre-defined ClickUp Space/Folder structure:
  * **Track 1:** Technical Integration & Interface Setup.
  * **Track 2:** Change Management & Training.
  * **Track 3:** Finance & Billing Milestones (tagged with high priority and billing conditions).

### Step 4: Time Tracking & Task Execution
* **Action:** Professional Services (PS) team members execute implementation tasks directly in ClickUp.
* **Tracked Hours:** Hours logged via ClickUp’s Time Tracking API (`/task/{task_id}/time`) are continually synced back to the local database, mapping logged hours against estimated budgets per track.

### Step 5: Single Source of Truth & Future Cross-Tenant Expansion
* **Client Source of Truth:** The central database (DuckDB locally, Delta Lake in Databricks) aggregates project health, completed milestones, logged time, and active interfaces.
* **Executive Dashboard:** Internal teams query this data to track project margins, revenue recognition against billing milestones, and resource availability.
* **Cross-Tenant Sync (Phase 2):** When deployed to Databricks, Delta Sharing or API webhooks will route validated client state and PS metrics to external client tenants or adjacent enterprise PS spaces.

---

## Local Repository Structure

```text
client-onboarding-hub/
├── README.md                   # System documentation & workflow guide
├── index.html                  # Single-page HTML interface (TechBook + Drawer)
├── services/
│   ├── contract_parser.js      # Contract, interface & billing regex parser
│   ├── clickup_connector.js    # ClickUp REST API client for tasks & milestones
│   └── powerbi_parser.js       # PowerBI DAX and dataset schema parser
└── mock_data/
    └── index.js                # Local TechBook interface data index