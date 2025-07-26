import os
import json
import fitz  # PyMuPDF
from collections import Counter, defaultdict

INPUT_DIR = '/app/input'
OUTPUT_DIR = '/app/output'

# Helper to flatten and sort font sizes for heading detection
def get_font_size_hierarchy(font_sizes):
    # Sort by frequency (descending), then by size (descending)
    freq = Counter(font_sizes)
    sorted_sizes = sorted(freq.items(), key=lambda x: (-x[1], -x[0]))
    return [size for size, _ in sorted_sizes]

# Extract headings and title from a PDF
def extract_outline_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_blocks = []
    font_sizes = []
    for page_num, page in enumerate(doc, 1):
        blocks = page.get_text("dict")['blocks']
        for block in blocks:
            if block['type'] != 0:
                continue  # skip images, etc.
            for line in block['lines']:
                for span in line['spans']:
                    text = span['text'].strip()
                    if not text:
                        continue
                    font_size = span['size']
                    font_name = span['font']
                    is_bold = 'Bold' in font_name or 'bold' in font_name
                    bbox = span['bbox']
                    text_blocks.append({
                        'text': text,
                        'font_size': font_size,
                        'is_bold': is_bold,
                        'page': page_num,
                        'bbox': bbox
                    })
                    font_sizes.append(font_size)

    if not text_blocks:
        return {"title": "", "outline": []}

    # Determine font size hierarchy (largest = title/H1)
    unique_sizes = sorted(set(font_sizes), reverse=True)
    if len(unique_sizes) == 1:
        # All text same size, fallback to bold or position
        h1_size, h2_size, h3_size = unique_sizes[0], unique_sizes[0], unique_sizes[0]
    else:
        h1_size = unique_sizes[0]
        h2_size = unique_sizes[1] if len(unique_sizes) > 1 else unique_sizes[0]
        h3_size = unique_sizes[2] if len(unique_sizes) > 2 else unique_sizes[-1]

    # Extract title: largest text on first page, near top
    title_candidates = [b for b in text_blocks if b['page'] == 1 and b['font_size'] == h1_size]
    if title_candidates:
        # Prefer text near the top of the page
        title = sorted(title_candidates, key=lambda b: b['bbox'][1])[0]['text']
    else:
        # Fallback: first large text on first page
        title = text_blocks[0]['text']

    # Extract headings
    outline = []
    for b in text_blocks:
        level = None
        if b['font_size'] == h1_size and b['is_bold']:
            level = 'H1'
        elif b['font_size'] == h2_size and b['is_bold']:
            level = 'H2'
        elif b['font_size'] == h3_size and b['is_bold']:
            level = 'H3'
        # Fallback: if not enough bold, use font size only
        elif b['font_size'] == h1_size and not b['is_bold']:
            level = 'H1'
        elif b['font_size'] == h2_size and not b['is_bold']:
            level = 'H2'
        elif b['font_size'] == h3_size and not b['is_bold']:
            level = 'H3'
        if level:
            outline.append({
                "level": level,
                "text": b['text'],
                "page": b['page']
            })

    # Remove duplicate headings (same text, same page, same level)
    seen = set()
    unique_outline = []
    for item in outline:
        key = (item['level'], item['text'], item['page'])
        if key not in seen:
            unique_outline.append(item)
            seen.add(key)

    return {
        "title": title,
        "outline": unique_outline
    }

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(INPUT_DIR, filename)
            outline = extract_outline_from_pdf(pdf_path)
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(outline, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main() 