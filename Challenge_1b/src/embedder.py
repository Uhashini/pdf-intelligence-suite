from sentence_transformers import SentenceTransformer
import numpy as np

# Load the model once
model = SentenceTransformer("multi-qa-mpnet-base-dot-v1")

def embed_query(persona, job):
    """
    Combines persona and job-to-be-done into a single sentence
    and returns the embedding.
    """
    combined = f"Persona: {persona.strip()}. Job: {job.strip()}"
    embedding = model.encode([combined], convert_to_numpy=True, normalize_embeddings=True)
    return embedding[0]

def embed_sections(section_texts):
    """
    Takes a list of full_text strings and returns list of embeddings.
    """
    return model.encode(section_texts, convert_to_numpy=True, normalize_embeddings=True)
