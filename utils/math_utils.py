import numpy as np

def cosine_similarity(embedding1, embedding2):
    """Calculate cosine similarity between two embeddings"""
    return np.dot(embedding1, embedding2)

def average_embedding(embeddings):
    """Calculate average of multiple embeddings"""
    return np.mean(np.array(embeddings), axis=0)

def calculate_all_similarities(embeddings):
    """Calculate pairwise similarities between all embeddings"""
    similarities = []
    n = len(embeddings)
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append(sim)
    return similarities