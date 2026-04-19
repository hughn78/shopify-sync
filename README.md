# Pharmacy Stock Sync

Pharmacy Stock Sync is a local desktop-first inventory reconciliation app for pharmacy operations. It builds and maintains a canonical product registry so Shopify products, Shopify inventory, and FOS stock data can be linked safely through a durable identity layer.

## Stack

- Python backend (FastAPI, SQLAlchemy, SQLite, Alembic)
- React + TypeScript frontend (Vite)
- Local-only API bridge
- Fully local data storage and export generation

## Setup

### Backend

```bash
cd backend
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend runs on `http://127.0.0.1:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173`

## Sample files

Use the files in `sample_data/`:
- `shopify_products_sample.csv`
- `shopify_inventory_sample.csv`
- `fos_stock_sample.xlsx`

## Workflow

1. Import Shopify Products, Shopify Inventory, and FOS files from the Imports page.
2. Source records are normalized and stored in `source_products`.
3. The matching engine resolves exact identifiers, normalized names, fuzzy candidates, and creates canonical products when needed.
4. Review uncertain links in the Link Review page.
5. Run inventory reconciliation through canonical products on the Inventory Sync page.
6. Export Shopify-ready inventory CSV outputs.

## Canonical registry design

This app does not rely on direct Shopify-row to FOS-row matching. Instead:
- `canonical_products` store the real-world product identity.
- `source_products` store source-specific records.
- `source_product_links` hold reviewable links.
- `product_identifiers` store reusable identifiers.
- `inventory_snapshots` store stock separately from identity.

That separation allows durable matching memory, auditability, and safer future sync behaviour.

## SQLite schema documentation

See `docs/schema.md`.

## Example exports

- `exports/example_inventory_sync.csv`
- `exports/example_barcode_update.csv`
- generated run outputs are written to `exports/generated/`

## Confidence thresholds and sync rules

Thresholds and sync settings live in:
- `backend/app/config.py`
- `.env` / `.env.example`

Important values:
- `AUTO_ACCEPT_THRESHOLD`
- `REVIEW_THRESHOLD`
- `PRIMARY_SHOPIFY_LOCATION_PATTERN`
- `RESERVE_STOCK_BUFFER`
- `AI_ENABLED`

## Automated sample import to export flow

A repeatable sample workflow is included:

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/run_sample_flow.py
```

What it does:
- resets the local schema
- imports all sample files
- creates or updates source products
- resolves matches
- auto-approves review rows for the scripted sample run
- runs reconciliation through canonical products
- creates inventory and link report exports
- records export history

## Example end-to-end flow using sample files

1. Import all three sample files.
2. Panadol and Nurofen auto-link by exact barcode/APN.
3. Vitamin C remains review-oriented because Shopify starts blank on barcode.
4. Approve or adjust the link in Link Review.
5. Run reconciliation through the canonical layer.
6. Export Shopify inventory sync CSV.
7. Use the barcode export path to fill missing Shopify barcodes where approved.
8. Audit counts remain visible via the dashboard and audit endpoint.

## Deliverables in this repo

- backend and frontend code
- sample config via `.env.example`
- schema docs in `docs/schema.md`
- sample inputs in `sample_data/`
- example exports in `exports/`
- Alembic migration baseline
- automated sample import-to-export flow script

## FutureExtensions

- direct Shopify Admin API integration
- multiple store locations
- supplier catalogue ingestion
- wholesaler feeds
- price reconciliation rules
- scheduled sync jobs
- duplicate canonical detection improvements
- stronger barcode enrichment workflows
