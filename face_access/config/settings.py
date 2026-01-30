class Settings:
    """Configuration untuk seluruh sistem"""
    
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'pegawai_bpk'
    }
    
    ENROLLMENT_FPS = 10 # Frame per second untuk enrollment
    RECOGNITION_FPS = 5 # Frame per second untuk recognition
    
    FACE_SIZE_THRESHOLD = 0.05 # Proporsi minimum ukuran wajah terhadap frame
    CONFIDENCE_THRESHOLD = 0.6 # Ambang batas confidence deteksi wajah
    MAX_FACES = 1 # Maksimum jumlah wajah yang dideteksi dalam satu frame
    
    BLUR_THRESHOLD = 60 # Ambang batas blur (0-100)
    YAW_THRESHOLD = 35 # Ambang batas kemiringan kanan-kiri (derajat)
    PITCH_THRESHOLD = 35 # Ambang batas kemiringan atas-bawah (derajat)
    EYE_LANDMARK_THRESHOLD = 0.6
    NOSE_LANDMARK_THRESHOLD = 0.6
    
    ENROLLMENT_SAMPLES = 10
    ENROLLMENT_SIMILARITY = 0.7
    RECOGNITION_SIMILARITY = 0.5
    
    REAL_TIME_CONSTRAINT = 5.0  # Timeout recognition (detik) — dikali 3 menjadi 15 detik total
    
    COOLDOWN = 5
    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 30
    
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_INDEX = 0
