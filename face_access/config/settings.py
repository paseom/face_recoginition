class Settings:
    """Configuration untuk seluruh sistem"""
    
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'pegawai_bpk'
    }
    
    
    FACE_SIZE_THRESHOLD = 0.05 # Proporsi minimum ukuran wajah terhadap frame
    CONFIDENCE_THRESHOLD = 0.6 # Ambang batas confidence deteksi wajah
    MAX_FACES = 1 # Maksimum jumlah wajah yang dideteksi dalam satu frame
    
    BLUR_THRESHOLD = 60 # Ambang batas blur (0-100)
    YAW_THRESHOLD = 35 # Ambang batas kemiringan kanan-kiri (derajat)
    PITCH_THRESHOLD = 35 # Ambang batas kemiringan atas-bawah (derajat)
    EYE_LANDMARK_THRESHOLD = 0.6
    NOSE_LANDMARK_THRESHOLD = 0.6
    
    ENROLLMENT_SAMPLES = 10
    ENROLLMENT_SIMILARITY = 0.6
    RECOGNITION_SIMILARITY = 0.5
    
    REAL_TIME_CONSTRAINT = 5.0  # Timeout recognition (detik) — dikali 3 menjadi 15 detik total
    
    COOLDOWN = 5
    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 30
    
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_AUTO_DETECT = True  # Auto-detect USB camera (jika ada), default ke built-in jika tidak
    CAMERA_INDEX = 0  # Manual camera index (dipakai jika CAMERA_AUTO_DETECT=False)
    PREFER_USB_CAMERA = True  # Jika True & CAMERA_AUTO_DETECT=True, prioritas USB camera
    
    @classmethod
    def get_camera_index(cls):
        """
        Return camera index berdasarkan setting auto-detect
        
        Returns:
            int: camera index yang akan digunakan
        """
        if not cls.CAMERA_AUTO_DETECT:
            return cls.CAMERA_INDEX
        
        from utils.camera_detector import CameraDetector
        
        if cls.PREFER_USB_CAMERA:
            # Cari USB camera dulu (index > 0)
            usb_idx = CameraDetector.find_usb_camera(exclude_builtin=True)
            if usb_idx != -1:
                return usb_idx
            # Fallback ke built-in jika USB tidak ada
            return 0
        else:
            # Pakai camera pertama yang tersedia
            available = CameraDetector.get_available_cameras()
            return available[0] if available else 0

