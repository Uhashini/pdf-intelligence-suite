# PDF Outline Extractor — Connecting the Dots Challenge

## IMPORTANT: Directory Structure
All files and folders (including this README, Dockerfile, process_pdfs.py, requirements.txt, and the dataset folder) **must be inside the `Challenge_1a` directory**. 

**All terminal commands below should be run from inside the `Challenge_1a` directory.**

---

## Overview
This solution extracts a structured outline (Title, H1, H2, H3 headings with page numbers) from PDF files, as required for Round 1A of the Adobe India Hackathon 2025.

## Approach
- **PDF Parsing:** Uses [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) for fast, accurate PDF text extraction.
- **Heading Detection:**
  - Analyzes font size, boldness, and position to identify headings.
  - Clusters text by font size and style to assign H1, H2, H3 levels.
  - Extracts the document title as the largest, most prominent text on the first page, using keyword and merging heuristics for accuracy.
- **Batch Processing:** Processes all PDFs in `/app/input` and outputs corresponding JSON files to `/app/output`.
- **No Internet Required:** All processing is offline and CPU-only.

## Dependencies
- Python 3.10
- PyMuPDF (fitz)

## How to Build and Run (Docker)

### 1. Change to the Challenge_1a Directory
```
cd Challenge_1a
```

### 2. Build the Docker Image
```
docker build --platform linux/amd64 -t pdf-processor .
```

### 3. Run the Container
```
docker run --rm -v ${PWD}/dataset/pdfs:/app/input:ro -v ${PWD}/dataset/outputs:/app/output --network none pdf-processor
```
- Place your PDF files in the `dataset/pdfs` directory (inside `Challenge_1a`).
- The output JSON files will appear in the `dataset/outputs` directory (inside `Challenge_1a`).

## Output Format
Each output JSON will look like:
```json
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
```

## Notes
- No hardcoded logic for specific files; works on any PDF up to 50 pages.
- No network calls or GPU dependencies.
- Model size and runtime are within challenge constraints.

---
**For any questions, see the code comments or contact the author.**
