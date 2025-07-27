import json
import os
import sys
from datetime import datetime
from extract_sections import extract_all_sections
from embedder import embed_query, embed_sections
from ranker import rank_sections, extract_subsections, diversify_sections, re_rank_with_cross_encoder
from sentence_transformers import SentenceTransformer

# Constants
INPUT_JSON = sys.argv[1]
OUTPUT_JSON = sys.argv[2]
PDF_FOLDER = sys.argv[3]

def main():
    # 1. Load input JSON
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    # 2. Extract persona and job
    persona_text = input_data["persona"]["role"]
    job_text = input_data["job_to_be_done"]["task"]

    # 3. Extract PDF filenames
    filenames = [doc["filename"] for doc in input_data["documents"]]

    # 4. Extract sections
    sections = extract_all_sections(PDF_FOLDER, filenames)

    # 5. Load model and compute embeddings
    model = SentenceTransformer("multi-qa-mpnet-base-dot-v1")
    query_vec = embed_query(persona_text, job_text)
    section_texts = [sec["full_text"] for sec in sections]
    section_vecs = embed_sections(section_texts)

    # 6. Rank sections and get top results
    initial_top = rank_sections(sections, section_vecs, query_vec, top_k=10)
    top_sections = re_rank_with_cross_encoder(initial_top, f"Persona: {persona_text} Job: {job_text}")

    # 7. Get top refined subsections from each section
    all_subsections = []
    for sec in top_sections:
        subs = extract_subsections(sec, query_vec, model)
        all_subsections.extend(subs)

    # 8. Format output
    output = {
        "metadata": {
            "input_documents": filenames,
            "persona": persona_text,
            "job_to_be_done": job_text
        },
        "extracted_sections": [
            {
                "document": sec["document"],
                "section_title": sec["section_title"],
                "importance_rank": sec["importance_rank"],
                "page_number": sec["page"]
            }
            for sec in top_sections
        ],
        "subsection_analysis": all_subsections
    }

    # 9. Save output
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nOutput saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
