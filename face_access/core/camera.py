import cv2

class Camera:
    """Camera handler dengan FPS control"""
    
    def __init__(self, camera_index=0, width=640, height=480, fps=30):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.target_fps = fps
        self.cap = None
    
    def open(self):
        """Open camera"""
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return self.cap.isOpened()
    
    def read(self):
        """Read frame from camera"""
        if self.cap is None:
            return False, None
        ret, frame = self.cap.read()
        if ret:
            # Resize to standard size
            frame = cv2.resize(frame, (self.width, self.height))
        return ret, frame
    
    def release(self):
        """Release camera"""
        if self.cap is not None:
            self.cap.release()
            cv2.destroyAllWindows()
    
    def is_opened(self):
        """Check if camera is opened"""
        return self.cap is not None and self.cap.isOpened()