# SynQanun — Legal Docs Modeling & API

A legal data pipeline that parses Arabic DOCX files (**Laws, Judgments, Fatwas**), stores extracted data in a relational database, and serves it through a **FastAPI** service.

---

## Project Overview

SynQanun ingests Arabic legal documents (DOCX — text selectable, no OCR) and provides:
- Parsing & normalization (Arabic text + dates)
- Relational storage (SQL Server)
- Retrieval + simple search via FastAPI

---
## Project Structure
```bash

SynQanun/
├── app/                        # Core Logic & API
│   ├── main.py                 # FastAPI Entry Point
│   ├── docx_text.py            # DOCX extraction helper
│   ├── parse_law.py            # Legislation parser
│   ├── parse_judgment.py       # Court rulings parser
│   ├── parse_fatwa.py          # Fatwa parser
│   ├── schema.sql              # Database Tables & Indexes
│   └── requirements.txt        # Project dependencies
├── load files/                 # SQL Ingestion Scripts
│   ├── load_fatwas_sqlserver.py
│   ├── load_laws_sqlserver.py
│   └── load_judgments_sqlserver.py
├── legal_loader/               # Source DOCX files (Input)
├── Json_clean_all/             # Processed JSON output folder
├── export_all_clean_json.py    # Main script to convert DOCX to JSON
└── README.md                   # Project documentation

```
## Data Model (Schema)

The schema is designed around legal document hierarchy and scalability:

### 1) Laws
- Stored as:
  - **Law metadata**
  - **Law articles** (1:N relationship)
- Each article is stored as a separate record for efficient search and updates.

### 2) Judgments
- Stored as:
  - **Judgment main record**
  - **Legal principles** (1:N relationship)

### 3) Fatwas
- Stored as:
  - **Fatwa main record**
  - **Principles**

---

## Setup & Run

### Step 1 — Install requirements
```bash
pip install -r requirements.txt
```
 
### Step 2 — Run Database Script
Execute the SQL script in your database manager (SSMS)
Location: sql/schema.sql

### Step 3 — Process Documents
```bash
python export_all_clean_json.py
```
### Step 4 — Load to SQL Server
```bash
python load_laws_sqlserver.py
python load_judgments_sqlserver.py
python load_fatwas_sqlserver.py
```
### Step 5 — Launch API
```bash
python -m uvicorn app.main:app --reload
```
Visit http://127.0.0.1:8000/docs to test the API via Swagger UI.
# Design Decisions

## Idempotency
Loaders rely on natural keys (e.g., reference numbers) to prevent duplicates when re-running scripts.
## Performance
Unique indexes and retrieval-oriented indexing were added to support large datasets.

## Migration-friendly

-Although the current runtime uses SQL Server, the schema stays close to Postgres conventions for easier migration later.
