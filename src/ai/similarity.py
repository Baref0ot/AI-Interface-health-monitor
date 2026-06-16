import numpy as np

def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.
    """
    
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))



def find_most_similar(new_embedding, past_embeddings):
    """
    Find the most similar past event based on cosine similarity.
    """
    best_score = -1
    best_match = None

    for record in past_embeddings:
        score = cosine_similarity(new_embedding, record['embedding'])
        
        if score > best_score:
            best_score = score
            best_match = record
            
    return best_match, best_score