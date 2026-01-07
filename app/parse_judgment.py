import re
from datetime import datetime
from app.docx_text import docx_paragraphs

HEADINGS = {"الهيئة", "المبادئ القانونية", "الوقائع", "الحيثيات"}


def clean(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[ \t]+", " ", s)
    return s


def parse_date_ar(s: str):
    m = re.search(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})", s)
    if not m:
        return None
    d, mo, y = map(int, m.groups())
    try:
        return datetime(y, mo, d).date().isoformat()
    except:
        return None


def parse_judgment(path: str):
    paras = [clean(p) for p in docx_paragraphs(path) if clean(p)]

    header_block = "\n".join(paras[:12])

    # line1 example: "جمهورية مصر العربية - محكمة النقض - مدني"
    line1 = paras[0] if paras else ""
    parts = [p.strip() for p in line1.split("-") if p.strip()]
    court_name = None
    case_type = None
    if len(parts) >= 3:
        court_name = parts[-2]
        case_type = parts[-1]
    elif len(parts) == 2:
        court_name = parts[1]

    def rx_int(pat):
        m = re.search(pat, header_block)
        return int(m.group(1)) if m else None

    def rx_str(pat):
        m = re.search(pat, header_block)
        return m.group(1).strip() if m else None

    appeal_number = rx_int(r"الطعن\s+رقم\s+(\d+)")
    judicial_year = rx_int(r"لسنة\s+(\d+)")
    session_date = None
    m = re.search(r"تاريخ\s+الجلسة\s*:?\s*([0-9\s/]+)", header_block)
    if m:
        session_date = parse_date_ar(m.group(1))

    technical_office_number = rx_str(r"مكتب\s+فني\s+(\d+)")
    volume_number = rx_str(r"رقم\s+الجزء\s+(\d+)")
    page_number = rx_str(r"رقم\s+الصفحة\s+(\d+)")
    rule_number = rx_str(r"القاعدة\s+رقم\s+(\d+)")
    reference_number = rx_str(r"الرقم\s+المرجعي\s*:\s*(\d+)")

    judicial_panel = None
    principles = []
    facts_parts = []
    reasons_parts = []

    mode = None
    current_principle = None

    for t in paras:
        if t in HEADINGS:
            if t == "الهيئة":
                mode = "panel"
            elif t == "المبادئ القانونية":
                if current_principle:
                    principles.append(current_principle)
                    current_principle = None
                mode = "principles"
            elif t == "الوقائع":
                if current_principle:
                    principles.append(current_principle)
                    current_principle = None
                mode = "facts"
            elif t == "الحيثيات":
                if current_principle:
                    principles.append(current_principle)
                    current_principle = None
                mode = "reasons"
            continue

        if mode == "panel":
            if judicial_panel is None:
                judicial_panel = t
            continue

        if mode == "principles":
            m = re.match(r"مبدأ\s+رقم\s+(\d+)", t)
            if m:
                if current_principle:
                    principles.append(current_principle)
                current_principle = {"principle_number": int(
                    m.group(1)), "principle_text": ""}
            else:
                if current_principle:
                    current_principle["principle_text"] = clean(
                        current_principle["principle_text"] + " " + t)
            continue

        if mode == "facts":
            facts_parts.append(t)
            continue

        if mode == "reasons":
            reasons_parts.append(t)
            continue

    if current_principle:
        principles.append(current_principle)

    judgment = {
        "court_name": court_name,
        "case_type": case_type,
        "appeal_number": appeal_number,
        "judicial_year": judicial_year,
        "session_date": session_date,
        "technical_office_number": technical_office_number,
        "volume_number": volume_number,
        "page_number": page_number,
        "rule_number": rule_number,
        "reference_number": reference_number,
        "judicial_panel": judicial_panel,
        "facts": "\n".join(facts_parts).strip() if facts_parts else None,
        "reasons": "\n".join(reasons_parts).strip() if reasons_parts else None,
    }

    # ✅ لاحظي: مفيش paragraphs ولا full_text في الناتج
    return judgment, principles
