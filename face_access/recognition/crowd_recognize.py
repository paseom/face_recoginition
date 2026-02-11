"""
Complete Crowd Detection System dengan 5-Stage Filtering & Normalization
"""

import cv2
import numpy as np
from utils.logger import Logger
from datetime import datetime
import time

class CrowdDetectionComplete:
    """
    Crowd Detection dengan 5-stage filtering:
    1. Face Detection (RetinaFace + NMS)
    2. Face Size Check
    3. Blur Detection
    4. Pose Estimation (Yaw, Pitch, Roll)
    5. Landmark Quality
    """
    
    def __init__(self, detector, embedding_extractor, matcher, 
                 pegawai_repo, embedding_repo, log_repo, settings):
        self.detector = detector
        self.embedding_extractor = embedding_extractor
        self.matcher = matcher
        self.pegawai_repo = pegawai_repo
        self.embedding_repo = embedding_repo
        self.log_repo = log_repo
        self.settings = settings
        
        # Stage 1: Face Detection Thresholds
        self.CONFIDENCE_THRESHOLD = 0.3
        
        # Stage 2: Face Size Thresholds
        self.FACE_SIZE_THRESHOLD = 0.01 # 5% dari frame
        
        # Stage 3: Blur Detection
        self.BLUR_INDOOR = 40
        self.BLUR_OUTDOOR = 60
        
        # Stage 4: Pose Thresholds
        self.YAW_THRESHOLD = 35    # degrees
        self.PITCH_THRESHOLD = 35  # degrees
        self.ROLL_THRESHOLD = 35   # degrees
        
        # Stage 5: Landmark Quality
        self.EYE_CONFIDENCE = 0.5
        self.NOSE_CONFIDENCE = 0.4
        self.MOUTH_CONFIDENCE = 0.4
        self.OUTLINE_THRESHOLD = 0.5 
        
        # Face Alignment
        self.LANDMARK_CONFIDENCE = 0.5
        self.MIN_INTER_EYE_DISTANCE = 30  # pixels
        self.MAX_REPROJECTION_ERROR = 5   # pixels
        
        # Recognition
        self.SIMILARITY_THRESHOLD = 0.5
    
    def detect_from_video(
        self,
        video_source,
        output_path=None,
        is_outdoor=False,
        sample_fps=5,
        duration_sec=None,
        source_type="VIDEO"
    ):
        """
        Main detection dari video/webcam
        
        Args:
            video_source: Path video atau 0 untuk webcam
            output_path: Path output video (optional)
            is_outdoor: True jika outdoor (blur threshold lebih tinggi)
            sample_fps: Process N frame per second
            duration_sec: Stop processing after N seconds (optional)
        """
        Logger.info(f"Starting crowd detection from video: {video_source}")
        
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            Logger.error("Failed to open video source")
            return None
        
        # Video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            # Webcam/device streams can return 0 FPS metadata.
            fps = 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        Logger.info(f"Video: {width}x{height} @ {fps}fps")
        
        # Video writer
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Set blur threshold based on environment
        blur_threshold = self.BLUR_OUTDOOR if is_outdoor else self.BLUR_INDOOR
        
        # Tracking
        detection_log = []  # Log semua deteksi
        unique_people = {}  # Track unique people
        filtered_totals = {
            'stage0_no_face': 0,
            'stage1_detection': 0,
            'stage2_size': 0,
            'stage3_blur': 0,
            'stage4_pose': 0,
            'stage5_landmark': 0
        }
        frame_count = 0
        sampled_frame_count = 0
        sample_fps = max(1, int(sample_fps))
        process_interval = max(1, fps // sample_fps)  # Process every N frames
        start_time = time.time()
        
        while True:
            if duration_sec and (time.time() - start_time) >= duration_sec:
                Logger.info(f"Reached duration limit: {duration_sec}s")
                break

            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Sample frames
            if frame_count % process_interval != 0:
                if writer:
                    writer.write(frame)
                continue
            
            # Process frame dengan 5-stage filtering
            result = self._process_frame_5stage(
                frame, 
                frame_count, 
                blur_threshold
            )
            sampled_frame_count += 1
            for key in filtered_totals:
                filtered_totals[key] += result['filtered'].get(key, 0)
            
            # Log detections
            timestamp = datetime.now()
            for person in result['detected']:
                detection_log.append({
                    'frame': frame_count,
                    'timestamp': timestamp,
                    'id_pegawai': person['id_pegawai'],
                    'nama': person['nama'],
                    'nip': person['nip'],
                    'similarity': person['similarity'],
                    'bbox': person['bbox']
                })
                
                # Track unique people
                id_peg = person['id_pegawai']
                if id_peg not in unique_people:
                    unique_people[id_peg] = {
                        'nama': person['nama'],
                        'nip': person['nip'],
                        'first_seen': frame_count,
                        'last_seen': frame_count,
                        'count': 0
                    }
                unique_people[id_peg]['last_seen'] = frame_count
                unique_people[id_peg]['count'] += 1

                # Persist crowd detection to DB (no frame/similarity in table schema)
                try:
                    self.log_repo.log_crowd_detection(
                        id_pegawai=person['id_pegawai'],
                        nama=person['nama'],
                        nip=person['nip'],
                        source_type=source_type
                    )
                except Exception as e:
                    Logger.error(f"Failed to write crowd_log: {e}")
            
            # Write annotated frame
            if writer:
                writer.write(result['annotated_frame'])
            
            # Display
            cv2.imshow('Crowd Detection', result['annotated_frame'])
            if cv2.waitKey(1) & 0xFF == ord('q'):
                Logger.warning("Stopped by user")
                break
        
        # Cleanup
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        
        # Summary
        summary = {
            'total_frames': frame_count,
            'processed_frames': sampled_frame_count,
            'unique_people': len(unique_people),
            'people': list(unique_people.values()),
            'detection_log': detection_log,
            'filter_summary': filtered_totals,
            'failure_reasons': self._build_failure_reasons(filtered_totals, sampled_frame_count)
        }

        # Tetap catat percobaan crowd meskipun tidak ada wajah yang recognized.
        if len(detection_log) == 0:
            try:
                self.log_repo.log_crowd_detection(
                    id_pegawai=None,
                    nama=None,
                    nip=None,
                    source_type=source_type
                )
            except Exception as e:
                Logger.error(f"Failed to write unknown crowd_log: {e}")
        
        Logger.success(f"Detection complete! Unique people: {len(unique_people)}")
        
        return summary

    def detect_from_image(self, image_source, is_outdoor=False, source_type="IMAGE"):
        """
        Detection dari satu gambar.

        Args:
            image_source: Path gambar
            is_outdoor: True jika outdoor (blur threshold lebih tinggi)
        """
        frame = cv2.imread(image_source)
        if frame is None:
            Logger.error("Failed to read image source")
            return None

        blur_threshold = self.BLUR_OUTDOOR if is_outdoor else self.BLUR_INDOOR
        result = self._process_frame_5stage(frame, frame_num=1, blur_threshold=blur_threshold)

        unique_people = {}
        detection_log = []
        timestamp = datetime.now()
        for person in result['detected']:
            id_peg = person['id_pegawai']
            unique_people[id_peg] = {
                'nama': person['nama'],
                'nip': person['nip'],
                'first_seen': 1,
                'last_seen': 1,
                'count': 1
            }
            detection_log.append({
                'frame': 1,
                'timestamp': timestamp,
                'id_pegawai': person['id_pegawai'],
                'nama': person['nama'],
                'nip': person['nip'],
                'similarity': person['similarity'],
                'bbox': person['bbox']
            })
            try:
                self.log_repo.log_crowd_detection(
                    id_pegawai=person['id_pegawai'],
                    nama=person['nama'],
                    nip=person['nip'],
                    source_type=source_type
                )
            except Exception as e:
                Logger.error(f"Failed to write crowd_log: {e}")

        filter_summary = {
            'stage0_no_face': result['filtered'].get('stage0_no_face', 0),
            'stage1_detection': result['filtered'].get('stage1_detection', 0),
            'stage2_size': result['filtered'].get('stage2_size', 0),
            'stage3_blur': result['filtered'].get('stage3_blur', 0),
            'stage4_pose': result['filtered'].get('stage4_pose', 0),
            'stage5_landmark': result['filtered'].get('stage5_landmark', 0)
        }

        if len(detection_log) == 0:
            try:
                self.log_repo.log_crowd_detection(
                    id_pegawai=None,
                    nama=None,
                    nip=None,
                    source_type=source_type
                )
            except Exception as e:
                Logger.error(f"Failed to write unknown crowd_log: {e}")

        return {
            'total_frames': 1,
            'processed_frames': 1,
            'unique_people': len(unique_people),
            'people': list(unique_people.values()),
            'detection_log': detection_log,
            'filter_summary': filter_summary,
            'failure_reasons': self._build_failure_reasons(filter_summary, 1)
        }
    
    def _process_frame_5stage(self, frame, frame_num, blur_threshold):
        """
        Process single frame dengan 5-stage filtering
        """
        h, w = frame.shape[:2]
        frame_area = h * w
        
        detected_people = []
        filtered_out = {
            'stage0_no_face': 0,
            'stage1_detection': 0,
            'stage2_size': 0,
            'stage3_blur': 0,
            'stage4_pose': 0,
            'stage5_landmark': 0
        }
        
        # STAGE 1: Face Detection (RetinaFace + NMS built-in)
        faces = self.detector.detect(frame)
        
        if len(faces) == 0:
            filtered_out['stage0_no_face'] = 1
        
        # Get stored embeddings once
        stored_embeddings = self.embedding_repo.get_all()
        
        for face in faces:
            bbox = face.bbox
            x1, y1, x2, y2 = bbox.astype(int)
            
            # Check confidence
            if face.det_score < self.CONFIDENCE_THRESHOLD:
                filtered_out['stage1_detection'] += 1
                self._draw_box(frame, bbox, "LOW CONF", (128, 128, 128))
                continue
            
            # STAGE 2: Face Size Check
            face_area = (x2 - x1) * (y2 - y1)
            size_ratio = face_area / frame_area
            
            if size_ratio < self.FACE_SIZE_THRESHOLD:
                filtered_out['stage2_size'] += 1
                self._draw_box(frame, bbox, "TOO SMALL", (255, 255, 0))
                continue
            
            # Extract face region
            face_img = frame[y1:y2, x1:x2]
            if face_img.size == 0:
                continue
            
            # STAGE 3: Blur Detection
            blur_score = self._calculate_blur(face_img)
            
            if blur_score < blur_threshold:
                filtered_out['stage3_blur'] += 1
                self._draw_box(frame, bbox, f"BLUR ({blur_score:.0f})", (255, 165, 0))
                continue
            
            # STAGE 4: Pose Estimation (Yaw, Pitch, Roll)
            yaw, pitch, roll = self._calculate_pose_complete(face.kps)
            
            if (yaw > self.YAW_THRESHOLD or 
                pitch > self.PITCH_THRESHOLD or 
                roll > self.ROLL_THRESHOLD):
                filtered_out['stage4_pose'] += 1
                self._draw_box(frame, bbox, f"BAD POSE", (255, 100, 100))
                continue
            
            # STAGE 5: Landmark Quality Check
            landmark_quality = self._check_landmark_quality(face)
            
            if not landmark_quality['pass']:
                filtered_out['stage5_landmark'] += 1
                self._draw_box(frame, bbox, landmark_quality['reason'], (200, 200, 0))
                continue
            
            # ALL STAGES PASSED - Proceed to normalization & recognition
            
            # Normalization
            normalized_face = self._normalize_face(face_img)
            
            # Face Alignment (already done by InsightFace internally)
            # But we validate alignment quality
            if not self._validate_alignment(face):
                self._draw_box(frame, bbox, "ALIGN FAIL", (180, 180, 180))
                continue
            
            # Extract embedding (ArcFace via InsightFace)
            embedding = face.normed_embedding
            
            # Match with database
            employee_id, similarity = self.matcher.match(embedding, stored_embeddings)
            
            # Draw result
            if employee_id and similarity >= self.SIMILARITY_THRESHOLD:
                # RECOGNIZED - Green box
                employee = self.pegawai_repo.get_by_id(employee_id)
                
                detected_people.append({
                    'id_pegawai': employee_id,
                    'nama': employee['nama'],
                    'nip': employee['nip'],
                    'similarity': similarity,
                    'bbox': bbox
                })
                
                self._draw_recognized(frame, bbox, employee['nama'], similarity)
            else:
                # UNKNOWN - Red box
                self._draw_unknown(frame, bbox, similarity)
        
        # Draw summary
        self._draw_summary(frame, len(detected_people), filtered_out)
        
        return {
            'detected': detected_people,
            'filtered': filtered_out,
            'annotated_frame': frame
        }

    def _build_failure_reasons(self, filter_summary, sampled_frame_count):
        reason_map = {
            'stage0_no_face': "Wajah tidak terdeteksi (posisi terlalu jauh/sudut tidak pas)",
            'stage1_detection': "Deteksi wajah lemah (confidence rendah)",
            'stage2_size': "Wajah terlalu kecil di frame",
            'stage3_blur': "Gambar blur / tidak fokus",
            'stage4_pose': "Pose wajah tidak frontal (yaw/pitch/roll tinggi)",
            'stage5_landmark': "Fitur wajah tidak lengkap / landmark tidak stabil"
        }

        reasons = []
        base = max(1, int(sampled_frame_count))
        for key, label in reason_map.items():
            count = int(filter_summary.get(key, 0))
            if count > 0:
                reasons.append({
                    'stage': key,
                    'reason': label,
                    'count': count,
                    'ratio': round(count / base, 3)
                })

        reasons.sort(key=lambda x: x['count'], reverse=True)
        return reasons
    
    def _calculate_blur(self, image):
        """Stage 3: Laplacian Variance untuk blur detection"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    def _calculate_pose_complete(self, landmarks):
        """
        Stage 4: Calculate Yaw, Pitch, Roll dari landmarks
        
        Simplified pose estimation using facial landmarks
        """
        # Get key points
        left_eye = landmarks[0]
        right_eye = landmarks[1]
        nose = landmarks[2]
        left_mouth = landmarks[3]
        right_mouth = landmarks[4]
        
        # Calculate eye center
        eye_center = (left_eye + right_eye) / 2
        
        # YAW (left-right rotation)
        eye_diff = right_eye[0] - left_eye[0]
        yaw = np.arctan2(nose[0] - eye_center[0], eye_diff) * 180 / np.pi
        
        # PITCH (up-down rotation)
        pitch = np.arctan2(nose[1] - eye_center[1], eye_diff) * 180 / np.pi
        
        # ROLL (tilt rotation)
        roll = np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]) * 180 / np.pi
        
        return abs(yaw), abs(pitch), abs(roll)
    
    def _check_landmark_quality(self, face):
        """
        Stage 5: Check landmark quality
        
        InsightFace provides landmarks with confidence scores
        We validate key facial features are clearly visible
        """
        # This is simplified - InsightFace handles this internally
        # In production, you'd check actual landmark detection scores
        
        landmarks = face.kps
        
        # Check if all 5 key landmarks are detected
        if len(landmarks) < 5:
            return {'pass': False, 'reason': 'MISSING LANDMARKS'}
        
        # Check inter-eye distance (proxy for face clarity)
        left_eye = landmarks[0]
        right_eye = landmarks[1]
        eye_distance = np.linalg.norm(right_eye - left_eye)
        
        if eye_distance < self.MIN_INTER_EYE_DISTANCE:
            return {'pass': False, 'reason': 'FACE TOO FAR'}
        
        # All checks passed
        return {'pass': True, 'reason': 'OK'}
    
    def _normalize_face(self, face_img):
        """
        Normalization dengan CLAHE atau Gamma Correction
        """
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        
        mean_brightness = np.mean(gray)
        std_contrast = np.std(gray)
        
        # Decide normalization strategy
        if std_contrast < 40 and 80 <= mean_brightness <= 180:
            # Low contrast, normal brightness → CLAHE
            normalized = self._apply_clahe(face_img)
        elif mean_brightness < 80:
            # Too dark → Gamma correction (brighten)
            normalized = self._apply_gamma(face_img, gamma=0.85)
        elif mean_brightness > 180:
            # Too bright → Gamma correction (darken)
            normalized = self._apply_gamma(face_img, gamma=1.15)
        else:
            # Good quality, no normalization needed
            normalized = face_img
        
        return normalized
    
    def _apply_clahe(self, image, clip_limit=2.0, tile_grid_size=(8, 8)):
        """Apply CLAHE for contrast enhancement"""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        l_clahe = clahe.apply(l)
        
        # Merge back
        lab_clahe = cv2.merge([l_clahe, a, b])
        result = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
        
        return result
    
    def _apply_gamma(self, image, gamma=1.0):
        """Apply gamma correction"""
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 
                         for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)
    
    def _validate_alignment(self, face):
        """
        Validate face alignment quality
        
        InsightFace does alignment internally, we just validate it's acceptable
        """
        landmarks = face.kps
        
        # Check landmark confidence (simplified)
        # In production, InsightFace provides landmark scores
        
        # Check inter-eye distance
        left_eye = landmarks[0]
        right_eye = landmarks[1]
        eye_distance = np.linalg.norm(right_eye - left_eye)
        
        if eye_distance < self.MIN_INTER_EYE_DISTANCE:
            return False
        
        # All checks OK
        return True
    
    def _draw_box(self, frame, bbox, label, color):
        """Draw bounding box dengan label"""
        x1, y1, x2, y2 = bbox.astype(int)
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Label background
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, y1-label_h-10), (x1+label_w, y1), color, -1)
        
        # Label text
        cv2.putText(frame, label, (x1, y1-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def _draw_recognized(self, frame, bbox, nama, similarity):
        """Draw green box untuk recognized person"""
        x1, y1, x2, y2 = bbox.astype(int)
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        label = f"{nama} ({similarity:.2f})"
        
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1-label_h-10), (x1+label_w, y1), (0, 255, 0), -1)
        
        cv2.putText(frame, label, (x1, y1-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    def _draw_unknown(self, frame, bbox, similarity):
        """Draw red box untuk unknown person"""
        x1, y1, x2, y2 = bbox.astype(int)
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        label = f"UNKNOWN ({similarity:.2f})" if similarity > 0 else "UNKNOWN"
        
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1-label_h-10), (x1+label_w, y1), (0, 0, 255), -1)
        
        cv2.putText(frame, label, (x1, y1-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def _draw_summary(self, frame, detected_count, filtered):
        """Draw summary statistics"""
        y_offset = 30
        
        # Detected count
        cv2.putText(frame, f"Detected: {detected_count}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y_offset += 30
        
        # Filtered stats
        total_filtered = sum(filtered.values())
        cv2.putText(frame, f"Filtered: {total_filtered}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        y_offset += 25
        
        # Breakdown
        for stage, count in filtered.items():
            if count > 0:
                stage_name = stage.replace('stage', 'S').replace('_', ' ')
                cv2.putText(frame, f"  {stage_name}: {count}", (15, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                y_offset += 20
    
    def generate_detection_report(self, summary, output_file=None):
        """Generate comprehensive detection report"""
        report_lines = []
        report_lines.append("="*70)
        report_lines.append("CROWD DETECTION REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("="*70)
        report_lines.append("")
        
        report_lines.append(f"Total Frames Processed: {summary['total_frames']}")
        report_lines.append(f"Detections Made: {summary['processed_frames']}")
        report_lines.append(f"Unique People: {summary['unique_people']}")
        report_lines.append("")
        report_lines.append("-"*70)
        report_lines.append("DETECTED PEOPLE:")
        report_lines.append("-"*70)
        
        for person in summary['people']:
            report_lines.append(f"\n{person['nama']} (NIP: {person['nip']})")
            report_lines.append(f"  First Seen: Frame {person['first_seen']}")
            report_lines.append(f"  Last Seen: Frame {person['last_seen']}")
            report_lines.append(f"  Appearances: {person['count']} times")
        
        report_lines.append("")
        report_lines.append("="*70)
        report_lines.append("DETECTION LOG (Chronological):")
        report_lines.append("="*70)
        
        for log in summary['detection_log']:
            report_lines.append(
                f"Frame {log['frame']:5d} | {log['timestamp'].strftime('%H:%M:%S')} | "
                f"{log['nama']:20s} | Sim: {log['similarity']:.3f}"
            )
        
        report_lines.append("="*70)
        
        report_text = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            Logger.success(f"Report saved: {output_file}")
        
        print(report_text)
        
        return report_text
    
    
