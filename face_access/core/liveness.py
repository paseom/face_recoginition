# import numpy as np
# import cv2
# import time

# class LivenessChecker:
#     """Liveness detection: hadap kanan, kiri, kedip"""
    
#     def __init__(self, detector, quality_checker):
#         self.detector = detector
#         self.quality_checker = quality_checker
    
#     def check(self, camera):
#         """Perform liveness check (3 random actions)"""
#         actions = ['right', 'left', 'blink']
#         np.random.shuffle(actions)
        
#         print("\n=== Liveness Check ===")
        
#         for action in actions:
#             if action == 'right':
#                 print("Hadap kanan...")
#                 if not self._check_head_turn(camera, 'right'):
#                     return False
#             elif action == 'left':
#                 print("Hadap kiri...")
#                 if not self._check_head_turn(camera, 'left'):
#                     return False
#             else:
#                 print("Kedipkan mata...")
#                 if not self._check_blink(camera):
#                     return False
#             time.sleep(0.5)
        
#         print("✓ Liveness check berhasil!")
#         return True
    
#     def _check_head_turn(self, camera, direction, timeout=3):
#         """Check head turn"""
#         start = time.time()
        
#         while time.time() - start < timeout:
#             ret, frame = camera.read()
#             if not ret:
#                 continue
            
#             face, msg = self.detector.get_single_face(frame, min_confidence=0.7)
            
#             if face is not None:
#                 yaw, pitch = self.quality_checker.calculate_pose(face.kps)
                
#                 if yaw > 15:  # Turned enough
#                     return True
            
#             cv2.imshow('Liveness Check', frame)
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 return False
        
#         return False
    
#     def _check_blink(self, camera, timeout=3):
#         """Check blink (simplified)"""
#         start = time.time()
        
#         while time.time() - start < timeout:
#             ret, frame = camera.read()
#             if not ret:
#                 continue
            
#             face, msg = self.detector.get_single_face(frame, min_confidence=0.7)
            
#             if face is not None:
#                 # Simplified: just accept after detection
#                 # In production, implement eye aspect ratio
#                 return True
            
#             cv2.imshow('Liveness Check', frame)
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 return False
        
#         return True