import re
from app.docx_text import docx_paragraphs


def _date_any(s: str):
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
    m = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None


def parse_law(path: str):
    paras = [p.strip() for p in docx_paragraphs(path) if p.strip()]
    if not paras:
        return {}, []

    title_line = paras[0]
    gazette = None
    subject = None

    # البحث عن "الجريدة الرسمية" وفصلها عن العنوان
    gazette_match = re.search(r"(الجريدة الرسمية.*?)(\d.*)", title_line)
    if gazette_match:
        gazette = gazette_match.group(0)
        title_line = title_line.replace(gazette, "").strip()

    # استخراج البيانات الخاصة بالقانون
    law_number = None
    law_year = None
    issue_date = None
    publication_date = None
    effective_date = None

    m = re.search(r"قانون\s*-\s*رقم\s*(\d+)", title_line)
    if m:
        law_number = int(m.group(1))

    m = re.search(r"لسنة\s*(\d{4})", title_line)
    if m:
        law_year = int(m.group(1))

    m = re.search(r"الصادر\s+بتاريخ\s+([0-9\-\/]+)", title_line)
    if m:
        issue_date = _date_any(m.group(1))

    m = re.search(r"نشر\s+بتاريخ\s+([0-9\-\/]+)", title_line)
    if m:
        publication_date = _date_any(m.group(1))

    m = re.search(r"يعمل\s+به\s+إ?عتبارا\s+من\s+([0-9\-\/]+)", title_line)
    if m:
        effective_date = _date_any(m.group(1))

    m = re.search(r"بشأن\s+(.+)$", title_line)
    if m:
        subject = m.group(1).strip()

    # لو "بشأن ..." مش في أول سطر، دور في باقي السطور
    if not subject:
        for p in paras[:20]:
            if p.startswith("بشأن"):
                subject = p.replace("بشأن", "", 1).strip()
                break

    law = {
        "law_number": law_number,
        "law_year": law_year,
        "issue_date": issue_date,
        "publication_date": publication_date,
        "effective_date": effective_date,
        "title": subject,
        "gazette_reference": gazette,
    }

    # --------- Articles ---------
    articles = []
    current = None

    def flush():
        nonlocal current
        if current:
            for k in ["original_text", "final_text"]:
                if current.get(k):
                    current[k] = current[k].strip()
            articles.append(current)
            current = None

    # ✅ تعديل مهم:
    # - يقبل "المادة" أو "مادة"
    # - article_type issuance فقط لو العنوان فيه "اصدار"
    # - repeated لو "مكرر"
    art_header = re.compile(r"^(?:المادة|مادة)\s+(\d+)(?:\s+(اصدار|مكرر))?$")

    for p in paras:
        # "مواد إصدار" هنعتبره مجرد عنوان/فاصل، مش هيحوّل كل اللي بعده issuance
        if p.strip() == "مواد إصدار":
            continue

        m = art_header.match(p.strip())
        if m:
            flush()
            num = m.group(1)
            tag = m.group(2)  # اصدار أو مكرر أو None

            is_repeated = (tag == "مكرر")
            article_type = "issuance" if tag == "اصدار" else "content"

            current = {
                "article_number": num,
                "article_type": article_type,
                "is_repeated": bool(is_repeated),
                "original_text": None,
                "final_text": "",
                "final_text_date": None,
            }
            continue

        if not current:
            continue

        # final_text_date
        if "النص النهائى للمادة بتاريخ" in p:
            dm = re.search(r"(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})", p)
            if dm:
                current["final_text_date"] = _date_any(dm.group(1))
            continue

        # original_text
        if p.startswith("النص الاصلى للمادة"):
            txt = p.replace("النص الاصلى للمادة", "", 1).strip()
            current["original_text"] = (current["original_text"] or "")
            current["original_text"] = (
                current["original_text"] + " " + txt).strip()
            continue

        # normal content -> final_text
        current["final_text"] = (current["final_text"] + " " + p).strip()

    flush()
    return law, articles
