from insightface.app import FaceAnalysis

class FaceDetector:
    """Face detection menggunakan RetinaFace (InsightFace)"""
    
    def __init__(self):
        self.app = FaceAnalysis(providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
    
    def detect(self, frame):
        """Detect faces in frame"""
        faces = self.app.get(frame)
        return faces
    
    def get_single_face(self, frame, min_confidence=0.8):
        """Get single face with confidence threshold"""
        faces = self.detect(frame)
        
        if len(faces) == 0:
            return None, "Wajah tidak terdeteksi"
        
        if len(faces) > 1:
            return None, "Harus sendiri! Terdeteksi lebih dari 1 wajah"
        
        face = faces[0]
        
        if face.det_score < min_confidence:
            return None, f"Confidence rendah: {face.det_score:.2f}"
        
        return face, "OK"