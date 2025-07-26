import os
import json
import fitz  # PyMuPDF
from collections import Counter
import re

INPUT_DIR = '/app/input'
OUTPUT_DIR = '/app/output'

def is_heading(text, font_size, body_font_size, is_bold, font_name):
    if len(text) < 3:
        return False
    if re.fullmatch(r'[-_]+', text):
        return False
    if font_size > body_font_size:
        return True
    if is_bold and font_size >= body_font_size:
        return True
    if text.isupper() and font_size >= body_font_size:
        return True
    if re.match(r'^\d+(\.\d+)*\s+.*', text):
        return True
    if font_name.lower().find('bold') != -1 and font_size >= body_font_size:
        return True
    return False

def is_valid_title(text):
    return re.search(r'[A-Za-z0-9]{3,}', text) is not None

def is_document_title_candidate(text):
    keywords = [
        'application', 'form', 'grant', 'advance', 'report', 'proposal', 'certificate',
        'request', 'statement', 'summary', 'plan', 'notice', 'order', 'agreement'
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords) and len(text) > 8

def extract_outline_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_blocks = []
    font_sizes = []
    for page_num, page in enumerate(doc, 1):
        blocks = page.get_text("dict")['blocks']
        for block in blocks:
            if block['type'] != 0:
                continue
            for line in block['lines']:
                merged_spans = []
                prev_span = None
                for span in line['spans']:
                    text = span['text'].strip()
                    if not text:
                        continue
                    font_size = span['size']
                    font_name = span['font']
                    is_bold = 'Bold' in font_name or 'bold' in font_name
                    bbox = span['bbox']
                    if prev_span and abs(bbox[1] - prev_span['bbox'][1]) < 3:  # close vertically
                        # Merge even if font/style is slightly different
                        prev_span['text'] += ' ' + text
                        prev_span['bbox'] = [
                            min(prev_span['bbox'][0], bbox[0]),
                            min(prev_span['bbox'][1], bbox[1]),
                            max(prev_span['bbox'][2], bbox[2]),
                            max(prev_span['bbox'][3], bbox[3])
                        ]
                        prev_span['font_size'] = max(prev_span['font_size'], font_size)
                        prev_span['is_bold'] = prev_span['is_bold'] or is_bold
                    else:
                        if prev_span:
                            merged_spans.append(prev_span)
                        prev_span = {
                            'text': text,
                            'font_size': font_size,
                            'is_bold': is_bold,
                            'font_name': font_name,
                            'page': page_num,
                            'bbox': bbox
                        }
                if prev_span:
                    merged_spans.append(prev_span)
                for span in merged_spans:
                    text_blocks.append(span)
                    font_sizes.append(span['font_size'])

    if not text_blocks:
        return {"title": "", "outline": []}

    body_font_size = Counter(font_sizes).most_common(1)[0][0]
    max_font_size = max(font_sizes)

    #Try to find a title block with a document keyword
    keyword_title_blocks = [b for b in text_blocks if b['page'] == 1 and is_document_title_candidate(b['text'])]
    if keyword_title_blocks:
        #Sort by vertical position
        keyword_title_blocks = sorted(keyword_title_blocks, key=lambda b: b['bbox'][1])
        merged_title = ""
        last_bottom = None
        for b in keyword_title_blocks:
            if last_bottom is None or b['bbox'][1] - last_bottom < 50:  # allow larger gap for title
                merged_title += ("" if merged_title == "" else " ") + b['text']
                last_bottom = b['bbox'][3]
            else:
                break
        title = merged_title.strip() if merged_title else (keyword_title_blocks[0]['text'] if keyword_title_blocks else "")
    else:
        #Fallback to previous merged title logic
        def is_preferred_title(text):
            if not is_valid_title(text):
                return False
            if text.strip().endswith(':'):
                return False
            if re.fullmatch(r'[-_]+', text):
                return False
            if any(word in text.upper() for word in ['RSVP', 'ADDRESS', 'DATE', 'TIME', 'FOR']):
                return False
            return True

        title_blocks = [
            b for b in text_blocks
            if b['page'] == 1
            and b['font_size'] >= max_font_size - 1
            and b['is_bold']
            and is_preferred_title(b['text'])
            and b['bbox'][1] < 300
        ]
        title_blocks = sorted(title_blocks, key=lambda b: b['bbox'][1])
        merged_title = ""
        last_bottom = None
        for b in title_blocks:
            if last_bottom is None or b['bbox'][1] - last_bottom < 30:
                merged_title += ("" if merged_title == "" else " ") + b['text']
                last_bottom = b['bbox'][3]
            else:
                break
        title = merged_title.strip() if merged_title else (title_blocks[0]['text'] if title_blocks else "")
        if not title:
            valid_blocks = [b for b in text_blocks if is_preferred_title(b['text'])]
            title = valid_blocks[0]['text'] if valid_blocks else ""

    outline = []
    prev_heading = None
    for b in text_blocks:
        if is_heading(b['text'], b['font_size'], body_font_size, b['is_bold'], b['font_name']):
            # Merge consecutive headings that are visually close (within 5px vertically)
            if prev_heading and b['page'] == prev_heading['page'] and abs(b['bbox'][1] - prev_heading['bbox'][3]) < 5:
                prev_heading['text'] += ' ' + b['text']
                prev_heading['bbox'][2] = max(prev_heading['bbox'][2], b['bbox'][2])
                prev_heading['bbox'][3] = max(prev_heading['bbox'][3], b['bbox'][3])
                prev_heading['font_size'] = max(prev_heading['font_size'], b['font_size'])
                prev_heading['is_bold'] = prev_heading['is_bold'] or b['is_bold']
            else:
                if prev_heading:
                    # Assign level based on font size difference from body
                    if prev_heading['font_size'] >= body_font_size + 3:
                        level = 'H1'
                    elif prev_heading['font_size'] >= body_font_size + 1:
                        level = 'H2'
                    else:
                        level = 'H3'
                    outline.append({
                        "level": level,
                        "text": prev_heading['text'],
                        "page": prev_heading['page']
                    })
                prev_heading = b.copy()
                prev_heading['bbox'] = list(prev_heading['bbox'])
    if prev_heading:
        if prev_heading['font_size'] >= body_font_size + 3:
            level = 'H1'
        elif prev_heading['font_size'] >= body_font_size + 1:
            level = 'H2'
        else:
            level = 'H3'
        outline.append({
            "level": level,
            "text": prev_heading['text'],
            "page": prev_heading['page']
        })

    #Remove duplicates
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