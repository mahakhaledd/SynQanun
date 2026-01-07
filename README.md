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

  
## Data Modeling & Scalability

The schema is designed to handle **hundreds of thousands of records** efficiently.

- **Normalized Tables:**  
  Core entities (e.g., **Laws / Judgments / Fatwas**) are stored in main tables, while repeating components like **Articles** and **Principles** are stored in dedicated child tables.  
  This reduces duplication and enables fast filtering/search on specific legal rules.

- **Indexing & Idempotency:**  
  Unique indexes are placed on natural identifiers (e.g., **Reference Numbers**).  
  If a loader is run more than once on the same input, it **updates the existing record** instead of inserting duplicates — ensuring **idempotent** ingestion.


## The Parser Logic

The core strength of this project lies in its three specialized parsers.  
Unlike simple text scrapers, these scripts act as **state machines** that understand the context of Arabic legal writing.

---

## 1) Legislation Parser (`parse_law.py`)

- **Hierarchical Extraction:** Identifies the law’s title, publication date in the *Official Gazette*, and enforcement date.
- **Article Tracking:** Uses regex to detect article headers (e.g., `مادة 1`).
- **Version Control:** Detects phrases such as *Original Text* and *Final Text as of [Date]* to store amendment history, ensuring the database reflects the most recent version of the law.

---

## 2) Judgment Parser (`parse_judgment.py`)

- **Context Awareness (Modes):** Court rulings are long and structured. The parser switches between section “modes”.
  - When it hits `الوقائع` (Facts), it collects text into the **facts** field.
  - When it hits `الحيثيات` (Reasons), it switches and collects into the **reasons** field.
- **Multi-Principle Extraction:** A single judgment may include multiple legal principles. The parser detects patterns like:
  - `Principle No. 1`
  - `Principle No. 2`
  
  Each principle is stored as a separate, searchable entity linked to the main judgment.

---

## 3) Fatwa Parser (`parse_fatwa.py`)

- **Metadata Detection:** Extracts the fatwa number, year, and issuing authority automatically.
- **Date Normalization:** Arabic documents use multiple date formats (e.g., `DD/MM/YYYY` or `YYYY-MM-DD`).  
  The parser includes a `_date_any` utility that n

## 🛠️ Deep Dive: The Parser Architecture

Our parsing engine is designed to handle the linguistic complexity of Arabic legal documents.  
It uses a **rule-based state machine** combined with **Regular Expressions (Regex)** to navigate document sections reliably.

---

## 1) Legislation (Laws) — `parse_law.py`

Laws follow a strict hierarchy. The parser identifies transitions between **metadata** and actual **legal provisions**.

### What we extract
- **Gazette Info:** Extracts publication volume and date from the header.
- **Entity Resolution:** Identifies the law number and year (e.g., *Law 147 of 2006*).
- **Article Segmentation:** Isolates each article and detects:
  - **Repeated** articles (`مكرر`)
  - **Issuance** articles (`إصدار`)
- **Temporal Versions:** Detects whether an article has:
  - **Original Text**
  - **Final Modified Text**
  
  Captures `final_text_date` to maintain a historical record of amendments.

  ## Data Structure
```bash
{
  "source_file": "قانون - رقم 1.docx",
  "doc_type": "law",
  "law": {
    "law_number": 1,
    "law_year": 2022,
    "issue_date": "2022-01-26",
    "publication_date": "2022-01-26",
    "effective_date": "2022-01-27",
    "title": "تعديل بعض أحكام قانون تنظيم الجامعات الصادر بالقانون رقم 49 لسنة 1972.",
    "gazette_reference": "الجريدة الرسمية 3 مكرر (هـ)"
  },
  "articles": [
    {
      "article_number": "1",
      "article_type": "content",
      "is_repeated": false,
      "original_text": null,
      "final_text": "...يستبد...",
      "final_text_date": null
    },
    {
      "article_number": "2",
      "article_type": "content",
      "is_repeated": false,
      "original_text": null,
      "final_text": "...يستبدل بالعنوان... ",
      "final_text_date": null
    },
    {
      "article_number": "3",
      "article_type": "content",
      "is_repeated": false,
      "original_text": null,
      "final_text": " ... قبل...":,
       "final_text_date": null
    },
    {
      "article_number": "4",
      "article_type": "content",
      "is_repeated": false,
      "original_text": null,
      "final_text": "..ينشر ...":,
      "final_text_date": null
 
    }
  ]
}
}
```

---

## 2) Judgments — `parse_judgment.py`

Court rulings are dense. The parser implements **context-switching** logic to separate narration from legal reasoning.

### What we extract
- **Court Metadata:** Extracts court name (e.g., *Court of Cassation*), case type (Civil/Criminal), and appeal numbers.
- **The Narrative (Facts):** Captures the `الوقائع` section describing the case background.
- **The Reasoning (Reasons):** Extracts `الحيثيات`, the legal basis for the decision.
- **Legal Principles:** The most critical part. The parser identifies and isolates `المبادئ القانونية`.
  - Since one judgment can contain multiple principles, we store them in a **1:N relationship**
  - Each principle becomes **independently searchable**, linked back to the main judgment
 
## Data Structure
```bash
{
  "source_file": "judgment1.docx",
  "judgment": {
    "judgment_id": 1,
    "court_name": "محكمة النقض",
    "case_type": "مدني",
    "appeal_number": 1784,
    "judicial_year": 54,
    "session_date": "1990-01-31",
    "technical_office_number": "41",
    "volume _number": "1",
    "page_number": "366",
    "rule_number": "67",
    "reference_number": "10232",
    "judicial_panel":"...",
    "facts":" .الوقائع.",
    "reasons": "....الإطلاع...."
  },
  "principles": [
    {
      "principle_number": 1,
      "principle_text": "....تنص...."
    }
  ]
}
```
---

## 3) Fatwas — `parse_fatwa.py`

Fatwas are structured differently, often focusing on an **opinion** based on a **request**.

### What we extract
- **Request Info:** Identifies the requesting entity and the subject/question.
- **Date Normalization:** Extracts:
  - **Session Date**
  - **Issue Date**
  
  Converts varied Arabic formats into **ISO-8601 (`YYYY-MM-DD`)** for database integrity.
- **Opinion & Application:** Separates the opinion from how it is applied to the case facts.
## Data Structure
```bash
{
  "source_file": "fatwa1.docx",
   "doc_type": "fatwa",
  "fatwa": {
    "fatwa_number": 99,
    "fatwa_year": 1960,
    "issued_date": "1960-01-30",
    "session_date": "1960-01-13",
    "file_number": null,
    "authority": null,
    "subject": null,
    "facts": null,
    "application": null,
    "opinion": "...انتهى..."
  },
  "principles": [
    {
      "principle_number": 1,
      "principle_text": "...الجرائم.."
    }
  ]
}
```
---

##  Core Parsing Technologies

- **State Tracking (Modes):**  
  The parser maintains a `mode` variable. For example, when it detects `الحيثيات`, it switches to:
  - `mode = "reasons"`
  
  All subsequent lines are appended to the **reasons** field until another header is detected.

- **Arabic Text Cleaning:**  
  A dedicated `clean()` function removes redundant whitespace, non-standard characters, and normalizes Arabic text to improve API search accuracy.

- **Idempotent Loading:**  
  During extraction, we generate a **natural key** (e.g., `Law Year + Law Number`).  
  This allows the system to detect if a document has already been processed and **update existing records** instead of inserting duplicates.



##  Backend API Layer (FastAPI)

The backend is the delivery mechanism of **SynQanun**.  
It transforms structured SQL data into actionable JSON responses. Built with **FastAPI**, it leverages validation and high-performance request handling to support legal data retrieval at scale.

---

## 1) Architectural Highlights

- **Direct SQL Integration:**  
  Uses `pyodbc` to execute optimized SQL queries directly against SQL Server, minimizing ORM overhead.

- **Dynamic Connection Management:**  
  Supports both **Trusted Windows Authentication** and **SQL Server Authentication** via environment variables (e.g., `DB_SERVER`, `DB_NAME`).

- **Parent–Child Integrity:**  
  Detail endpoints are designed to return the main document along with its related entities in a structured hierarchy:
  - Laws → Articles  
  - Judgments → Principles  
  - Fatwas → Principles / Opinion sections

---

## 2) Available Endpoints & Logic

### A) Legislation (Laws)

- **`GET /laws`**  
  Lists all ingested laws.

- **`GET /laws/{id}`** *(deep fetch)*  
  Returns the law metadata plus all related articles from `Law_Article`, ordered by their natural sequence.  
  Includes handling for special cases like **Repeated (`مكرر`)** articles via custom SQL sorting.

---

### B) Court Judgments

- **`GET /judgments`**  
  Supports a global search parameter `q`.

  **Logic:** When `q` is provided, the API performs a multi-column `LIKE` search across:
  - `court_name`
  - `facts`
  - `reasons`

- **`GET /judgments/{id}`**  
  Returns the full judgment details (panel/meta), case **facts**, legal **reasons**, and a list of extracted **Legal Principles** from `Judgment_Principle`.

---

### C) Fatwas (Legal Opinions)

- **`GET /fatwas`**  
  Searchable by **subject** or **authority** name.

- **`GET /fatwas/{id}`**  
  Returns fatwa metadata plus extracted principles/opinions associated with it.

---

## 3) Smart Search Implementation

The search functionality is designed to be scalable:

- **Indexed Lookups:**  
  Optimized to benefit from the indexes and uniqueness constraints defined in `schema.sql`.

- **Natural Language Readiness:**  
  Currently uses `LIKE` for matching, but the schema + API contract are ready for upgrades like:
  - SQL Server **Full-Text Search (FTS)**
  - **Vector Search**
  
  without changing endpoint design.

---
## Data Modeling & Database Schema

The database is designed using a **relational schema (SQL Server)** with a focus on **data integrity** and **high-performance retrieval**.  
We chose a **normalized structure** to reflect the hierarchy of legal documents and avoid duplication at scale.

---

## 1) The Core Entities

The schema is divided into three main document silos, each following a **Parent–Child** relationship.

### A) Legislation Silo (`Law` & `Law_Article`)

- **Parent (`Law`):** Stores law metadata such as:
  - Year
  - Issue date
  - Official Gazette publication reference
- **Child (`Law_Article`):** Stores individual articles.
  - Enables tracking **amendments** at the article level (e.g., **Original** vs **Final** text + effective dates)

---

### B) Judicial Silo (`Judgment` & `Judgment_Principle`)

- **Parent (`Judgment`):** Stores court and case metadata such as:
  - Court name
  - Case type
  - Appeal / reference numbers
- **Child (`Judgment_Principle`):** Captures extracted legal maxims (**principles**).
  - This supports legal research use cases where users need to search for a **rule** independently of the full judgment text.

---

### C) Advisory Silo (`Fatwa` & `Fatwa_Principle`)

- **Parent (`Fatwa`):** Stores metadata such as:
  - Issuing authority
  - Session/issue dates
- **Child (`Fatwa_Principle`):** Stores the core principles extracted from the opinion.
  - Keeps the fatwa content structured and searchable by principle.
## PostgreSQL Mapping (Important Note)

Although the current implementation runs on **MS SQL Server**, the schema is designed to be **fully compatible with PostgreSQL**. To migrate:

- Replace `IDENTITY(1,1)` with:
  - `SERIAL`, **or**
  - `GENERATED ALWAYS AS IDENTITY`

- Map `NVARCHAR(MAX)` to `TEXT`

 The logical relationships (**Parent–Child structure**) and the indexing strategy remain the same.

## Helpful Indexes (Idempotent Loaders)

These unique indexes enforce **natural keys** to prevent duplicates when loaders are re-run, keeping ingestion **idempotent**.

```sql
-- Helpful indexes for idempotent loaders
CREATE UNIQUE INDEX UX_Judgment_ReferenceNumber
ON dbo.Judgment(reference_number)
WHERE reference_number IS NOT NULL;

CREATE UNIQUE INDEX UX_Judgment_FallbackKey
ON dbo.Judgment(appeal_number, judicial_year, session_date)
WHERE appeal_number IS NOT NULL AND judicial_year IS NOT NULL AND session_date IS NOT NULL;

CREATE UNIQUE INDEX UX_Fatwa_NumberYear
ON dbo.Fatwa(fatwa_number, fatwa_year)
WHERE fatwa_number IS NOT NULL AND fatwa_year IS NOT NULL;
