import cv2
import time
from utils.logger import Logger
from utils.timer import Timer

class Recognition:
    """Alur face recognition untuk akses pintu"""
    
    def __init__(self, camera, detector, quality_checker, # liveness_checker,
                 embedding_extractor, matcher, pegawai_repo, embedding_repo,
                 log_repo, settings):
        self.camera = camera
        self.detector = detector
        self.quality_checker = quality_checker
        # self.liveness_checker = liveness_checker
        self.embedding_extractor = embedding_extractor
        self.matcher = matcher
        self.pegawai_repo = pegawai_repo
        self.embedding_repo = embedding_repo
        self.log_repo = log_repo
        self.settings = settings
        
        # Security tracking
        self.failed_attempts = 0
        self.lockout_until = 0
    
    def recognize(self):
        """Proses face recognition untuk akses pintu"""
        Logger.info("=== Face Recognition Access System ===")
        
        # Check lockout
        if self._is_locked_out():
            remaining = int(self.lockout_until - time.time())
            Logger.warning(f"Sistem terkunci. Coba lagi dalam {remaining} detik")
            return False
        
        # Step 1: Buka kamera
        if not self.camera.open():
            Logger.error("Gagal membuka kamera")
            return False
        
        try:
            # Step 2: Detect & recognize face
            employee_id, similarity = self._recognize_face()
            
            if employee_id is None:
                self._handle_failed_attempt()
                self.log_repo.log_access(None, 'DENIED', 'Wajah tidak dikenali')
                Logger.error("AKSES DITOLAK - Wajah tidak dikenali")
                return False
            
            Logger.success(f"Wajah dikenali! Similarity: {similarity:.3f}")
            
            # Step 3: Liveness check (DISABLED)
            # Logger.info("Melakukan liveness check...")
            # if not self.liveness_checker.check(self.camera):
            #     self.log_repo.log_access(employee_id, 'DENIED', 'Liveness check gagal')
            #     Logger.error("AKSES DITOLAK - Liveness check gagal")
            #     return False
            
            # Step 4: Check access rights
            has_access = self._check_access_rights(employee_id)
            
            if not has_access:
                self.log_repo.log_access(employee_id, 'DENIED', 'Tidak memiliki hak akses')
                Logger.error("AKSES DITOLAK - Tidak memiliki hak akses")
                return False
            
            # Step 5: Grant access
            self._grant_access(employee_id)
            return True
        
        finally:
            self.camera.release()
    
    def _recognize_face(self):
        """Detect dan recognize face dalam time constraint"""
        timer = Timer(self.settings.REAL_TIME_CONSTRAINT * 3)
        timer.start()
        
        frame_count = 0
        process_interval = 2
        
        Logger.info("Posisikan wajah di depan kamera...")
        
        while not timer.is_timeout():
            ret, frame = self.camera.read()
            if not ret:
                continue
            
            frame_count += 1
            display_frame = frame.copy()
            
            # Show remaining time
            remaining = int(timer.remaining())
            cv2.putText(display_frame, f"Time: {remaining}s", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
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
                        
                        # Match with database
                        stored_embeddings = self.embedding_repo.get_all()
                        employee_id, similarity = self.matcher.match(embedding, stored_embeddings)
                        
                        if employee_id:
                            cv2.putText(display_frame, f"RECOGNIZED! Sim: {similarity:.2f}", 
                                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            cv2.imshow('Access Control', display_frame)
                            cv2.waitKey(500)  # Show result for 500ms
                            cv2.destroyAllWindows()
                            return employee_id, similarity
                        else:
                            cv2.putText(display_frame, f"Tidak terdaftar (sim: {similarity:.2f})", 
                                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    else:
                        cv2.putText(display_frame, result, (10, 60),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            
            cv2.imshow('Access Control', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        
        cv2.destroyAllWindows()
        return None, 0.0
    
    def _check_access_rights(self, employee_id):
        """Check apakah pegawai punya hak akses"""
        # Get employee info
        employee = self.pegawai_repo.get_by_id(employee_id)
        
        if employee is None:
            return False
        
        # For now, all registered employees have access
        # You can implement more complex logic here
        return True
    
    def _grant_access(self, employee_id):
        """Grant access dan buka pintu"""
        employee = self.pegawai_repo.get_by_id(employee_id)
        
        Logger.success("="*50)
        Logger.success(f"✓ AKSES DIBERIKAN")
        Logger.success(f"Nama: {employee['nama']}")
        Logger.success(f"NIP: {employee['nip']}")
        Logger.success("="*50)
        
        # Log access
        self.log_repo.log_access(employee_id, 'GRANTED', 'Akses berhasil')
        
        # Reset failed attempts
        self.failed_attempts = 0
        
        # Simulate door opening
        self._open_door()
    
    def _open_door(self):
        """Simulate buka pintu"""
        Logger.info("🚪 Pintu terbuka...")
        time.sleep(2)
        Logger.info("🚪 Pintu tertutup")
    
    def _handle_failed_attempt(self):
        """Handle failed recognition attempt"""
        self.failed_attempts += 1
        
        Logger.warning(f"Percobaan gagal: {self.failed_attempts}/{self.settings.MAX_ATTEMPTS}")
        
        if self.failed_attempts >= self.settings.MAX_ATTEMPTS:
            self.lockout_until = time.time() + self.settings.LOCKOUT_DURATION
            Logger.error(f"⚠ Sistem terkunci selama {self.settings.LOCKOUT_DURATION} detik")
        else:
            Logger.info(f"Cooldown {self.settings.COOLDOWN} detik...")
            time.sleep(self.settings.COOLDOWN)
    
    def _is_locked_out(self):
        """Check apakah sistem sedang terkunci"""
        if self.lockout_until > time.time():
            return True
        
        # Reset if lockout expired
        if self.lockout_until > 0:
            self.lockout_until = 0
            self.failed_attempts = 0
        
        return False