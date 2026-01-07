from zipfile import ZipFile
import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def docx_paragraphs(path: str) -> list[str]:
    """
    Extract paragraphs (roughly) from a .docx without external libs.
    """
    with ZipFile(path) as z:
        xml = z.read("word/document.xml")

    root = ET.fromstring(xml)

    paras = []
    for p in root.findall(".//w:p", NS):
        texts = []
        for t in p.findall(".//w:t", NS):
            if t.text:
                texts.append(t.text)
        para_text = "".join(texts).strip()
        if para_text:
            paras.append(para_text)
    return paras


def docx_text(path: str) -> str:
    """
    Extract all text from the .docx file, returns it as a single string.
    """
    return "\n".join(docx_paragraphs(path))


def extract_text_for_all(path: str):
    """
    A unified function that extracts text for law, judgment, and fatwa documents.
    """
    paragraphs = docx_paragraphs(path)

    # Define the type based on the first few lines or headings (example approach)
    first_paragraph = paragraphs[0] if paragraphs else ""

    if "قانون" in first_paragraph:
        return "Law Document", paragraphs
    elif "الطعن" in first_paragraph:
        return "Judgment Document", paragraphs
    elif "الفتوى" in first_paragraph:
        return "Fatwa Document", paragraphs
    else:
        return "Unknown Document Type", paragraphs
