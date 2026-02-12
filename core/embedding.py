class EmbeddingExtractor:
    """Extract embeddings menggunakan ArcFace"""
    
    def __init__(self, detector):
        self.detector = detector
    
    def extract(self, face):
        """Extract normalized embedding from face"""
        return face.normed_embedding
    
    def extract_from_frame(self, frame):
        """Detect face and extract embedding"""
        face, msg = self.detector.get_single_face(frame)
        if face is None:
            return None, msg
        return self.extract(face), "OK"