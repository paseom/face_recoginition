import cv2
from utils.logger import Logger


class CameraDetector:
    """Detect available cameras dan pilih yang cocok"""
    
    @staticmethod
    def get_available_cameras(max_cameras=5):
        """
        Scan dan return list index camera yang tersedia
        
        Args:
            max_cameras: max index camera untuk di-scan (default 5)
            
        Returns:
            list: index camera yang tersedia, misal [0, 1]
        """
        available = []
        
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        
        return available
    
    @staticmethod
    def find_usb_camera(exclude_builtin=True):
        """
        Cari USB camera (biasanya index > 0)
        
        Args:
            exclude_builtin: jika True, skip index 0 (built-in webcam)
            
        Returns:
            int: index USB camera pertama yang tersedia, atau -1 jika tidak ada
        """
        available = CameraDetector.get_available_cameras()
        
        if exclude_builtin:
            # skip index 0 (built-in), ambil yang pertama setelah itu
            for idx in available:
                if idx > 0:
                    return idx
            return -1
        else:
            return available[0] if available else -1
    
    @staticmethod
    def print_camera_info():
        """Print info semua camera yang tersedia"""
        available = CameraDetector.get_available_cameras()
        
        if not available:
            Logger.warning("Tidak ada camera terdeteksi!")
            return
        
        Logger.info(f"Found {len(available)} camera(s):")
        for idx in available:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)
                Logger.info(f"  Camera {idx}: {int(width)}x{int(height)} @ {int(fps)} fps")
                cap.release()
    
    @staticmethod
    def validate_camera(camera_index):
        """Check apakah camera index valid dan bisa dibuka"""
        cap = cv2.VideoCapture(camera_index)
        is_valid = cap.isOpened()
        cap.release()
        return is_valid
