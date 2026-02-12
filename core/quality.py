import cv2
import numpy as np

class QualityChecker:
    """Quality checks: blur, pose, landmarks"""
    
    def __init__(self, blur_threshold=100, yaw_threshold=25, pitch_threshold=25):
        self.blur_threshold = blur_threshold
        self.yaw_threshold = yaw_threshold
        self.pitch_threshold = pitch_threshold
    
    def check_blur(self, face_img):
        """Check blur using Laplacian variance"""
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if blur_score < self.blur_threshold:
            return False, f"Blur terdeteksi (score: {blur_score:.1f}). Hold still!"
        
        return True, blur_score
    
    def calculate_pose(self, landmarks):
        """Calculate head pose (yaw, pitch) from landmarks"""
        left_eye = landmarks[0]
        right_eye = landmarks[1]
        nose = landmarks[2]
        
        eye_center = (left_eye + right_eye) / 2
        eye_diff = right_eye[0] - left_eye[0]
        
        yaw = np.arctan2(nose[0] - eye_center[0], eye_diff) * 180 / np.pi
        pitch = np.arctan2(nose[1] - eye_center[1], eye_diff) * 180 / np.pi
        
        return abs(yaw), abs(pitch)
    
    def check_pose(self, landmarks):
        """Check if pose is frontal"""
        yaw, pitch = self.calculate_pose(landmarks)
        
        if yaw > self.yaw_threshold or pitch > self.pitch_threshold:
            return False, f"Hadap ke depan (yaw: {yaw:.1f}°, pitch: {pitch:.1f}°)"
        
        return True, (yaw, pitch)
    
    def check_face_size(self, bbox, frame_shape):
        """Check if face is large enough"""
        face_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        frame_area = frame_shape[0] * frame_shape[1]
        ratio = face_area / frame_area
        
        if ratio < 0.05:
            return False, "Mendekat ke kamera"
        
        return True, ratio
    
    def validate_face(self, frame, face):
        """Comprehensive face validation"""
        valid, result = self.check_face_size(face.bbox, frame.shape)
        if not valid:
            return False, result
        
        bbox = face.bbox.astype(int)
        x1, y1, x2, y2 = max(0, bbox[0]), max(0, bbox[1]), bbox[2], bbox[3]
        face_img = frame[y1:y2, x1:x2]
        
        if face_img.size == 0:
            return False, "Error cropping face"
        
        valid, result = self.check_blur(face_img)
        if not valid:
            return False, result
        
        valid, result = self.check_pose(face.kps)
        if not valid:
            return False, result
        
        return True, "OK"