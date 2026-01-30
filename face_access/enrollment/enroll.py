import cv2
import numpy as np
import os
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
    
    def enroll(self, nama, nip, mode='video', image_paths=None):
        """
        Proses pendaftaran pegawai baru
        mode: 'video' atau 'upload'
        image_paths: list of image paths (untuk mode upload dari streamlit)
        """
        Logger.info(f"Memulai pendaftaran: {nama} ({nip}) - Mode: {mode}")
        
        if mode == 'video':
            return self._enroll_video(nama, nip)
        elif mode == 'upload':
            # Pass image_paths as keyword argument
            return self._enroll_upload(nama=nama, nip=nip, image_paths=image_paths)
        else:
            Logger.error(f"Mode tidak valid: {mode}")
            return False
    
    def _enroll_video(self, nama, nip):
        """Enrollment dengan rekam video dari webcam"""
        # Buka kamera
        if not self.camera.open():
            Logger.error("Gagal membuka kamera")
            return False
        
        try:
            # Capture multiple embeddings
            embeddings = self._capture_embeddings_video()
            
            if len(embeddings) < self.settings.ENROLLMENT_SAMPLES:
                Logger.warning(f"Hanya dapat {len(embeddings)} embeddings, butuh minimal {self.settings.ENROLLMENT_SAMPLES}")
                return False
            
            # Verify consistency
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
            
            # Calculate average embedding
            avg_embedding = average_embedding(embeddings)
            
            # Save to database
            id_pegawai = self._save_to_database(nama, nip, avg_embedding)
            
            if id_pegawai:
                Logger.success(f"Pendaftaran berhasil! ID Pegawai: {id_pegawai}")
                return True
            else:
                Logger.error("Gagal menyimpan ke database")
                return False
        
        finally:
            self.camera.release()
    
    def _enroll_upload(self, nama, nip, image_paths=None):
        """Enrollment dengan upload multiple images"""
        Logger.info("Mode: Upload gambar")
        
        # If image_paths provided (from Streamlit), use them directly
        if image_paths is not None:
            Logger.info(f"Menggunakan {len(image_paths)} gambar dari parameter")
        else:
            # Interactive mode (CLI)
            Logger.info(f"Siapkan {self.settings.ENROLLMENT_SAMPLES} foto wajah dengan:")
            Logger.info("- Angle berbeda (depan, sedikit kiri, sedikit kanan)")
            Logger.info("- Ekspresi berbeda")
            Logger.info("- Pencahayaan baik")
            Logger.info("- Format: jpg, jpeg, png")
            
            # Get image paths from user
            image_paths = self._get_image_paths()
        
        if len(image_paths) < 5:
            Logger.error(f"Minimal 5 gambar diperlukan, hanya ada {len(image_paths)}")
            self._cleanup_temp_files(image_paths)
            return False
        
        # Process images
        embeddings = self._process_uploaded_images(image_paths)
        
        # Cleanup temp files if generated (not from Streamlit)
        if image_paths and len(image_paths) > 0:
            # Only cleanup if it's temp generated files, not user-provided
            import tempfile
            first_path = image_paths[0]
            if tempfile.gettempdir() in first_path:
                self._cleanup_temp_files(image_paths)
        
        if len(embeddings) < 5:
            Logger.warning(f"Hanya {len(embeddings)} gambar valid dari {len(image_paths)}")
            Logger.warning("Upload lebih banyak gambar berkualitas baik")
            return False
        
        # Verify consistency
        is_consistent, avg_similarity = self._verify_consistency(embeddings)
        
        if not is_consistent:
            Logger.warning(f"Kualitas embedding tidak konsisten (avg similarity: {avg_similarity:.3f})")
            Logger.warning("Upload gambar dengan angle & pencahayaan lebih bervariasi")
            return False
        
        Logger.success(f"Embeddings konsisten (avg similarity: {avg_similarity:.3f})")
        
        # NO liveness check for uploaded images (can't do live check on static images)
        Logger.warning("⚠️ Liveness check dilewati untuk mode upload")
        Logger.warning("⚠️ Pastikan foto adalah wajah asli, bukan dari layar/print")
        
        # Calculate average embedding
        avg_embedding = average_embedding(embeddings)
        
        # Save to database
        id_pegawai = self._save_to_database(nama, nip, avg_embedding)
        
        if id_pegawai:
            Logger.success(f"Pendaftaran berhasil! ID Pegawai: {id_pegawai}")
            return True
        else:
            Logger.error("Gagal menyimpan ke database")
            return False
    
    def _cleanup_temp_files(self, image_paths):
        """Cleanup temporary generated files"""
        import tempfile
        import shutil
        
        if not image_paths:
            return
        
        # Check if files are in temp directory
        first_path = image_paths[0]
        if tempfile.gettempdir() in first_path:
            temp_dir = os.path.dirname(first_path)
            try:
                shutil.rmtree(temp_dir)
                Logger.info(f"Cleaned up temp files: {temp_dir}")
            except Exception as e:
                Logger.warning(f"Failed to cleanup temp files: {e}")
    
    def _get_image_paths(self):
        """Get image paths dari user input"""
        print("\n" + "="*60)
        print("UPLOAD GAMBAR")
        print("="*60)
        print("Cara 1: Browse file satu per satu (File Dialog)")
        print("Cara 2: Browse folder (Folder Dialog)")
        print("Cara 3: Single pas foto dengan file browser")
        print("Cara 4: Manual input path (advanced)")
        print("="*60)
        
        mode = input("\nPilih cara (1/2/3/4): ").strip()
        
        if mode == '1':
            return self._browse_images_one_by_one()
        elif mode == '2':
            return self._browse_folder()
        elif mode == '3':
            return self._browse_single_photo_with_augmentation()
        elif mode == '4':
            return self._manual_input_images()
        else:
            Logger.error("Pilihan tidak valid")
            return []
    
    def _browse_images_one_by_one(self):
        """Browse file dialog untuk pilih gambar satu per satu"""
        try:
            from tkinter import Tk
            from tkinter.filedialog import askopenfilenames
        except ImportError:
            Logger.error("Tkinter tidak tersedia, gunakan cara manual (pilih 4)")
            return []
        
        Logger.info("Membuka file browser...")
        Logger.info("Pilih 5-15 foto wajah (Ctrl+Click untuk multiple)")
        
        root = Tk()
        root.withdraw()  # Hide main window
        root.attributes('-topmost', True)  # Bring to front
        
        file_paths = askopenfilenames(
            title="Pilih Foto Wajah (5-15 foto)",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        root.destroy()
        
        if not file_paths:
            Logger.warning("Tidak ada file yang dipilih")
            return []
        
        image_paths = list(file_paths)
        Logger.info(f"Dipilih {len(image_paths)} foto")
        
        for i, path in enumerate(image_paths, 1):
            Logger.info(f"  {i}. {os.path.basename(path)}")
        
        return image_paths
    
    def _browse_folder(self):
        """Browse folder dialog"""
        try:
            from tkinter import Tk
            from tkinter.filedialog import askdirectory
        except ImportError:
            Logger.error("Tkinter tidak tersedia, gunakan cara manual (pilih 4)")
            return []
        
        Logger.info("Membuka folder browser...")
        Logger.info("Pilih folder yang berisi foto-foto wajah")
        
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        folder_path = askdirectory(
            title="Pilih Folder Berisi Foto Wajah"
        )
        
        root.destroy()
        
        if not folder_path:
            Logger.warning("Tidak ada folder yang dipilih")
            return []
        
        Logger.info(f"Folder dipilih: {folder_path}")
        
        # Get all image files
        image_paths = []
        supported_formats = ('.jpg', '.jpeg', '.png')
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_formats):
                full_path = os.path.join(folder_path, filename)
                image_paths.append(full_path)
        
        Logger.info(f"Ditemukan {len(image_paths)} gambar:")
        for i, path in enumerate(image_paths, 1):
            Logger.info(f"  {i}. {os.path.basename(path)}")
        
        return image_paths
    
    def _browse_single_photo_with_augmentation(self):
        """Browse single photo dengan file dialog"""
        try:
            from tkinter import Tk
            from tkinter.filedialog import askopenfilename
        except ImportError:
            Logger.error("Tkinter tidak tersedia, gunakan cara manual (pilih 4)")
            return []
        
        print("\n⚠️  PERHATIAN: Mode ini untuk TESTING/DEMO saja!")
        print("⚠️  Untuk production, gunakan multiple real photos!")
        
        Logger.info("Membuka file browser...")
        Logger.info("Pilih 1 pas foto (akan di-generate menjadi 9 variations)")
        
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        path = askopenfilename(
            title="Pilih Pas Foto",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        root.destroy()
        
        if not path:
            Logger.warning("Tidak ada file yang dipilih")
            return []
        
        Logger.info(f"Foto dipilih: {os.path.basename(path)}")
        
        return self._generate_variations_from_single_photo(path)
    
    def _manual_input_images(self):
        """Manual input path (fallback untuk advanced user)"""
        print("\n=== MANUAL INPUT MODE ===")
        print("Pilih sub-mode:")
        print("1. Input path satu per satu")
        print("2. Input path folder")
        print("3. Single photo dengan path")
        
        sub_mode = input("Pilih (1/2/3): ").strip()
        
        if sub_mode == '1':
            return self._get_images_one_by_one()
        elif sub_mode == '2':
            return self._get_images_from_folder()
        elif sub_mode == '3':
            return self._get_single_photo_with_augmentation()
        else:
            Logger.error("Pilihan tidak valid")
            return []
    
    def _get_images_one_by_one(self):
        """Input gambar satu per satu"""
        image_paths = []
        
        print(f"\nMasukkan path gambar (minimal 5, maksimal 15)")
        print("Ketik 'done' jika sudah selesai")
        
        for i in range(15):  # Max 15 images
            path = input(f"\nGambar {i+1}: ").strip()
            
            if path.lower() == 'done':
                break
            
            if not os.path.exists(path):
                Logger.warning(f"File tidak ditemukan: {path}")
                continue
            
            if not path.lower().endswith(('.jpg', '.jpeg', '.png')):
                Logger.warning("Format harus jpg, jpeg, atau png")
                continue
            
            image_paths.append(path)
            Logger.info(f"✓ Ditambahkan: {os.path.basename(path)}")
        
        return image_paths
    
    def _generate_variations_from_single_photo(self, path):
        """Generate variations dari 1 pas foto"""
        if not os.path.exists(path):
            Logger.error(f"File tidak ditemukan: {path}")
            return []
        
        Logger.info("Membaca foto...")
        original = cv2.imread(path)
        
        if original is None:
            Logger.error("Gagal membaca foto")
            return []
        
        # Create temp directory untuk simpan variations
        import tempfile
        temp_dir = tempfile.mkdtemp()
        Logger.info(f"Generating variations di: {temp_dir}")
        
        variations = []
        
        # Original
        original_path = os.path.join(temp_dir, "original.jpg")
        cv2.imwrite(original_path, original)
        variations.append(original_path)
        Logger.info("✓ Original saved")
        
        # Slight rotations (simulate head turns)
        angles = [-10, -5, 5, 10]
        for i, angle in enumerate(angles):
            rotated = self._rotate_image(original, angle)
            rotated_path = os.path.join(temp_dir, f"rotated_{i+1}.jpg")
            cv2.imwrite(rotated_path, rotated)
            variations.append(rotated_path)
            Logger.info(f"✓ Rotation {angle}° saved")
        
        # Brightness variations
        for i, factor in enumerate([0.9, 1.1]):
            adjusted = self._adjust_brightness(original, factor)
            adjusted_path = os.path.join(temp_dir, f"brightness_{i+1}.jpg")
            cv2.imwrite(adjusted_path, adjusted)
            variations.append(adjusted_path)
            Logger.info(f"✓ Brightness {factor} saved")
        
        # Slight zoom
        for i, scale in enumerate([0.95, 1.05]):
            zoomed = self._zoom_image(original, scale)
            zoomed_path = os.path.join(temp_dir, f"zoom_{i+1}.jpg")
            cv2.imwrite(zoomed_path, zoomed)
            variations.append(zoomed_path)
            Logger.info(f"✓ Zoom {scale} saved")
        
        Logger.success(f"Generated {len(variations)} variations dari pas foto")
        Logger.warning("⚠️  Ini hanya untuk demo/testing!")
        
        return variations
    
    def _get_single_photo_with_augmentation(self):
        """Generate variations dari 1 pas foto (manual path input)"""
        print("\n⚠️  PERHATIAN: Mode ini untuk TESTING/DEMO saja!")
        print("⚠️  Untuk production, gunakan multiple real photos!")
        print()
        
        path = input("Masukkan path pas foto: ").strip()
        
        return self._generate_variations_from_single_photo(path)
    
    def _rotate_image(self, image, angle):
        """Rotate image by angle"""
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, matrix, (w, h), 
                                 borderMode=cv2.BORDER_REPLICATE)
        return rotated
    
    def _adjust_brightness(self, image, factor):
        """Adjust brightness"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv = hsv.astype(np.float32)
        hsv[:,:,2] = hsv[:,:,2] * factor
        hsv[:,:,2] = np.clip(hsv[:,:,2], 0, 255)
        hsv = hsv.astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def _zoom_image(self, image, scale):
        """Zoom image"""
        h, w = image.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        
        if scale > 1:
            # Zoom in
            resized = cv2.resize(image, (new_w, new_h))
            start_y = (new_h - h) // 2
            start_x = (new_w - w) // 2
            cropped = resized[start_y:start_y+h, start_x:start_x+w]
            return cropped
        else:
            # Zoom out
            resized = cv2.resize(image, (new_w, new_h))
            canvas = np.zeros_like(image)
            start_y = (h - new_h) // 2
            start_x = (w - new_w) // 2
            canvas[start_y:start_y+new_h, start_x:start_x+new_w] = resized
            return canvas
    
    def _get_images_from_folder(self):
        """Input semua gambar dari satu folder"""
        folder_path = input("\nMasukkan path folder: ").strip()
        
        if not os.path.exists(folder_path):
            Logger.error(f"Folder tidak ditemukan: {folder_path}")
            return []
        
        if not os.path.isdir(folder_path):
            Logger.error(f"Bukan folder: {folder_path}")
            return []
        
        # Get all image files
        image_paths = []
        supported_formats = ('.jpg', '.jpeg', '.png')
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_formats):
                full_path = os.path.join(folder_path, filename)
                image_paths.append(full_path)
        
        Logger.info(f"Ditemukan {len(image_paths)} gambar dalam folder")
        
        return image_paths
    
    def _process_uploaded_images(self, image_paths):
        """Process uploaded images dan extract embeddings"""
        embeddings = []
        
        Logger.info(f"Memproses {len(image_paths)} gambar...")
        
        for i, image_path in enumerate(image_paths):
            Logger.info(f"Processing {i+1}/{len(image_paths)}: {os.path.basename(image_path)}")
            
            # Read image
            frame = cv2.imread(image_path)
            
            if frame is None:
                Logger.warning(f"Gagal membaca gambar: {image_path}")
                continue
            
            # Resize if too large
            h, w = frame.shape[:2]
            if w > 1920 or h > 1080:
                scale = min(1920/w, 1080/h)
                new_w, new_h = int(w*scale), int(h*scale)
                frame = cv2.resize(frame, (new_w, new_h))
            
            # Detect face
            face, msg = self.detector.get_single_face(frame, self.settings.CONFIDENCE_THRESHOLD)
            
            if face is None:
                Logger.warning(f"  ✗ {msg}")
                continue
            
            # Validate quality
            is_valid, result = self.quality_checker.validate_face(frame, face)
            
            if not is_valid:
                Logger.warning(f"  ✗ {result}")
                continue
            
            # Extract embedding
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