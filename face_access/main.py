"""
Face Recognition Door Access System
Entry point untuk sistem
"""

from config.settings import Settings
from core.camera import Camera
from core.detector import FaceDetector
from core.quality import QualityChecker
from core.embedding import EmbeddingExtractor
from core.matcher import FaceMatcher
from db.database import Database
from db.pegawai_repo import PegawaiRepository
from db.embedding_repo import EmbeddingRepository
from db.log_repo import LogRepository
from enrollment.enroll import Enrollment
from recognition.recognize import Recognition
from recognition.crowd_recognize import CrowdDetectionComplete
from utils.logger import Logger


class FaceAccessSystem:
    def __init__(self):
        Logger.info("Initializing Face Access System...")

        self.settings = Settings()

        self.database = Database(self.settings.DB_CONFIG)
        if not self.database.connect():
            raise Exception("Database connection failed")

        self.pegawai_repo = PegawaiRepository(self.database)
        self.embedding_repo = EmbeddingRepository(self.database)
        self.log_repo = LogRepository(self.database)

        self.detector = FaceDetector()
        self.quality_checker = QualityChecker(
            blur_threshold=self.settings.BLUR_THRESHOLD,
            yaw_threshold=self.settings.YAW_THRESHOLD,
            pitch_threshold=self.settings.PITCH_THRESHOLD
        )
        self.embedding_extractor = EmbeddingExtractor(self.detector)
        self.matcher = FaceMatcher(threshold=self.settings.RECOGNITION_SIMILARITY)

        self.camera = None
        self.recognition_instance = None

        self.crowd_detector = CrowdDetectionComplete(
            detector=self.detector,
            embedding_extractor=self.embedding_extractor,
            matcher=self.matcher,
            pegawai_repo=self.pegawai_repo,
            embedding_repo=self.embedding_repo,
            log_repo=self.log_repo,
            settings=self.settings
        )

        Logger.success("System initialized successfully!")

    def _init_camera_for_enrollment(self):
        self.camera = Camera(
            camera_index=self.settings.CAMERA_INDEX,
            width=self.settings.CAMERA_WIDTH,
            height=self.settings.CAMERA_HEIGHT
        )

    def _init_camera_for_recognition(self):
        self.camera = Camera(
            camera_index=self.settings.CAMERA_INDEX,
            width=self.settings.CAMERA_WIDTH,
            height=self.settings.CAMERA_HEIGHT
        )

    def enroll_employee(self, nama, nip, mode='video', image_paths=None):
        if mode == 'video':
            self._init_camera_for_enrollment()

        enrollment = Enrollment(
            camera=self.camera,
            detector=self.detector,
            quality_checker=self.quality_checker,
            embedding_extractor=self.embedding_extractor,
            pegawai_repo=self.pegawai_repo,
            embedding_repo=self.embedding_repo,
            settings=self.settings
        )

        return enrollment.enroll(nama, nip, mode, image_paths)

    def recognize_face(self):
        self._init_camera_for_recognition()

        self.recognition_instance = Recognition(
            camera=self.camera,
            detector=self.detector,
            quality_checker=self.quality_checker,
            embedding_extractor=self.embedding_extractor,
            matcher=self.matcher,
            pegawai_repo=self.pegawai_repo,
            embedding_repo=self.embedding_repo,
            log_repo=self.log_repo,
            settings=self.settings
        )

        return self.recognition_instance.recognize()

    def recognize_from_crowd_video(
        self,
        video_source,
        output_path=None,
        is_outdoor=False,
        sample_fps=5,
        duration_sec=None,
        source_type="VIDEO"
    ):
        # `duration_sec` and `source_type` are kept for backward compatibility
        # with older callers that still pass these arguments.
        return self.crowd_detector.detect_from_video(
            video_source=video_source,
            output_path=output_path,
            is_outdoor=is_outdoor,
            sample_fps=sample_fps,
            duration_sec=duration_sec,
            source_type=source_type
        )

    def show_menu(self):
        while True:
            print("\n" + "=" * 60)
            print("FACE ACCESS SYSTEM")
            print("=" * 60)
            print("1. Pendaftaran Pegawai")
            print("2. Face Recognition")
            print("3. Crowd Recognition (Video/CCTV)")
            print("4. Keluar")

            choice = input("Pilih (1-4): ").strip()

            if choice == '1':
                self._menu_enrollment()
            elif choice == '2':
                self._menu_recognition()
            elif choice == '3':
                self._menu_crowd_recognition()
            elif choice == '4':
                break

    def _menu_enrollment(self):
        nama = input("Nama: ").strip()
        nip = input("NIP: ").strip()
        self.enroll_employee(nama, nip, mode='video')

    def _menu_recognition(self):
        self.recognize_face()

    def recognize_from_crowd_image(self, image_path, is_outdoor=False, source_type="IMAGE"):
        return self.crowd_detector.detect_from_image(
            image_source=image_path,
            is_outdoor=is_outdoor,
            source_type=source_type
        )

    def recognize_from_crowd_video_legacy(
        self,
        video_source,
        duration_sec=None,
        is_outdoor=False,
        source_type="VIDEO"
    ):
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            raise ValueError("Video/Webcam tidak bisa dibuka")

        start_time = time.time()
        processed_frames = 0
        people_summary = {}

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            processed_frames += 1

            detections = self.crowd_detector.detect_and_recognize(
                frame,
                is_outdoor=is_outdoor
            )

            for d in detections:
                key = d["id_pegawai"]
                if key not in people_summary:
                    people_summary[key] = {
                        "nama": d["nama"],
                        "nip": d["nip"],
                        "count": 0
                    }
                people_summary[key]["count"] += 1

                # simpan log
                self.crowd_log_repo.insert(
                    id_pegawai=d["id_pegawai"],
                    nama=d["nama"],
                    nip=d["nip"],
                    source_type=source_type
                )

            if duration_sec and (time.time() - start_time) >= duration_sec:
                break

        cap.release()

        return {
            "processed_frames": processed_frames,
            "unique_people": len(people_summary),
            "people": list(people_summary.values())
        }

def main():
    system = FaceAccessSystem()
    system.show_menu()


if __name__ == "__main__":
    main()

