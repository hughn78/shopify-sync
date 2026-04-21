# Shopify Export Roadmap

## Purpose

This document turns the current Pharmacy Stock Sync prototype into a concrete implementation roadmap for producing:

1. a **real Shopify inventory upload/export CSV** from reconciled FOS + Shopify data
2. a **real Shopify products export CSV** from a richer canonical product registry and Shopify projection layer

It is written around the current app architecture:

- FastAPI backend
- SQLite + Alembic schema
- canonical product registry
- reviewed source-product linking
- inventory reconciliation workflow

---

## Current State

The app can currently:

- import Shopify products CSVs
- import Shopify inventory CSVs
- import FOS cleaned stock XLSX/CSV files
- normalize and persist source records
- create canonical-product links
- generate reconciliation rows
- export a safer Shopify inventory upload bundle:
  - `safe_upload_to_shopify_*.csv`
  - `exceptions_needing_review_*.csv`

The app cannot yet:

- reconstruct a true Shopify inventory export from FOS alone
- reconstruct a true Shopify products export from a FOS stock report alone
- act as a complete Shopify catalog projection system

---

## Key Product Truths

### Inventory export truth

A FOS stock report is a valid **stock source**, but not a sufficient Shopify inventory export source by itself.

To generate a trustworthy Shopify inventory upload/export file, the app must combine:

- FOS stock quantities
- Shopify inventory identity
- reviewed canonical mappings
- location-aware sync rules

### Product export truth

A FOS stock report is **not** a full product catalog source.

To generate a real Shopify products export CSV, the app needs a richer source of:

- handles
- product titles
- body HTML / descriptions
- vendor
- product type
- tags
- variant structure
- prices
- status
- images and other catalog metadata

That means the app needs to evolve from a stock reconciliation tool into a **catalog projection system**.

---

## End-State Architecture

The app should eventually treat Shopify and FOS as two source systems projected through a canonical registry.

### Layers

1. **Canonical Product Registry**
   - one real-world product identity
   - reusable identifiers
   - curated preferred metadata

2. **Source System Records**
   - FOS stock records
   - Shopify product records
   - Shopify inventory records

3. **Reviewed Match Layer**
   - approved source-to-canonical links
   - conflict/exclusion handling
   - durable matching memory

4. **Projection Layer**
   - Shopify inventory projection
   - Shopify product projection

5. **Export Layer**
   - safe inventory upload bundle
   - products export bundle
   - exception files

---

## Roadmap Overview

### Phase 1, production-safe inventory uploads

**Goal:** Turn the app into a trustworthy Shopify inventory upload generator.

### Phase 2, richer catalog memory

**Goal:** Preserve enough Shopify and canonical metadata to support product export generation later.

### Phase 3, Shopify product projection

**Goal:** Model Shopify catalog structure explicitly inside the app.

### Phase 4, true product export generation

**Goal:** Generate a real Shopify products export CSV from the app.

### Phase 5, operational hardening

**Goal:** Make the workflow repeatable, testable, and safe in real store operations.

---

# Phase 1, Production-Safe Inventory Uploads

## Objective

Generate a file that is safe for Hugh’s real workflow:

1. export Shopify inventory CSV
2. export FOS cleaned stock XLSX
3. import both into app
4. review exceptions
5. upload safe inventory CSV into Shopify

## Required data

### FOS source fields

Already available or mostly available:

- `Stock Name`
- `Full Name`
- `APN`
- `PDE`
- `SOH`
- optional category/department/price fields

### Shopify source fields

Must be imported and persisted consistently:

- `Handle`
- `Title`
- `SKU`
- `Barcode`
- `Variant ID`
- `Inventory Item ID`
- `Location ID`
- `Location Name`
- current inventory quantity

## Required app capabilities

### 1. strict sync-safe row rules

A row can only go into `safe_upload_to_shopify.csv` if:

- the canonical match is approved or auto-accepted
- `Inventory Item ID` exists
- `Location ID` exists
- quantity proposal exists
- no warnings or blocker flags exist
- there is exactly one approved Shopify target row
- there is exactly one approved FOS source row

### 2. explicit exception reporting

Every blocked row must explain why, for example:

- `MISSING_SHOPIFY_INVENTORY_ITEM_ID`
- `MISSING_SHOPIFY_LOCATION_ID`
- `SYNC_STATUS_NOT_READY`
- `MISSING_FOS_LINK`
- `MISSING_SHOPIFY_LINK`
- `LARGE_DELTA`
- `AMBIGUOUS_MATCH`
- `MULTIPLE_SHOPIFY_ROWS`

### 3. location mapping rules

Add app settings for:

- default Shopify location ID or pattern
- optional FOS report -> Shopify location mapping
- reserve stock buffer
- delta threshold requiring manual approval

## Backend changes

### Recommended schema additions

Add to settings / rules layer:

- `inventory_sync_rules`
  - `shopify_location_id`
  - `shopify_location_name`
  - `reserve_buffer`
  - `max_auto_delta`
  - `require_review_on_negative_delta`
  - `active`

Optional but useful:

- `inventory_sync_attempts`
  - `run_id`
  - `row_id`
  - `status`
  - `exported_at`
  - `notes`

## API additions

- `GET /api/reconciliation-runs/{run_id}/summary`
- `GET /api/reconciliation-runs/{run_id}/exceptions`
- `POST /api/exports/shopify-upload/{run_id}` (already added, keep evolving)
- `POST /api/reconciliation-runs/{run_id}/recompute`

## UI additions

### Inventory Sync page

Add:

- safe rows count
- exceptions count
- blocker chips by category
- download buttons for:
  - safe upload file
  - exceptions file
- filter toggles:
  - safe only
  - exceptions only
  - large deltas
  - missing IDs

### Import flow

Add a post-import health summary:

- Shopify inventory rows imported
- Shopify products rows imported
- FOS rows imported
- unmatched rows count
- duplicate identity groups count

## Success criteria for Phase 1

The app can reliably generate a Shopify-safe inventory upload file from:

- Shopify inventory export CSV
- Shopify products export CSV
- FOS cleaned stock XLSX

without unsafe rows leaking into the upload file.

---

# Phase 2, Richer Catalog Memory

## Objective

Strengthen the canonical registry so the app remembers enough catalog structure to support true product export generation later.

## Required changes

### Preserve more Shopify product fields on import

Current source-product persistence is too shallow for a true products export.

The app should retain fields such as:

- handle
- title
- vendor
- product type
- status
- variant title
- option1/2/3 names and values
- variant price
- compare-at price
- barcode
- SKU
- published / draft status
- tags
- body HTML
- image source references when available

## Recommended schema direction

Either enrich `source_products.raw_payload_json` usage systematically or add dedicated tables.

Recommended long-term approach:

### `shopify_products_projection`
- canonical_product_id
- handle
- title
- body_html
- vendor
- product_type
- tags_json
- status
- seo_title
- seo_description
- source_of_truth
- completeness_score

### `shopify_variants_projection`
- canonical_product_id
- variant_rank
- variant_title
- option1_name
- option1_value
- option2_name
- option2_value
- option3_name
- option3_value
- sku
- barcode
- price
- compare_at_price
- inventory_tracked
- taxable
- requires_shipping
- weight

## Matching memory improvements

Keep expanding `product_identifiers` from:

- approved links
- product imports
- product export imports
- manual curation

Add confidence metadata if helpful:

- source priority
- human-reviewed flag
- last verified timestamp

## Success criteria for Phase 2

The canonical registry knows enough about Shopify catalog structure that product export generation becomes feasible.

---

# Phase 3, Shopify Product Projection Layer

## Objective

Represent what Shopify should look like, separately from both FOS and raw Shopify imports.

## Why

Raw Shopify imports describe the current state.
A product projection describes the desired exportable state.

That allows the app to:

- preserve current Shopify catalog structure
- incorporate reviewed canonical improvements
- emit a coherent products export CSV later

## Projection rules

For each canonical product, define how to derive:

- canonical title -> Shopify title
- department/category -> Shopify product type / tags
- barcode/APN/PDE/SKU -> preferred variant identifiers
- sell price -> Shopify price
- availability / stock policy -> status rules

## UI required

### Canonical Registry page

Add editable fields for:

- preferred Shopify title
- vendor
- product type
- tags
- default price
- handle override
- default status
- product body / notes

### Projection review page

A new page showing:

- canonical product
- current Shopify product data
- projected Shopify export row(s)
- completeness blockers
- publish/export readiness

## Success criteria for Phase 3

The app can preview what a Shopify products export row would look like for each canonical product.

---

# Phase 4, True Shopify Products Export Generation

## Objective

Generate a real Shopify Products Export CSV from the app.

## Hard rule

Do not attempt this from FOS stock alone.

Use:

- existing Shopify products exports as baseline structure memory
- canonical product registry
- reviewed projection fields
- explicit completeness and safety checks

## Output files

### A. `shopify_products_export_ready.csv`
Only rows where required catalog fields are complete.

### B. `shopify_products_exceptions.csv`
Rows blocked due to incomplete or ambiguous catalog data.

## Required completeness checks

Examples:

- missing handle
- missing title
- missing SKU
- missing barcode when required
- broken variant option structure
- missing price
- missing status
- duplicate handles
- duplicate SKU collisions

## Export templates

Support at least one template matching Hugh’s actual Shopify products export style.

Long term:

- template versioning
- different export modes by Shopify store/schema

## Success criteria for Phase 4

The app can generate a Shopify products export CSV that is structurally valid and reviewable before import.

---

# Phase 5, Operational Hardening

## Objective

Make the app dependable in real repeated use.

## Required work

### Automated regression fixtures

Keep real-world anonymized fixtures for:

- Shopify inventory exports
- Shopify products exports
- FOS cleaned XLSX files
- known exception cases

### Tests to add

- repeated import across dates
- same product with reordered rows
- multiple Shopify locations
- duplicate SKU edge cases
- missing APN/PDE cases
- product export completeness blocking
- duplicate handle detection
- safe upload bundle correctness

### Observability

Add:

- import summaries
- export summaries
- exception counts by type
- last successful run timestamps
- last successful safe-upload generation timestamp

### Optional future direction

Direct Shopify Admin API support for inventory updates, with:

- dry-run mode
- apply mode
- per-row audit trail
- retry handling
- rollback/reconciliation logs

---

# Recommended Immediate Next Milestone

## Build milestone: “Inventory Upload Production Candidate”

Implement the following in order:

1. confirm Hugh’s exact Shopify inventory upload CSV shape
2. add stricter reconciliation blocker rules
3. surface blocker counts and exception filtering in UI
4. preserve more Shopify import fields if missing
5. validate generated safe-upload CSV against Hugh’s real Shopify import workflow

### Deliverable

A version of the app where Hugh can:

- import real Shopify inventory export CSV
- import real Shopify products export CSV
- import real FOS cleaned XLSX
- click process
- review exceptions
- export a Shopify-safe upload CSV with confidence

---

# Explicit Non-Goals Right Now

These should not be treated as immediate objectives:

- generating a complete Shopify products export from FOS stock alone
- inventing missing Shopify catalog structure automatically
- auto-applying risky stock changes without review
- treating fuzzy matches as sync-safe without confirmation

---

# Final Summary

## What the app should become

### For inventory
A trustworthy **Shopify inventory upload generator** driven by:

- FOS stock report
- Shopify exports
- canonical mapping
- strict blocker rules

### For products
A **Shopify catalog projection and export system** driven by:

- prior Shopify product exports
- canonical product registry
- reviewed projection fields
- completeness validation

## Practical sequencing

1. make inventory upload generation production-safe
2. enrich the canonical/product memory model
3. build Shopify product projection tables and UI
4. generate real products export CSVs

That is the safest and most realistic path from the current codebase to a dependable export tool.
