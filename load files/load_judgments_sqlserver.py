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
    with open("loader.log", "a", encoding="utf-8") as f:
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


def find_existing_judgment_id(cur, j: dict):
    # 1) reference_number if available
    ref = j.get("reference_number")
    if ref:
        row = cur.execute(
            "SELECT judgment_id FROM dbo.Judgment WHERE reference_number = ?",
            ref
        ).fetchone()
        if row:
            return int(row[0])

    # 2) fallback: (appeal_number, judicial_year, session_date)
    appeal = j.get("appeal_number")
    year = j.get("judicial_year")
    date = j.get("session_date")
    if appeal and year and date:
        row = cur.execute(
            """
            SELECT judgment_id
            FROM dbo.Judgment
            WHERE appeal_number = ? AND judicial_year = ? AND session_date = ?
            """,
            appeal, year, date
        ).fetchone()
        if row:
            return int(row[0])

    return None


def insert_judgment(cur, j: dict) -> int:
    # OUTPUT INSERTED.judgment_id guarantees we get the identity value
    row = cur.execute(
        """
        INSERT INTO dbo.Judgment (
            court_name, case_type, appeal_number, judicial_year, session_date,
            technical_office_number, volume_number, page_number, rule_number, reference_number,
            judicial_panel, facts, reasons
        )
        OUTPUT INSERTED.judgment_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            j.get("court_name"),
            j.get("case_type"),
            j.get("appeal_number"),
            j.get("judicial_year"),
            j.get("session_date"),
            j.get("technical_office_number"),
            j.get("volume_number"),
            j.get("page_number"),
            j.get("rule_number"),
            j.get("reference_number"),
            j.get("judicial_panel"),
            j.get("facts"),
            j.get("reasons"),
        )
    ).fetchone()

    return int(row[0])


def update_judgment(cur, judgment_id: int, j: dict):
    cur.execute(
        """
        UPDATE dbo.Judgment SET
            court_name = ?, case_type = ?, appeal_number = ?, judicial_year = ?, session_date = ?,
            technical_office_number = ?, volume_number = ?, page_number = ?, rule_number = ?, reference_number = ?,
            judicial_panel = ?, facts = ?, reasons = ?
        WHERE judgment_id = ?
        """,
        (
            j.get("court_name"),
            j.get("case_type"),
            j.get("appeal_number"),
            j.get("judicial_year"),
            j.get("session_date"),
            j.get("technical_office_number"),
            j.get("volume_number"),
            j.get("page_number"),
            j.get("rule_number"),
            j.get("reference_number"),
            j.get("judicial_panel"),
            j.get("facts"),
            j.get("reasons"),
            judgment_id,
        )
    )


def replace_principles(cur, judgment_id: int, principles: list[dict]):
    # delete old
    cur.execute(
        "DELETE FROM dbo.Judgment_Principle WHERE judgment_id = ?",
        judgment_id
    )

    # insert new
    inserted = 0
    for p in principles:
        cur.execute(
            """
            INSERT INTO dbo.Judgment_Principle (judgment_id, principle_number, principle_text)
            VALUES (?, ?, ?)
            """,
            (
                judgment_id,
                p.get("principle_number"),
                p.get("principle_text"),
            )
        )
        inserted += 1

    return inserted


def upsert_judgment(cur, j: dict, principles: list[dict]) -> int:
    existing_id = find_existing_judgment_id(cur, j)

    if existing_id is None:
        judgment_id = insert_judgment(cur, j)
        log(f"INSERT Judgment id={judgment_id} ref={j.get('reference_number')}")
    else:
        judgment_id = existing_id
        update_judgment(cur, judgment_id, j)
        log(f"UPDATE Judgment id={judgment_id} ref={j.get('reference_number')}")

    inserted = replace_principles(cur, judgment_id, principles)
    log(f"REPLACE principles count={inserted} for judgment_id={judgment_id}")

    return judgment_id


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

        # Only process judgment JSON files
        if data.get("doc_type") != "judgment":
            continue

        j = data.get("judgment", {}) or {}
        principles = data.get("principles", []) or []

        # Skip invalid/empty payloads (prevents NULL-row inserts)
        if not j:
            log(f"SKIP empty judgment payload in {os.path.basename(fp)}")
            continue

        ref = (j.get("reference_number") or "").strip() if j.get(
            "reference_number") is not None else None
        appeal = j.get("appeal_number")
        year = j.get("judicial_year")
        sdate = (j.get("session_date") or "").strip() if j.get(
            "session_date") is not None else None

        # If there is no stable key, skip to keep idempotency guaranteed
        if not ref and not (appeal is not None and year is not None and sdate):
            log(f"SKIP (no stable key) in {os.path.basename(fp)}")
            continue

        if not ref:
            log(
                f"ASSUMPTION: no reference_number in {os.path.basename(fp)} -> using fallback key")

        upsert_judgment(cur, j, principles)

    conn.commit()
    cur.close()
    conn.close()
    log("DONE")

if __name__ == "__main__":
    main()
