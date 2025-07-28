Adobe India Hackathon 2025 – Challenge 1B  
Intelligent Section and Subsection Extraction from Documents

Problem Statement
Given a set of PDF documents, a persona, and a job-to-be-done (JTBD), intelligently extract and rank the most relevant sections and key subsections from the documents. The goal is to identify content that aligns closely with the persona’s needs and task context.


Project Structure

challenge_1b/
│
├── Collection_1/
│ ├── challenge1b_input.json
│ ├── PDFs/
│ │ └── [input PDFs]
│ └── challenge1b_output.json
│
├── Collection_2/
│ ├── challenge1b_input.json
│ ├── PDFs/
│ │ └── [input PDFs]
│ └── challenge1b_output.json
│
├── Collection_3/
│ ├── challenge1b_input.json
│ ├── PDFs/
│ │ └── [input PDFs]
│ └── challenge1b_output.json
│
├── src/
│ ├── main.py
│ ├── embedder.py
│ ├── extract_sections.py
│ └── ranker.py
│
├── requirements.txt
└── Dockerfile


How It Works

Inputs:
  - JSON file containing:
    - `persona` (e.g., "Travel blogger")
    - `job_to_be_done` (e.g., "Plan a luxury trip to South of France")
    - List of "PDF documents" relevant to the topic

Process:
  1. PDFs are parsed and sections are extracted using layout-aware OCR.
  2. Semantic embeddings are generated using Sentence Transformers.
  3. Sections are ranked based on similarity to persona + JTBD.
  4. Best subsections are extracted using cosine similarity and cross-encoder reranking.

Outputs:
  - A JSON file containing:
    - Metadata
    - Ranked sections
    - Relevant subsections with context


Running the Project

Option 1: Using Docker (Recommended)
> Make sure [Docker](https://www.docker.com/products/docker-desktop) is installed and running.

Step 1: Build Docker Image
```bash
docker build -t adobe-solution .

Step 2: Run for Each Collection
docker run --rm -v "E:\Adobe\Challenge_1b:/app" -w /app/src adobe-solution \
  python main.py ../Collection_1/challenge1b_input.json ../Collection_1/challenge1b_output.json ../Collection_1/PDFs

Repeat the above command for Collection_2 and Collection_3 as needed (change paths accordingly).

Dependencies
Installed automatically via requirements.txt, includes:
    - Python 3.11
    - PyMuPDF (fitz)
    - SentenceTransformers
    - Transformers
    - Scikit-learn
    - NumPy
    - Torch (CPU)


Output Format
Each output1.json contains:
{
  "metadata": {
    "input_documents": [...],
    "persona": "...",
    "job_to_be_done": "..."
  },
  "extracted_sections": [
    {
      "document": "filename.pdf",
      "section_title": "Section Title",
      "importance_rank": 1,
      "page_number": 4
    },
    ...
  ],
  "subsection_analysis": [
    {
      "document": "filename.pdf",
      "section_title": "Section Title",
      "subsection_text": "...",
      "score": 0.873
    },
    ...
  ]
}

Notes
  - Supports up to 3 document collections.
  - Model used: multi-qa-mpnet-base-dot-v1 for embeddings, cross-encoder/ms-marco-MiniLM-L-6-v2 for re-ranking.
  - Designed for fast, explainable, and diverse content recommendations.

