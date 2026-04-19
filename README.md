# Pharmacy Stock Sync - Essential Backend Tools

Essential backend tools for pharmacy inventory reconciliation, scanners, and audit.  

## Core Features
- **Canonical product registry**: Master identity layer across discharge channels
- **Source product ingestion**: Raw product data from multiple suppliers
- **Flexible import handling**: Upload defenses for varied wholesale pricebooks, catalogs, and scraped CSVs
- **Review workflow**: In-app review/approve/exclude for edge cases
- **Multi-importer**: Support for Avery files, pricebooks, scraped product lists

## Setup
```bash
# Backend
cd backend && source .venv/bin/activate && alembic upgrade head && uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend
cd frontend && npm install && npm run dev -- --host 127.0.0.1 --port 5173
```

## Important Notes
- `.gitignore` protects local imports and macOS junk files
- New source-type filters handle wholesale pricebooks, mastercatalogs, and scraped catalogs
- Review UI now handles bulk operations safely
- API `/import` now accepts **multiple files** at once