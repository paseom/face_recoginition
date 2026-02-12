from utils.math_utils import cosine_similarity
import numpy as np

class FaceMatcher:
    """Match faces using cosine similarity"""
    
    def __init__(self, threshold=0.6):
        self.threshold = threshold
    
    def match(self, embedding, stored_embeddings):
        """Match embedding against database"""
        if embedding is None:
            return None, 0.0

        best_match = None
        best_similarity = 0
        
        for id_pegawai, stored_embedding in stored_embeddings:
            if stored_embedding is None:
                continue
            similarity = cosine_similarity(embedding, stored_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = id_pegawai
        
        if best_similarity >= self.threshold:
            return best_match, best_similarity
        
        return None, best_similarity
    
    def verify_consistency(self, embeddings, threshold=0.7):
        """Verify embeddings are consistent"""
        from utils.math_utils import calculate_all_similarities
        
        similarities = calculate_all_similarities(embeddings)
        avg_similarity = np.mean(similarities)
        
        return avg_similarity >= threshold, avg_similarity
