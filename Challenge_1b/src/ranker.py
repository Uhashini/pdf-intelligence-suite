import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from sentence_transformers import CrossEncoder
def rank_sections(sections, section_vectors, query_vector, top_k=5):
    """
    Rank sections using a hybrid scoring mechanism.
    """
    similarities = cosine_similarity([query_vector], section_vectors)[0]
    
    ranked = []
    for i, section in enumerate(sections):
        similarity_score = similarities[i]
        
        # Heuristics
        length_score = min(len(section["full_text"]) / 500, 1.0)  # Cap at 1.0
        position_score = max(1.0 - (section["page"] - 1) * 0.1, 0)  # Earlier pages weigh more
        
        # Weighted hybrid score
        final_score = (
            0.65 * similarity_score +    # Core semantic similarity
            0.25 * length_score +        # Prefer richer sections
            0.10 * position_score        # Slight preference to early pages
        )

        section_copy = section.copy()
        section_copy["score"] = final_score
        section_copy["similarity_score"] = float(similarity_score)
        section_copy["importance_rank"] = 0  # temporary
        ranked.append(section_copy)

    # Sort by final_score
    ranked_sorted = sorted(ranked, key=lambda x: x["score"], reverse=True)

    # Assign final ranks
    for i, sec in enumerate(ranked_sorted[:top_k]):
        sec["importance_rank"] = i + 1

    return ranked_sorted[:top_k]



def extract_subsections(section, query_vector, model, max_subs=2):
    """
    Further split a section into sentences/paragraphs and rank them.
    """
    from sentence_transformers import util

    text = section["full_text"]
    doc_name = section["document"]
    page = section["page"]

    # Split by paragraph or sentence
    chunks = [p.strip() for p in text.split('\n') if len(p.strip()) > 20]

    if not chunks:
        return []

    # Embed all chunks
    chunk_embeddings = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)

    # Compute similarity to the query
    scores = cosine_similarity([query_vector], chunk_embeddings)[0]

    # Rank top max_subs
    ranked_chunks = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)[:max_subs]

    # Format output
    subsections = []
    for chunk, _ in ranked_chunks:
        subsections.append({
            "document": doc_name,
            "page_number": page,
            "refined_text": chunk
        })

    return subsections


def diversify_sections(ranked_sections, top_n=5, max_per_doc=2):
    doc_buckets = defaultdict(list)

    # Group by document
    for section in ranked_sections:
        doc_buckets[section["document"]].append(section)

    # Sort each document's sections by importance
    for doc in doc_buckets:
        doc_buckets[doc] = sorted(doc_buckets[doc], key=lambda x: x["score"], reverse=True)

    # Interleave best from each doc (up to max_per_doc)
    diversified = []
    while len(diversified) < top_n:
        for doc, sections in doc_buckets.items():
            if sections:
                diversified.append(sections.pop(0))
            if len(diversified) >= top_n:
                break

    return diversified

def re_rank_with_cross_encoder(top_sections, query, max_rerank=5):
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")

    pairs = [(query, sec["full_text"]) for sec in top_sections]
    scores = model.predict(pairs)

    for i, score in enumerate(scores):
        top_sections[i]["score"] += 0.5 * float(score)  # Blend cross-score

    reranked = sorted(top_sections, key=lambda x: x["score"], reverse=True)
    
    for i, sec in enumerate(reranked[:max_rerank]):
        sec["importance_rank"] = i + 1

    return reranked[:max_rerank]