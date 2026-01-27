import cv2
import numpy as np
import os
import sys
from pathlib import Path
from tkinter import Tk, filedialog

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import Logger
from utils.math_utils import average_embedding

class Enrollment:
    """Alur pendaftaran pegawai dengan pilihan rekam video atau upload gambar"""
    
    def __init__(self, camera, detector, quality_checker, #liveness_checker, 
                 embedding_extractor, pegawai_repo, embedding_repo, settings):
        self.camera = camera
        self.detector = detector
        self.quality_checker = quality_checker
        # self.liveness_checker = liveness_checker
        self.embedding_extractor = embedding_extractor
        self.pegawai_repo = pegawai_repo
        self.embedding_repo = embedding_repo
        self.settings = settings
    
    def enroll(self, nama, nip, mode='video'):
        """
        Proses pendaftaran pegawai baru
        mode: 'video' atau 'upload'
        """
        Logger.info(f"Memulai pendaftaran: {nama} ({nip}) - Mode: {mode}")
        
        if mode == 'video':
            return self._enroll_video(nama, nip)
        elif mode == 'upload':
            return self._enroll_upload(nama, nip)
        else:
            Logger.error(f"Mode tidak valid: {mode}")
            return False
    
    def _enroll_video(self, nama, nip):
        """Enrollment dengan rekam video dari webcam"""
        if not self.camera.open():
            Logger.error("Gagal membuka kamera")
            return False
        
        try:
            embeddings = self._capture_embeddings_video()
            
            if len(embeddings) < self.settings.ENROLLMENT_SAMPLES:
                Logger.warning(f"Hanya dapat {len(embeddings)} embeddings, butuh minimal {self.settings.ENROLLMENT_SAMPLES}")
                return False
            
            is_consistent, avg_similarity = self._verify_consistency(embeddings)
            
            if not is_consistent:
                Logger.warning(f"Kualitas embedding tidak konsisten (avg similarity: {avg_similarity:.3f})")
                Logger.warning("Ulangi pendaftaran dengan pencahayaan lebih baik")
                return False
            
            Logger.success(f"Embeddings konsisten (avg similarity: {avg_similarity:.3f})")
            
            # Liveness check
            # Logger.info("Melakukan liveness check...")
            # if not self.liveness_checker.check(self.camera):
            #     Logger.error("Liveness check gagal")
            #     return False
            
            avg_embedding = average_embedding(embeddings)
            
            id_pegawai = self._save_to_database(nama, nip, avg_embedding)
            
            if id_pegawai:
                Logger.success(f"Pendaftaran berhasil! ID Pegawai: {id_pegawai}")
                return True
            else:
                Logger.error("Gagal menyimpan ke database")
                return False
        
        finally:
            self.camera.release()
    
    def _enroll_upload(self, nama, nip):
        """Enrollment dengan upload multiple images"""
        Logger.info("Mode: Upload gambar")
        Logger.info(f"Siapkan 5-10 foto wajah dengan:")
        Logger.info("- Angle berbeda (depan, sedikit kiri, sedikit kanan)")
        Logger.info("- Ekspresi berbeda")
        Logger.info("- Pencahayaan baik")
        Logger.info("- Format: jpg, jpeg, png")
        
        image_paths = self._get_image_paths()
        
        if len(image_paths) < 5:
            Logger.error(f"❌ GAGAL: Minimal 5 gambar diperlukan, hanya ada {len(image_paths)}")
            return False
        
        Logger.info(f"✓ Diterima {len(image_paths)} gambar untuk diproses")
        
        embeddings = self._process_uploaded_images(image_paths)
        
        if len(embeddings) < 5:
            Logger.warning(f"❌ Hanya {len(embeddings)} gambar valid dari {len(image_paths)}")
            Logger.warning("Upload lebih banyak gambar berkualitas baik (minimal 5)")
            return False
        
        Logger.success(f"✓ Berhasil extract {len(embeddings)} embeddings valid")
        
        is_consistent, avg_similarity = self._verify_consistency(embeddings)
        
        if not is_consistent:
            Logger.warning(f"Kualitas embedding tidak konsisten (avg similarity: {avg_similarity:.3f})")
            Logger.warning("Upload gambar dengan angle & pencahayaan lebih bervariasi")
            return False
        
        Logger.success(f"✓ Embeddings konsisten (avg similarity: {avg_similarity:.3f})")
        
        Logger.warning("⚠️ Liveness check dilewati untuk mode upload")
        Logger.warning("⚠️ Pastikan foto adalah wajah asli, bukan dari layar/print")
        
        avg_embedding = average_embedding(embeddings)
        
        id_pegawai = self._save_to_database(nama, nip, avg_embedding)
        
        if id_pegawai:
            Logger.success(f"✓ Pendaftaran berhasil! ID Pegawai: {id_pegawai}")
            return True
        else:
            Logger.error("Gagal menyimpan ke database")
            return False
    
    def _get_image_paths(self):
        """Get image paths menggunakan file browser dialog"""
        Logger.info("⏳ Membuka file browser...")
        
        try:
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            file_paths = filedialog.askopenfilenames(
                title="Pilih 5-10 foto wajah Anda (minimal 5)",
                filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")],
                initialdir=os.path.expanduser("~\\Pictures")
            )
            
            root.destroy()
            
            if not file_paths:
                Logger.error("❌ Tidak ada file yang dipilih")
                return []
            
            image_paths = list(file_paths)
            
            if len(image_paths) < 5:
                Logger.error(f"❌ Minimal 5 gambar diperlukan, hanya ada {len(image_paths)}")
                return []
            
            if len(image_paths) > 10:
                Logger.warning(f"⚠️ Dipilih {len(image_paths)} gambar, maksimal 10. Menggunakan 10 gambar pertama.")
                image_paths = image_paths[:10]
            
            Logger.success(f"✓ Dipilih {len(image_paths)} gambar:")
            for i, path in enumerate(image_paths, 1):
                Logger.info(f"  {i}. {os.path.basename(path)}")
            
            return image_paths
        
        except Exception as e:
            Logger.error(f"Error saat membuka file browser: {e}")
            return []
    
    def _process_uploaded_images(self, image_paths):
        """Process uploaded images dan extract embeddings"""
        embeddings = []
        
        Logger.info(f"Memproses {len(image_paths)} gambar...")
        
        for i, image_path in enumerate(image_paths):
            Logger.info(f"Processing {i+1}/{len(image_paths)}: {os.path.basename(image_path)}")
            
            frame = cv2.imread(image_path)
            
            if frame is None:
                Logger.warning(f"Gagal membaca gambar: {image_path}")
                continue
            
            h, w = frame.shape[:2]
            if w > 1920 or h > 1080:
                scale = min(1920/w, 1080/h)
                new_w, new_h = int(w*scale), int(h*scale)
                frame = cv2.resize(frame, (new_w, new_h))
            
            face, msg = self.detector.get_single_face(frame, self.settings.CONFIDENCE_THRESHOLD)
            
            if face is None:
                Logger.warning(f"  ✗ {msg}")
                continue
            
            is_valid, result = self.quality_checker.validate_face(frame, face)
            
            if not is_valid:
                Logger.warning(f"  ✗ {result}")
                continue
            
            embedding = self.embedding_extractor.extract(face)
            embeddings.append(embedding)
            
            Logger.success(f"  ✓ Valid - embedding extracted")
        
        Logger.info(f"Berhasil extract {len(embeddings)} embeddings dari {len(image_paths)} gambar")
        
        return embeddings
    
    def _capture_embeddings_video(self):
        """Capture embeddings dari video webcam"""
        embeddings = []
        frame_count = 0
        process_interval = 3
        
        Logger.info("Posisikan wajah Anda di depan kamera...")
        Logger.info(f"Target: {self.settings.ENROLLMENT_SAMPLES} embeddings")
        
        while len(embeddings) < self.settings.ENROLLMENT_SAMPLES:
            ret, frame = self.camera.read()
            if not ret:
                continue
            
            frame_count += 1
            display_frame = frame.copy()
            
            cv2.putText(display_frame, f"Captured: {len(embeddings)}/{self.settings.ENROLLMENT_SAMPLES}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if frame_count % process_interval == 0:
                face, msg = self.detector.get_single_face(frame, self.settings.CONFIDENCE_THRESHOLD)
                
                if face is None:
                    cv2.putText(display_frame, msg, (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    is_valid, result = self.quality_checker.validate_face(frame, face)
                    
                    if is_valid:
                        embedding = self.embedding_extractor.extract(face)
                        embeddings.append(embedding)
                        
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
            id_pegawai = self.pegawai_repo.create(nama, nip)
            
            self.embedding_repo.save(id_pegawai, embedding)
            
            return id_pegawai
        
        except Exception as e:
            Logger.error(f"Database error: {e}")
            return None