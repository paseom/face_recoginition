class Settings:
    """Configuration untuk seluruh sistem"""
    
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'pegawai_bpk'
    }
    
    ENROLLMENT_FPS = 10
    RECOGNITION_FPS = 5
    
    FACE_SIZE_THRESHOLD = 0.05  
    CONFIDENCE_THRESHOLD = 0.6
    MAX_FACES = 1
    
    BLUR_THRESHOLD = 60
    YAW_THRESHOLD = 35
    PITCH_THRESHOLD = 35
    EYE_LANDMARK_THRESHOLD = 0.6
    NOSE_LANDMARK_THRESHOLD = 0.6
    
    ENROLLMENT_SAMPLES = 10
    ENROLLMENT_SIMILARITY = 0.7
    RECOGNITION_SIMILARITY = 0.6
    
    REAL_TIME_CONSTRAINT = 1.0
    
    COOLDOWN = 5
    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 30
    
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_INDEX = 0
