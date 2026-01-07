import os
import glob
import pyodbc

from app.parse_judgment import parse_judgment
from app.parse_fatwa import parse_fatwa
from app.parse_law import parse_law

SERVER = r"MAHOZZ"            
DATABASE = "model"

DATA_DIR = r"./data"


def connect():
    # جرّبي Driver 18 لو موجود عندك بدل 17
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def insert_judgment(cur, j, principles):
    cur.execute("""
        INSERT INTO Judgment (
            court_name, case_type, appeal_number, judicial_year, session_date,
            technical_office_number, volume_number, page_number, rule_number, reference_number,
            judicial_panel, facts, reasons
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        j.get("court_name"), j.get("case_type"), j.get(
            "appeal_number"), j.get("judicial_year"), j.get("session_date"),
        j.get("technical_office_number"), j.get("volume_number"), j.get(
            "page_number"), j.get("rule_number"), j.get("reference_number"),
        j.get("judicial_panel"), j.get("facts"), j.get("reasons")
    ))
    judgment_id = cur.execute("SELECT SCOPE_IDENTITY()").fetchval()

    for p in principles:
        cur.execute("""
            INSERT INTO Judgment_Principle (judgment_id, principle_number, principle_text)
            VALUES (?, ?, ?)
        """, (judgment_id, p.get("principle_number"), p.get("principle_text")))


def insert_fatwa(cur, f, principles, citations):
    cur.execute("""
        INSERT INTO Fatwa (
            fatwa_number, fatwa_year, issued_date, session_date,
            subject, authority, full_text, file_number, facts, application, opinion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f.get("fatwa_number"), f.get("fatwa_year"), f.get(
            "issued_date"), f.get("session_date"),
        f.get("subject"), f.get("authority"), f.get(
            "full_text"), f.get("file_number"),
        f.get("facts"), f.get("application"), f.get("opinion")
    ))
    fatwa_id = cur.execute("SELECT SCOPE_IDENTITY()").fetchval()

    # principles + citations
    principle_id_map = []
    for p in principles:
        cur.execute("""
            INSERT INTO Fatwa_Principle (fatwa_id, principle_number, principle_text)
            VALUES (?, ?, ?)
        """, (fatwa_id, p.get("principle_number"), p.get("principle_text")))
        pid = cur.execute("SELECT SCOPE_IDENTITY()").fetchval()
        principle_id_map.append(pid)

    # citations: list of {principle_index, law_number, law_year, law_article}
    for c in citations:
        idx = c.get("principle_index")
        if idx is None or idx < 0 or idx >= len(principle_id_map):
            continue
        cur.execute("""
            INSERT INTO Fatwa_Principle_Law (principle_id, law_number, law_year, law_article)
            VALUES (?, ?, ?, ?)
        """, (principle_id_map[idx], c.get("law_number"), c.get("law_year"), c.get("law_article")))


def insert_law(cur, law, articles):
    cur.execute("""
        INSERT INTO Law (law_year, issue_date, publication_date, effective_date, title, gazette_reference)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        law.get("law_year"), law.get(
            "issue_date"), law.get("publication_date"),
        law.get("effective_date"), law.get(
            "title"), law.get("gazette_reference")
    ))
    law_id = cur.execute("SELECT SCOPE_IDENTITY()").fetchval()

    for a in articles:
        cur.execute("""
            INSERT INTO Law_Article (
                law_id, article_number, article_type, is_repeated,
                original_text, final_text, final_text_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            law_id, a.get("article_number"), a.get(
                "article_type"), a.get("is_repeated", 0),
            a.get("original_text"), a.get(
                "final_text"), a.get("final_text_date")
        ))


def main():
    conn = connect()
    cur = conn.cursor()

    # judgments
    for path in glob.glob(os.path.join(DATA_DIR, "judgment*.docx")):
        j, principles = parse_judgment(path)
        insert_judgment(cur, j, principles)
        print("Inserted judgment:", os.path.basename(
            path), "principles:", len(principles))

    # fatwas
    for path in glob.glob(os.path.join(DATA_DIR, "fatwa*.docx")):
        f, principles, citations = parse_fatwa(path)
        insert_fatwa(cur, f, principles, citations)
        print("Inserted fatwa:", os.path.basename(path), "principles:",
              len(principles), "citations:", len(citations))

    # laws (files start with قانون)
    for path in glob.glob(os.path.join(DATA_DIR, "قانون*.docx")):
        law, articles = parse_law(path)
        insert_law(cur, law, articles)
        print("Inserted law:", os.path.basename(
            path), "articles:", len(articles))

    conn.commit()
    cur.close()
    conn.close()
    print("DONE")


if __name__ == "__main__":
    main()
