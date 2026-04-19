# Pharmacy Stock Sync Schema

The database is built around a canonical product registry.

## Core concepts

- `canonical_products`: one real-world product record.
- `source_products`: source-system specific records from Shopify or FOS.
- `product_identifiers`: reusable identifiers like barcode, APN, PDE, and SKU.
- `source_product_links`: reviewed connections between source records and canonical products.
- `inventory_snapshots`: stock state separated from product identity.
- `inventory_reconciliation_rows`: stock sync proposals derived through canonical products.

## Migration support

Schema changes are managed through Alembic.

Initial migration:
- `backend/alembic/versions/0001_initial_canonical_registry.py`

Apply migrations:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

## Why this matters

This avoids fragile row-to-row matching and creates durable matching memory across runs.
