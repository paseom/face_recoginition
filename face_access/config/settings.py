class Settings:
    """Configuration untuk seluruh sistem"""
    
    # Database
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'pegawai_bpk'
    }
    
    # FPS Settings
    ENROLLMENT_FPS = 10
    RECOGNITION_FPS = 5
    
    # Face Detection Thresholds
    FACE_SIZE_THRESHOLD = 0.05  # 5% dari frame
    CONFIDENCE_THRESHOLD = 0.6
    MAX_FACES = 1  # Only 1 face allowed
    
    # Quality Filters
    BLUR_THRESHOLD = 60  # Laplacian variance
    YAW_THRESHOLD = 30    # degrees
    PITCH_THRESHOLD = 30  # degrees
    EYE_LANDMARK_THRESHOLD = 0.7
    NOSE_LANDMARK_THRESHOLD = 0.7
    
    # Embedding & Similarity
    ENROLLMENT_SAMPLES = 10  # 5-10 embeddings
    ENROLLMENT_SIMILARITY = 0.7
    RECOGNITION_SIMILARITY = 0.6
    
    # Real-time Constraints
    REAL_TIME_CONSTRAINT = 1.0  # seconds
    
    # Security
    COOLDOWN = 5  # seconds between attempts
    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 30  # seconds
    
    # Camera
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_INDEX = 0
