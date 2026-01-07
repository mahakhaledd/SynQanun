import os
import glob
import json
import pyodbc
from datetime import datetime

SERVER = r"MAHOZZ\SQLEXPRESS"
DATABASE = "model"
JSON_DIR = r"json_clean_all"  


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open("loader_law.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def connect():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def find_existing_law_id(cur, law: dict):
    """
    Find an existing Law row using a stable natural key.
    NOTE: schema does not include a law_number column, so we use (law_year, issue_date, title).
    """
    year = law.get("law_year")
    title = law.get("title")
    issue_date = law.get("issue_date")

    if year and title and issue_date:
        row = cur.execute(
            """
            SELECT law_id FROM dbo.Law
            WHERE law_year = ? AND issue_date = ? AND title = ?
            """,
            year, issue_date, title
        ).fetchone()
        if row:
            return int(row[0])

    if year and title:
        row = cur.execute(
            """
            SELECT law_id FROM dbo.Law
            WHERE law_year = ? AND title = ?
            """,
            year, title
        ).fetchone()
        if row:
            return int(row[0])

    return None


def insert_law(cur, law: dict) -> int:
    row = cur.execute(
        """
        INSERT INTO dbo.Law (
            law_year, issue_date, publication_date, effective_date,
            title, gazette_reference
        )
        OUTPUT INSERTED.law_id
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            law.get("law_year"),
            law.get("issue_date"),
            law.get("publication_date"),
            law.get("effective_date"),
            law.get("title"),
            law.get("gazette_reference"),
        )
    ).fetchone()
    return int(row[0])


def update_law(cur, law_id: int, law: dict):
    cur.execute(
        """
        UPDATE dbo.Law SET
            law_year = ?, issue_date = ?, publication_date = ?, effective_date = ?,
            title = ?, gazette_reference = ?
        WHERE law_id = ?
        """,
        (
            law.get("law_year"),
            law.get("issue_date"),
            law.get("publication_date"),
            law.get("effective_date"),
            law.get("title"),
            law.get("gazette_reference"),
            law_id,
        )
    )


def replace_articles(cur, law_id: int, articles: list[dict]) -> int:
    """
    Idempotent article load:
    - delete existing articles for this law
    - insert the current set
    Includes an in-memory dedup guard to avoid UNIQUE(law_id, article_number, article_type) conflicts.
    """
    cur.execute("DELETE FROM dbo.Law_Article WHERE law_id = ?", law_id)

    seen = set()
    inserted = 0

    for a in articles:
        article_number = str(a.get("article_number"))
        article_type = a.get("article_type")

        key = (article_number, article_type)
        if key in seen:
            log(f"SKIP duplicate article key={key} for law_id={law_id}")
            continue
        seen.add(key)

        cur.execute(
            """
            INSERT INTO dbo.Law_Article (
                law_id, article_number, article_type, is_repeated,
                original_text, final_text, final_text_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                law_id,
                article_number,
                article_type,
                1 if a.get("is_repeated") else 0,
                a.get("original_text"),
                a.get("final_text"),
                a.get("final_text_date"),
            )
        )
        inserted += 1

    return inserted


def main():
    conn = connect()
    cur = conn.cursor()

    files = sorted(glob.glob(os.path.join(JSON_DIR, "*.json")))
    if not files:
        log(f"No json files found in {JSON_DIR}")
        return

    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("doc_type") != "law":
            continue

        law = data.get("law", {}) or {}
        articles = data.get("articles", []) or []

        existing_id = find_existing_law_id(cur, law)

        if existing_id is None:
            law_id = insert_law(cur, law)
            log(
                f"INSERT Law id={law_id} year={law.get('law_year')} title={(law.get('title') or '')[:60]}")
        else:
            law_id = existing_id
            update_law(cur, law_id, law)
            log(
                f"UPDATE Law id={law_id} year={law.get('law_year')} title={(law.get('title') or '')[:60]}")

        cnt = replace_articles(cur, law_id, articles)
        log(f"REPLACE Law_Article count={cnt} for law_id={law_id}")

    conn.commit()
    cur.close()
    conn.close()
    log("DONE")


if __name__ == "__main__":
    main()
