"""
Pose Estimation Module
Extracts body keypoints using MediaPipe Pose
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Tuple, List
from config import POSE_CONFIG, KEYPOINTS


class PoseEstimator:
    """
    Extracts pose landmarks from video frames using MediaPipe
    """
    
    def __init__(self, 
                 min_detection_confidence: float = POSE_CONFIG['min_detection_confidence'],
                 min_tracking_confidence: float = POSE_CONFIG['min_tracking_confidence'],
                 model_complexity: int = POSE_CONFIG['model_complexity']):
        """
        Initialize pose estimator
        
        Args:
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
            model_complexity: Model complexity (0, 1, or 2)
        """
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[object]]:
        """
        Process a single frame and extract pose landmarks
        
        Args:
            frame: Input image frame (BGR)
            
        Returns:
            Tuple of (landmarks_array, pose_results)
            landmarks_array: numpy array of shape (33, 3) or None
            pose_results: MediaPipe pose results object or None
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.pose.process(frame_rgb)
        
        if results.pose_landmarks:
            # Extract landmarks to numpy array
            landmarks = []
            for landmark in results.pose_landmarks.landmark:
                landmarks.append([landmark.x, landmark.y, landmark.z])
            landmarks_array = np.array(landmarks)
            return landmarks_array, results
        
        return None, None
    
    def process_video(self, video_path: str) -> Tuple[List[np.ndarray], List[np.ndarray], dict]:
        """
        Process entire video and extract pose landmarks for all frames
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (frames, landmarks_sequence, video_info)
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        video_info = {
            'fps': fps,
            'total_frames': total_frames,
            'width': width,
            'height': height
        }
        
        frames = []
        landmarks_sequence = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frames.append(frame.copy())
            landmarks, _ = self.process_frame(frame)
            landmarks_sequence.append(landmarks)
        
        cap.release()
        
        return frames, landmarks_sequence, video_info
    
    def draw_landmarks(self, frame: np.ndarray, landmarks: np.ndarray, 
                      connections: bool = True) -> np.ndarray:
        """
        Draw pose landmarks on frame
        
        Args:
            frame: Input frame
            landmarks: Landmarks array (33, 3)
            connections: Whether to draw skeleton connections
            
        Returns:
            Frame with landmarks drawn
        """
        annotated_frame = frame.copy()
        h, w = frame.shape[:2]
        
        # Draw landmarks
        for i, landmark in enumerate(landmarks):
            x, y = int(landmark[0] * w), int(landmark[1] * h)
            cv2.circle(annotated_frame, (x, y), 3, (0, 255, 0), -1)
        
        if connections:
            # Draw skeleton connections
            pose_connections = self.mp_pose.POSE_CONNECTIONS
            for connection in pose_connections:
                start_idx, end_idx = connection
                if start_idx < len(landmarks) and end_idx < len(landmarks):
                    start = landmarks[start_idx]
                    end = landmarks[end_idx]
                    
                    start_point = (int(start[0] * w), int(start[1] * h))
                    end_point = (int(end[0] * w), int(end[1] * h))
                    
                    cv2.line(annotated_frame, start_point, end_point, (255, 0, 255), 2)
        
        return annotated_frame
    
    def get_joint_angle(self, landmarks: np.ndarray, 
                       point1_idx: int, point2_idx: int, point3_idx: int) -> float:
        """
        Calculate angle at point2 formed by three points
        
        Args:
            landmarks: Landmarks array
            point1_idx, point2_idx, point3_idx: Indices of the three points
            
        Returns:
            Angle in degrees
        """
        if landmarks is None or len(landmarks) <= max(point1_idx, point2_idx, point3_idx):
            return 0.0
        
        p1 = landmarks[point1_idx][:2]
        p2 = landmarks[point2_idx][:2]
        p3 = landmarks[point3_idx][:2]
        
        # Calculate vectors
        v1 = p1 - p2
        v2 = p3 - p2
        
        # Calculate angle
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        
        return np.degrees(angle)
    
    def calculate_body_angles(self, landmarks: np.ndarray) -> dict:
        """
        Calculate important body angles for golf swing analysis
        
        Args:
            landmarks: Landmarks array
            
        Returns:
            Dictionary of body angles
        """
        if landmarks is None:
            return {}
        
        angles = {}
        
        # Right arm angle (shoulder-elbow-wrist)
        angles['right_elbow'] = self.get_joint_angle(
            landmarks, KEYPOINTS['right_shoulder'], 
            KEYPOINTS['right_elbow'], KEYPOINTS['right_wrist']
        )
        
        # Left arm angle
        angles['left_elbow'] = self.get_joint_angle(
            landmarks, KEYPOINTS['left_shoulder'], 
            KEYPOINTS['left_elbow'], KEYPOINTS['left_wrist']
        )
        
        # Right knee angle
        angles['right_knee'] = self.get_joint_angle(
            landmarks, KEYPOINTS['right_hip'], 
            KEYPOINTS['right_knee'], KEYPOINTS['right_ankle']
        )
        
        # Left knee angle
        angles['left_knee'] = self.get_joint_angle(
            landmarks, KEYPOINTS['left_hip'], 
            KEYPOINTS['left_knee'], KEYPOINTS['left_ankle']
        )
        
        # Hip-shoulder angle (spine angle)
        if len(landmarks) > max(KEYPOINTS['left_hip'], KEYPOINTS['left_shoulder']):
            hip_center = (landmarks[KEYPOINTS['left_hip']][:2] + 
                         landmarks[KEYPOINTS['right_hip']][:2]) / 2
            shoulder_center = (landmarks[KEYPOINTS['left_shoulder']][:2] + 
                             landmarks[KEYPOINTS['right_shoulder']][:2]) / 2
            
            spine_vector = shoulder_center - hip_center
            vertical = np.array([0, 1])
            
            cos_angle = np.dot(spine_vector, vertical) / (np.linalg.norm(spine_vector) + 1e-6)
            angles['spine_angle'] = 90 - np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
        
        return angles
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'pose'):
            self.pose.close()
