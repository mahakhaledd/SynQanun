import os
import json
import glob
import hashlib

from app.parse_judgment import parse_judgment
from app.parse_fatwa import parse_fatwa
from app.parse_law import parse_law

INPUT_DIR = r"C:\Users\Menna\Downloads\SynQanun\legal_loader"
OUT_DIR = r"json_clean_all"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def doc_type_from_name(filename: str) -> str:
    low = filename.lower()
    if "judgment" in low or "حكم" in filename:
        return "judgment"
    if "fatwa" in low or "فتوى" in filename:
        return "fatwa"
    if "law" in low or "قانون" in filename:
        return "law"
    return "unknown"


def export_one(docx_path: str):
    name = os.path.basename(docx_path)
    doc_type = doc_type_from_name(name)

    out = {
        "source_file": name,
        "sha256": sha256_file(docx_path),
        "doc_type": doc_type,
    }

    if doc_type == "judgment":
        j, principles = parse_judgment(docx_path)
        out["judgment"] = j
        out["principles"] = principles

    elif doc_type == "fatwa":
        f, principles = parse_fatwa(docx_path)
        out["fatwa"] = f
        out["principles"] = principles

    elif doc_type == "law":
        law, articles = parse_law(docx_path)
        out["law"] = law
        out["articles"] = articles

    else:
        # لو ملف مش معروف اسمه، بنسيبه بس metadata عشان ما نطلعش نص خام
        out["note"] = "unknown doc type by filename; rename file to include judgment/fatwa/law or حكم/فتوى/قانون"

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, os.path.splitext(name)[0] + ".json")

    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    print("Saved:", out_path)


def main():
    files = glob.glob(os.path.join(INPUT_DIR, "**", "*.docx"), recursive=True)
    files = [p for p in files if not os.path.basename(p).startswith("~$")]

    if not files:
        print("No docx found in:", INPUT_DIR)
        return

    for p in sorted(files):
        export_one(p)

    print("DONE. Output:", OUT_DIR)


if __name__ == "__main__":
    main()
