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
    with open("loader_fatwa.log", "a", encoding="utf-8") as f:
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


def find_existing_fatwa_id(cur, f: dict):
    # Preferred key: (fatwa_number, fatwa_year)
    num = f.get("fatwa_number")
    yr = f.get("fatwa_year")
    if num is not None and yr is not None:
        row = cur.execute(
            "SELECT fatwa_id FROM dbo.Fatwa WHERE fatwa_number = ? AND fatwa_year = ?",
            num, yr
        ).fetchone()
        if row:
            return int(row[0])

    # Fallback: file_number (often unique)
    file_no = f.get("file_number")
    if file_no:
        row = cur.execute(
            "SELECT fatwa_id FROM dbo.Fatwa WHERE file_number = ?",
            file_no
        ).fetchone()
        if row:
            return int(row[0])

    return None


def insert_fatwa(cur, f: dict) -> int:
    row = cur.execute(
        """
        INSERT INTO dbo.Fatwa (
            fatwa_number, fatwa_year, issued_date, session_date,
            subject, authority, full_text, file_number,
            facts, application, opinion
        )
        OUTPUT INSERTED.fatwa_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f.get("fatwa_number"),
            f.get("fatwa_year"),
            f.get("issued_date"),
            f.get("session_date"),
            f.get("subject"),
            f.get("authority"),
            None,  # full_text not used in the clean JSON output
            f.get("file_number"),
            f.get("facts"),
            f.get("application"),
            f.get("opinion"),
        )
    ).fetchone()
    return int(row[0])


def update_fatwa(cur, fatwa_id: int, f: dict):
    cur.execute(
        """
        UPDATE dbo.Fatwa SET
            fatwa_number = ?, fatwa_year = ?, issued_date = ?, session_date = ?,
            subject = ?, authority = ?, full_text = ?, file_number = ?,
            facts = ?, application = ?, opinion = ?
        WHERE fatwa_id = ?
        """,
        (
            f.get("fatwa_number"),
            f.get("fatwa_year"),
            f.get("issued_date"),
            f.get("session_date"),
            f.get("subject"),
            f.get("authority"),
            None,  # full_text not used
            f.get("file_number"),
            f.get("facts"),
            f.get("application"),
            f.get("opinion"),
            fatwa_id,
        )
    )


def replace_fatwa_principles(cur, fatwa_id: int, principles: list[dict]) -> int:
    # Remove old principles to keep the operation idempotent
    cur.execute("DELETE FROM dbo.Fatwa_Principle WHERE fatwa_id = ?", fatwa_id)

    inserted = 0
    for p in principles:
        cur.execute(
            """
            INSERT INTO dbo.Fatwa_Principle (fatwa_id, principle_number, principle_text)
            VALUES (?, ?, ?)
            """,
            (fatwa_id, p.get("principle_number"), p.get("principle_text"))
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

        if data.get("doc_type") != "fatwa":
            continue

        fatwa = data.get("fatwa", {}) or {}
        principles = data.get("principles", []) or []

        existing_id = find_existing_fatwa_id(cur, fatwa)

        if existing_id is None:
            fatwa_id = insert_fatwa(cur, fatwa)
            log(f"INSERT Fatwa id={fatwa_id} num={fatwa.get('fatwa_number')} year={fatwa.get('fatwa_year')}")
        else:
            fatwa_id = existing_id
            update_fatwa(cur, fatwa_id, fatwa)
            log(f"UPDATE Fatwa id={fatwa_id} num={fatwa.get('fatwa_number')} year={fatwa.get('fatwa_year')}")

        cnt = replace_fatwa_principles(cur, fatwa_id, principles)
        log(f"REPLACE Fatwa_Principle count={cnt} for fatwa_id={fatwa_id}")

    conn.commit()
    cur.close()
    conn.close()
    log("DONE")


if __name__ == "__main__":
    main()
