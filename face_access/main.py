from config.settings import Settings
from core.camera import Camera
from core.detector import FaceDetector
from core.quality import QualityChecker
# from core.liveness import LivenessChecker
from core.embedding import EmbeddingExtractor
from core.matcher import FaceMatcher
from db.database import Database
from db.pegawai_repo import PegawaiRepository
from db.embedding_repo import EmbeddingRepository
from db.log_repo import LogRepository
from enrollment.enroll import Enrollment
from recognition.recognize import Recognition
from utils.logger import Logger


class FaceAccessSystem:
    """Main system class"""
    
    def __init__(self):
        """Initialize all components"""
        Logger.info("Initializing Face Access System...")
        
        # Load settings
        self.settings = Settings()
        
        # Initialize database
        self.database = Database(self.settings.DB_CONFIG)
        if not self.database.connect():
            Logger.error("Gagal koneksi ke database!")
            raise Exception("Database connection failed")
        
        # Initialize repositories
        self.pegawai_repo = PegawaiRepository(self.database)
        self.embedding_repo = EmbeddingRepository(self.database)
        self.log_repo = LogRepository(self.database)
        
        # Initialize core components
        self.detector = FaceDetector()
        self.quality_checker = QualityChecker(
            blur_threshold=self.settings.BLUR_THRESHOLD,
            yaw_threshold=self.settings.YAW_THRESHOLD,
            pitch_threshold=self.settings.PITCH_THRESHOLD
        )
        self.embedding_extractor = EmbeddingExtractor(self.detector)
        self.matcher = FaceMatcher(threshold=self.settings.RECOGNITION_SIMILARITY)
        
        # Camera will be initialized per session
        self.camera = None
        # self.liveness_checker = None
        
        Logger.success("System initialized successfully!")
    
    def _init_camera_for_enrollment(self):
        """Initialize camera untuk enrollment"""
        self.camera = Camera(
            camera_index=self.settings.CAMERA_INDEX,
            width=self.settings.CAMERA_WIDTH,
            height=self.settings.CAMERA_HEIGHT,
            fps=self.settings.ENROLLMENT_FPS
        )
        # self.liveness_checker = LivenessChecker(self.detector, self.quality_checker)
    
    def _init_camera_for_recognition(self):
        """Initialize camera untuk recognition"""
        self.camera = Camera(
            camera_index=self.settings.CAMERA_INDEX,
            width=self.settings.CAMERA_WIDTH,
            height=self.settings.CAMERA_HEIGHT,
            fps=self.settings.RECOGNITION_FPS
        )
        # self.liveness_checker = LivenessChecker(self.detector, self.quality_checker)
    
    def enroll_employee(self, nama, nip):
        """Daftarkan pegawai baru"""
        self._init_camera_for_enrollment()
        
        enrollment = Enrollment(
            camera=self.camera,
            detector=self.detector,
            quality_checker=self.quality_checker,
            # liveness_checker=self.liveness_checker,
            embedding_extractor=self.embedding_extractor,
            pegawai_repo=self.pegawai_repo,
            embedding_repo=self.embedding_repo,
            settings=self.settings
        )
        
        return enrollment.enroll(nama, nip)
    
    def recognize_face(self):
        """Face recognition untuk akses pintu"""
        self._init_camera_for_recognition()
        
        recognition = Recognition(
            camera=self.camera,
            detector=self.detector,
            quality_checker=self.quality_checker,
            # liveness_checker=self.liveness_checker,
            embedding_extractor=self.embedding_extractor,
            matcher=self.matcher,
            pegawai_repo=self.pegawai_repo,
            embedding_repo=self.embedding_repo,
            log_repo=self.log_repo,
            settings=self.settings
        )
        
        return recognition.recognize()
    
    def show_menu(self):
        """Tampilkan menu utama"""
        while True:
            print("1. Pendaftaran Pegawai Baru")
            print("2. Face Recognition (Akses Pintu)")
            print("3. Keluar")
            
            choice = input("\nPilih menu (1-3): ").strip()
            
            if choice == '1':
                self._menu_enrollment()
            elif choice == '2':
                self._menu_recognition()
            elif choice == '3':
                Logger.info("Terima kasih telah menggunakan sistem!")
                break
            else:
                Logger.warning("Pilihan tidak valid!")
    
    def _menu_enrollment(self):
        """Menu pendaftaran"""
        nama = input("Nama Lengkap: ").strip()
        nip = input("NIP: ").strip()
        
        if not nama or not nip:
            Logger.warning("Nama dan NIP tidak boleh kosong!")
            return
        
        if len(nip) != 10:
            Logger.warning("NIP harus 10 digit!")
            return
        
        Logger.info("Memulai proses pendaftaran...")
        Logger.info("Tekan 'q' untuk membatalkan")
        
        success = self.enroll_employee(nama, nip)
        
        if success:
            input("\nTekan Enter untuk kembali ke menu...")
        else:
            Logger.error("Pendaftaran gagal!")
            input("\nTekan Enter untuk kembali ke menu...")
    
    def _menu_recognition(self):
        """Menu face recognition"""        
        Logger.info("Memulai face recognition...")
        Logger.info("Tekan 'q' untuk membatalkan")
        
        success = self.recognize_face()
        
        if success:
            input("\nTekan Enter untuk kembali ke menu...")
        else:
            input("\nTekan Enter untuk kembali ke menu...")


def main():
    """Main entry point"""
    try:
        system = FaceAccessSystem()
        system.show_menu()
    except KeyboardInterrupt:
        Logger.info("\nProgram dihentikan oleh user")
    except Exception as e:
        Logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        Logger.info("Program selesai")


if __name__ == "__main__":
    main()