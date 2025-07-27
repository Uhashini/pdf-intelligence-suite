import fitz  # PyMuPDF
import os

def is_valid_title(title):
    title = title.strip()
    if not title or title in {"•", "-", "*"}:
        return False
    if len(title) < 5:
        return False
    return True

def extract_sections_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    sections = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] != 0:
                continue  # Skip non-text blocks

            lines = []
            for line in block["lines"]:
                line_text = " ".join([span["text"] for span in line["spans"]]).strip()
                if line_text:
                    lines.append(line_text)

            if not lines:
                continue

            full_text = " ".join(lines)
            if len(full_text) < 30:
                continue  # Skip very short text

            # Title cleanup and fallback
            title_candidate = lines[0][:80]
            section_title = title_candidate if is_valid_title(title_candidate) else full_text.split(".")[0][:80]

            section = {
                "document": os.path.basename(pdf_path),
                "page": page_num + 1,
                "section_title": section_title,
                "full_text": full_text
            }
            sections.append(section)

    return sections

def extract_all_sections(pdf_folder, filenames):
    all_sections = []
    for file in filenames:
        path = os.path.join(pdf_folder, file)
        if os.path.exists(path):
            sections = extract_sections_from_pdf(path)
            all_sections.extend(sections)
        else:
            print(f"Warning: File not found -> {file}")
    return all_sections
