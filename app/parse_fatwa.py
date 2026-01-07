import re
from app.docx_text import docx_paragraphs

SECTION_HEADS = ["الجهة", "موضوع الفتوى", "الوقائع", "التطبيق", "الرأى"]


def _date_any(s: str):
    # يقبل YYYY-MM-DD أو DD/MM/YYYY
    if not s:
        return None
    s = s.strip()
    m = re.search(r"\d{4}-\d{2}-\d{2}", s)
    if m:
        return m.group(0)
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None


def parse_fatwa(path: str):
    paras = [p.strip() for p in docx_paragraphs(path) if p.strip()]
    if not paras:
        return {}, []

    title = paras[0]

    fatwa_number = None
    fatwa_year = None
    issued_date = None
    session_date = None
    file_number = None

    m = re.search(r"الفتوى\s+رقم\s+(\d+)", title)
    if m:
        fatwa_number = int(m.group(1))

    m = re.search(r"لسنة\s+(\d{4})", title)
    if m:
        fatwa_year = int(m.group(1))

    m = re.search(r"رقم\s+الملف\s+([0-9/]+)", title)
    if m:
        file_number = m.group(1).strip()

    m = re.search(r"بتاريخ\s+([0-9\-\/]+)", title)
    if m:
        issued_date = _date_any(m.group(1))

    m = re.search(r"تاريخ\s+الجلسة\s+([0-9\-\/]+)", title)
    if m:
        session_date = _date_any(m.group(1))

    # sections + principles
    sections = {k: "" for k in ["authority",
                                "subject", "facts", "application", "opinion"]}
    principles = []
    mode = None
    current_principle = None

    i = 1
    while i < len(paras):
        t = paras[i]

        # headings
        if t in SECTION_HEADS:
            # close any open principle
            if current_principle:
                principles.append(current_principle)
                current_principle = None

            if t == "الجهة":
                mode = "authority"
            elif t == "موضوع الفتوى":
                mode = "subject"
            elif t == "الوقائع":
                mode = "facts"
            elif t == "التطبيق":
                mode = "application"
            elif t == "الرأى":
                mode = "opinion"
            i += 1
            continue

        # principle header like: "مبدأ 1" or "مبدأ رقم 1"
        pm = re.match(r"^مبدأ(?:\s+رقم)?\s+(\d+)\s*$", t)
        if pm:
            if current_principle:
                principles.append(current_principle)
            current_principle = {"principle_number": int(
                pm.group(1)), "principle_text": ""}
            mode = "principle"
            i += 1
            continue

        # collect text
        if mode == "principle" and current_principle:
            current_principle["principle_text"] = (
                current_principle["principle_text"] + " " + t).strip()
        elif mode in sections:
            sections[mode] = (sections[mode] + " " + t).strip()

        i += 1

    if current_principle:
        principles.append(current_principle)

    fatwa = {
        "fatwa_number": fatwa_number,
        "fatwa_year": fatwa_year,
        "issued_date": issued_date,
        "session_date": session_date,
        "file_number": file_number,
        "authority": sections["authority"] or None,
        "subject": sections["subject"] or None,
        "facts": sections["facts"] or None,
        "application": sections["application"] or None,
        "opinion": sections["opinion"] or None,
    }

    return fatwa, principles
