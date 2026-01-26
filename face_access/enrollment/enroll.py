import cv2
import numpy as np
from utils.logger import Logger
from utils.math_utils import average_embedding

class Enrollment:
    """Alur pendaftaran pegawai"""
    
    def __init__(self, camera, detector, quality_checker, # liveness_checker, 
                 embedding_extractor, pegawai_repo, embedding_repo, settings):
        self.camera = camera
        self.detector = detector
        self.quality_checker = quality_checker
        # self.liveness_checker = liveness_checker
        self.embedding_extractor = embedding_extractor
        self.pegawai_repo = pegawai_repo
        self.embedding_repo = embedding_repo
        self.settings = settings
    
    def enroll(self, nama, nip):
        """Proses pendaftaran pegawai baru"""
        Logger.info(f"Memulai pendaftaran: {nama} ({nip})")
        
        # Step 1: Buka kamera
        if not self.camera.open():
            Logger.error("Gagal membuka kamera")
            return False
        
        try:
            # Step 2: Capture multiple embeddings
            embeddings = self._capture_embeddings()
            
            if len(embeddings) < self.settings.ENROLLMENT_SAMPLES:
                Logger.warning(f"Hanya dapat {len(embeddings)} embeddings, butuh minimal {self.settings.ENROLLMENT_SAMPLES}")
                return False
            
            # Step 3: Verify consistency
            is_consistent, avg_similarity = self._verify_consistency(embeddings)
            
            if not is_consistent:
                Logger.warning(f"Kualitas embedding tidak konsisten (avg similarity: {avg_similarity:.3f})")
                Logger.warning("Ulangi pendaftaran dengan pencahayaan lebih baik")
                return False
            
            Logger.success(f"Embeddings konsisten (avg similarity: {avg_similarity:.3f})")
            
            # Step 4: Liveness check (DISABLED)
            # Logger.info("Melakukan liveness check...")
            # if not self.liveness_checker.check(self.camera):
            #     Logger.error("Liveness check gagal")
            #     return False
            
            # Step 5: Calculate average embedding
            avg_embedding = average_embedding(embeddings)
            
            # Step 6: Save to database
            id_pegawai = self._save_to_database(nama, nip, avg_embedding)
            
            if id_pegawai:
                Logger.success(f"Pendaftaran berhasil! ID Pegawai: {id_pegawai}")
                return True
            else:
                Logger.error("Gagal menyimpan ke database")
                return False
        
        finally:
            self.camera.release()
    
    def _capture_embeddings(self):
        """Capture 5-10 embeddings dengan validasi"""
        embeddings = []
        frame_count = 0
        process_interval = 3  # Process every 3rd frame
        
        Logger.info("Posisikan wajah Anda di depan kamera...")
        Logger.info(f"Target: {self.settings.ENROLLMENT_SAMPLES} embeddings")
        
        while len(embeddings) < self.settings.ENROLLMENT_SAMPLES:
            ret, frame = self.camera.read()
            if not ret:
                continue
            
            frame_count += 1
            display_frame = frame.copy()
            
            # Display progress
            cv2.putText(display_frame, f"Captured: {len(embeddings)}/{self.settings.ENROLLMENT_SAMPLES}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Process face detection every N frames
            if frame_count % process_interval == 0:
                face, msg = self.detector.get_single_face(frame, self.settings.CONFIDENCE_THRESHOLD)
                
                if face is None:
                    cv2.putText(display_frame, msg, (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    # Validate quality
                    is_valid, result = self.quality_checker.validate_face(frame, face)
                    
                    if is_valid:
                        # Extract embedding
                        embedding = self.embedding_extractor.extract(face)
                        embeddings.append(embedding)
                        
                        # Draw bounding box
                        bbox = face.bbox.astype(int)
                        cv2.rectangle(display_frame, (bbox[0], bbox[1]), 
                                    (bbox[2], bbox[3]), (0, 255, 0), 2)
                        
                        cv2.putText(display_frame, "VALID - Captured!", (10, 60),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        Logger.info(f"Captured {len(embeddings)}/{self.settings.ENROLLMENT_SAMPLES}")
                    else:
                        cv2.putText(display_frame, result, (10, 60),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            
            cv2.imshow('Enrollment', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                Logger.warning("Pendaftaran dibatalkan oleh user")
                break
        
        cv2.destroyAllWindows()
        return embeddings
    
    def _verify_consistency(self, embeddings):
        """Verify bahwa semua embeddings konsisten"""
        from utils.math_utils import calculate_all_similarities
        
        similarities = calculate_all_similarities(embeddings)
        avg_similarity = np.mean(similarities)
        
        is_consistent = avg_similarity >= self.settings.ENROLLMENT_SIMILARITY
        
        return is_consistent, avg_similarity
    
    def _save_to_database(self, nama, nip, embedding):
        """Save pegawai dan embedding ke database"""
        try:
            # Save pegawai
            id_pegawai = self.pegawai_repo.create(nama, nip)
            
            # Save embedding
            self.embedding_repo.save(id_pegawai, embedding)
            
            return id_pegawai
        
        except Exception as e:
            Logger.error(f"Database error: {e}")
            return None