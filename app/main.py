import os
import pyodbc
from fastapi import FastAPI, Query, HTTPException


DB_SERVER = os.getenv("DB_SERVER", r"MAHOZZ\SQLEXPRESS")
DB_NAME = os.getenv("DB_NAME", "model")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")




def connect():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        "TrustServerCertificate=yes;"
    )
    if DB_USER and DB_PASSWORD:
        conn_str += f"UID={DB_USER};PWD={DB_PASSWORD};"
    else:
        conn_str += "Trusted_Connection=yes;"
    return pyodbc.connect(conn_str)


app = FastAPI(title="SynQanun API")


@app.get("/")
def home():
    return {
        "service": "SynQanun API",
        "docs": "/docs",
        "health": "/health"
    }



# ------------------------- Judgments -------------------------

@app.get("/judgments")
def list_judgments(q: str | None = Query(default=None, description="Search term")):
    """
    List judgments. If q is provided, performs a simple LIKE search across key fields.
    """
    conn = connect()
    cur = conn.cursor()

    if q:
        like = f"%{q}%"
        rows = cur.execute(
            """
            SELECT TOP 100
                judgment_id, reference_number, appeal_number, judicial_year,
                session_date, court_name, case_type
            FROM dbo.Judgment
            WHERE
                reference_number LIKE ?
                OR court_name LIKE ?
                OR facts LIKE ?
                OR reasons LIKE ?
            ORDER BY judgment_id DESC
            """,
            like, like, like, like
        ).fetchall()
    else:
        rows = cur.execute(
            """
            SELECT TOP 100
                judgment_id, reference_number, appeal_number, judicial_year,
                session_date, court_name, case_type
            FROM dbo.Judgment
            ORDER BY judgment_id DESC
            """
        ).fetchall()

    conn.close()

    result = []
    for r in rows:
        result.append({
            "judgment_id": r[0],
            "reference_number": r[1],
            "appeal_number": r[2],
            "judicial_year": r[3],
            "session_date": r[4].isoformat() if r[4] else None,
            "court_name": r[5],
            "case_type": r[6],
        })
    return result


@app.get("/judgments/{judgment_id}")
def get_judgment(judgment_id: int):
    """
    Fetch a single judgment with its principles.
    """
    conn = connect()
    cur = conn.cursor()

    j = cur.execute(
        """
        SELECT
            judgment_id, court_name, case_type, appeal_number, judicial_year, session_date,
            technical_office_number, volume_number, page_number, rule_number, reference_number,
            judicial_panel, facts, reasons
        FROM dbo.Judgment
        WHERE judgment_id = ?
        """,
        judgment_id
    ).fetchone()

    if not j:
        conn.close()
        raise HTTPException(status_code=404, detail="Judgment not found")

    principles = cur.execute(
        """
        SELECT principle_number, principle_text
        FROM dbo.Judgment_Principle
        WHERE judgment_id = ?
        ORDER BY principle_number
        """,
        judgment_id
    ).fetchall()

    conn.close()

    return {
        "judgment": {
            "judgment_id": j[0],
            "court_name": j[1],
            "case_type": j[2],
            "appeal_number": j[3],
            "judicial_year": j[4],
            "session_date": j[5].isoformat() if j[5] else None,
            "technical_office_number": j[6],
            "volume_number": j[7],
            "page_number": j[8],
            "rule_number": j[9],
            "reference_number": j[10],
            "judicial_panel": j[11],
            "facts": j[12],
            "reasons": j[13],
        },
        "principles": [{"principle_number": p[0], "principle_text": p[1]} for p in principles],
    }


# ------------------------- Fatwas -------------------------

@app.get("/fatwas")
def list_fatwas(q: str | None = Query(default=None, description="Search term")):
    """
    List fatwas. If q is provided, performs a simple LIKE search across key fields.
    """
    conn = connect()
    cur = conn.cursor()

    if q:
        like = f"%{q}%"
        rows = cur.execute(
            """
            SELECT TOP 100
                fatwa_id, fatwa_number, fatwa_year, issued_date, session_date,
                subject, authority, file_number
            FROM dbo.Fatwa
            WHERE
                subject LIKE ?
                OR authority LIKE ?
                OR facts LIKE ?
                OR opinion LIKE ?
            ORDER BY fatwa_id DESC
            """,
            like, like, like, like
        ).fetchall()
    else:
        rows = cur.execute(
            """
            SELECT TOP 100
                fatwa_id, fatwa_number, fatwa_year, issued_date, session_date,
                subject, authority, file_number
            FROM dbo.Fatwa
            ORDER BY fatwa_id DESC
            """
        ).fetchall()

    conn.close()

    result = []
    for r in rows:
        result.append({
            "fatwa_id": r[0],
            "fatwa_number": r[1],
            "fatwa_year": r[2],
            "issued_date": r[3].isoformat() if r[3] else None,
            "session_date": r[4].isoformat() if r[4] else None,
            "subject": r[5],
            "authority": r[6],
            "file_number": r[7],
        })
    return result


@app.get("/fatwas/{fatwa_id}")
def get_fatwa(fatwa_id: int):
    """
    Fetch a single fatwa with its principles.
    """
    conn = connect()
    cur = conn.cursor()

    f = cur.execute(
        """
        SELECT
            fatwa_id, fatwa_number, fatwa_year, issued_date, session_date, file_number,
            subject, authority, facts, application, opinion
        FROM dbo.Fatwa
        WHERE fatwa_id = ?
        """,
        fatwa_id
    ).fetchone()

    if not f:
        conn.close()
        raise HTTPException(status_code=404, detail="Fatwa not found")

    principles = cur.execute(
        """
        SELECT principle_number, principle_text
        FROM dbo.Fatwa_Principle
        WHERE fatwa_id = ?
        ORDER BY principle_number
        """,
        fatwa_id
    ).fetchall()

    conn.close()

    return {
        "fatwa": {
            "fatwa_id": f[0],
            "fatwa_number": f[1],
            "fatwa_year": f[2],
            "issued_date": f[3].isoformat() if f[3] else None,
            "session_date": f[4].isoformat() if f[4] else None,
            "file_number": f[5],
            "subject": f[6],
            "authority": f[7],
            "facts": f[8],
            "application": f[9],
            "opinion": f[10],
        },
        "principles": [{"principle_number": p[0], "principle_text": p[1]} for p in principles],
    }


# ------------------------- Laws -------------------------

@app.get("/laws")
def list_laws(q: str | None = Query(default=None, description="Search term")):
    """
    List laws. If q is provided, searches on the title/gazette reference.
    """
    conn = connect()
    cur = conn.cursor()

    if q:
        like = f"%{q}%"
        rows = cur.execute(
            """
            SELECT TOP 100
                law_id, law_year, issue_date, publication_date, effective_date, title,gazette_reference
            FROM dbo.Law
            WHERE title LIKE ? OR gazette_reference LIKE ?
            ORDER BY law_id DESC
            """,
            like, like
        ).fetchall()
    else:
        rows = cur.execute(
            """
            SELECT TOP 100
                law_id, law_year, issue_date, publication_date, effective_date, title, gazette_reference
            FROM dbo.Law
            ORDER BY law_id DESC
            """
        ).fetchall()

    conn.close()

    result = []
    for r in rows:
        result.append({
            "law_id": r[0],
            "law_year": r[1],
            "issue_date": r[2].isoformat() if r[2] else None,
            "publication_date": r[3].isoformat() if r[3] else None,
            "effective_date": r[4].isoformat() if r[4] else None,
            "title": r[5],
            "gazette_reference": r[6],

        })
    return result


@app.get("/laws/{law_id}")
def get_law(law_id: int):
    """
    Fetch a single law with its articles.
    """
    conn = connect()
    cur = conn.cursor()

    l = cur.execute(
        """
        SELECT law_id, law_year, issue_date, publication_date, effective_date, title, gazette_reference
        FROM dbo.Law
        WHERE law_id = ?
        """,
        law_id
    ).fetchone()

    if not l:
        conn.close()
        raise HTTPException(status_code=404, detail="Law not found")

    articles = cur.execute(
        """
        SELECT article_number, article_type, is_repeated, original_text, final_text, final_text_date
        FROM dbo.Law_Article
        WHERE law_id = ?
        ORDER BY
          TRY_CONVERT(int, REPLACE(article_number, N' مكرر', '')),
          article_number
        """,
        law_id
    ).fetchall()

    conn.close()

    return {
        "law": {
            "law_id": l[0],
            "law_year": l[1],
            "issue_date": l[2].isoformat() if l[2] else None,
            "publication_date": l[3].isoformat() if l[3] else None,
            "effective_date": l[4].isoformat() if l[4] else None,
            "title": l[5],
            "gazette_reference": l[6],
        },
        "articles": [
            {
                "article_number": a[0],
                "article_type": a[1],
                "is_repeated": bool(a[2]),
                "original_text": a[3],
                "final_text": a[4],
                "final_text_date": a[5].isoformat() if a[5] else None,
            }
            for a in articles
        ],
    }
