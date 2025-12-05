"""
Biomechanical Analysis Module
Analyzes golf swing mechanics and calculates performance metrics
"""

import numpy as np
from typing import List, Dict, Tuple
from scipy.spatial.distance import euclidean
from scipy.signal import savgol_filter
from config import BIOMECHANICS, KEYPOINTS


class BiomechanicalAnalyzer:
    """
    Analyzes biomechanical aspects of golf swing
    """
    
    def __init__(self):
        """Initialize biomechanical analyzer"""
        self.keypoints = KEYPOINTS
        
    def calculate_swing_plane(self, landmarks_sequence: List[np.ndarray],
                              key_positions: dict) -> dict:
        """
        Calculate swing plane using hand/club positions
        
        Args:
            landmarks_sequence: Sequence of pose landmarks
            key_positions: Key swing positions (address, top, impact, finish)
            
        Returns:
            Dictionary with swing plane metrics
        """
        # Use right wrist as club proxy (assuming right-handed)
        wrist_idx = self.keypoints['right_wrist']
        shoulder_idx = self.keypoints['right_shoulder']
        
        # Extract wrist positions during swing
        wrist_positions = []
        shoulder_positions = []
        
        address_frame = key_positions.get('address', 0)
        finish_frame = key_positions.get('finish', len(landmarks_sequence) - 1)
        
        for i in range(address_frame, min(finish_frame + 1, len(landmarks_sequence))):
            if landmarks_sequence[i] is not None:
                if len(landmarks_sequence[i]) > wrist_idx:
                    wrist_positions.append(landmarks_sequence[i][wrist_idx])
                if len(landmarks_sequence[i]) > shoulder_idx:
                    shoulder_positions.append(landmarks_sequence[i][shoulder_idx])
        
        if len(wrist_positions) < 3:
            return {'swing_plane_angle': 0, 'plane_consistency': 0, 'plane_deviation': 0}
        
        wrist_positions = np.array(wrist_positions)
        
        # Fit plane to wrist positions using PCA
        centered = wrist_positions - np.mean(wrist_positions, axis=0)
        _, _, vh = np.linalg.svd(centered)
        normal = vh[2]  # Normal to the plane
        
        # Calculate plane angle relative to horizontal
        horizontal = np.array([1, 0, 0])
        plane_angle = np.degrees(np.arccos(np.abs(np.dot(normal, horizontal)) / 
                                           (np.linalg.norm(normal) + 1e-6)))
        
        # Calculate consistency (how well points fit the plane)
        distances = np.abs(np.dot(centered, normal))
        plane_deviation = np.std(distances)
        plane_consistency = max(0, 100 - plane_deviation * 1000)
        
        return {
            'swing_plane_angle': plane_angle,
            'plane_consistency': plane_consistency,
            'plane_deviation': plane_deviation,
            'ideal_angle': BIOMECHANICS['ideal_swing_plane_angle'],
            'angle_error': abs(plane_angle - BIOMECHANICS['ideal_swing_plane_angle'])
        }
    
    def calculate_rotation_metrics(self, landmarks_sequence: List[np.ndarray],
                                   key_positions: dict) -> dict:
        """
        Calculate hip and shoulder rotation metrics
        
        Args:
            landmarks_sequence: Sequence of pose landmarks
            key_positions: Key swing positions
            
        Returns:
            Dictionary with rotation metrics
        """
        results = {
            'hip_rotation': [],
            'shoulder_rotation': [],
            'max_hip_rotation': 0,
            'max_shoulder_rotation': 0,
            'rotation_sequence_score': 0
        }
        
        # Get address position for reference
        address_frame = key_positions.get('address', 0)
        if (address_frame >= len(landmarks_sequence) or 
            landmarks_sequence[address_frame] is None):
            return results
        
        address_landmarks = landmarks_sequence[address_frame]
        
        # Calculate reference hip and shoulder lines at address
        left_hip_addr = address_landmarks[self.keypoints['left_hip']][:2]
        right_hip_addr = address_landmarks[self.keypoints['right_hip']][:2]
        hip_ref_vector = right_hip_addr - left_hip_addr
        
        left_shoulder_addr = address_landmarks[self.keypoints['left_shoulder']][:2]
        right_shoulder_addr = address_landmarks[self.keypoints['right_shoulder']][:2]
        shoulder_ref_vector = right_shoulder_addr - left_shoulder_addr
        
        # Calculate rotations throughout swing
        start = key_positions.get('address', 0)
        end = key_positions.get('finish', len(landmarks_sequence) - 1)
        
        hip_rotations = []
        shoulder_rotations = []
        
        for i in range(start, min(end + 1, len(landmarks_sequence))):
            if landmarks_sequence[i] is None:
                hip_rotations.append(0)
                shoulder_rotations.append(0)
                continue
            
            lm = landmarks_sequence[i]
            
            # Hip rotation
            left_hip = lm[self.keypoints['left_hip']][:2]
            right_hip = lm[self.keypoints['right_hip']][:2]
            hip_vector = right_hip - left_hip
            
            hip_rotation = self._calculate_rotation_angle(hip_ref_vector, hip_vector)
            hip_rotations.append(hip_rotation)
            
            # Shoulder rotation
            left_shoulder = lm[self.keypoints['left_shoulder']][:2]
            right_shoulder = lm[self.keypoints['right_shoulder']][:2]
            shoulder_vector = right_shoulder - left_shoulder
            
            shoulder_rotation = self._calculate_rotation_angle(shoulder_ref_vector, shoulder_vector)
            shoulder_rotations.append(shoulder_rotation)
        
        if hip_rotations and shoulder_rotations:
            results['hip_rotation'] = hip_rotations
            results['shoulder_rotation'] = shoulder_rotations
            results['max_hip_rotation'] = max(np.abs(hip_rotations))
            results['max_shoulder_rotation'] = max(np.abs(shoulder_rotations))
            
            # Check rotation sequence (shoulders should rotate more than hips)
            if results['max_shoulder_rotation'] > results['max_hip_rotation']:
                ratio = results['max_shoulder_rotation'] / (results['max_hip_rotation'] + 1)
                # Ideal ratio is about 2:1
                results['rotation_sequence_score'] = max(0, 100 - abs(ratio - 2) * 30)
            else:
                results['rotation_sequence_score'] = 50  # Insufficient shoulder turn
        
        return results
    
    def _calculate_rotation_angle(self, ref_vector: np.ndarray, 
                                  current_vector: np.ndarray) -> float:
        """
        Calculate rotation angle between two vectors
        
        Args:
            ref_vector: Reference vector
            current_vector: Current vector
            
        Returns:
            Rotation angle in degrees (positive = clockwise)
        """
        # Normalize vectors
        ref_norm = ref_vector / (np.linalg.norm(ref_vector) + 1e-6)
        curr_norm = current_vector / (np.linalg.norm(current_vector) + 1e-6)
        
        # Calculate angle
        dot_product = np.clip(np.dot(ref_norm, curr_norm), -1.0, 1.0)
        angle = np.degrees(np.arccos(dot_product))
        
        # Determine sign using cross product
        cross = ref_norm[0] * curr_norm[1] - ref_norm[1] * curr_norm[0]
        if cross < 0:
            angle = -angle
        
        return angle
    
    def calculate_weight_transfer(self, landmarks_sequence: List[np.ndarray],
                                  key_positions: dict) -> dict:
        """
        Calculate weight transfer during swing
        
        Args:
            landmarks_sequence: Sequence of pose landmarks
            key_positions: Key swing positions
            
        Returns:
            Dictionary with weight transfer metrics
        """
        results = {
            'weight_distribution': [],
            'max_weight_shift': 0,
            'weight_transfer_score': 0
        }
        
        start = key_positions.get('address', 0)
        end = key_positions.get('finish', len(landmarks_sequence) - 1)
        
        weight_ratios = []
        
        for i in range(start, min(end + 1, len(landmarks_sequence))):
            if landmarks_sequence[i] is None:
                weight_ratios.append(0.5)
                continue
            
            lm = landmarks_sequence[i]
            
            # Use hip and ankle positions to estimate weight distribution
            left_hip = lm[self.keypoints['left_hip']]
            right_hip = lm[self.keypoints['right_hip']]
            left_ankle = lm[self.keypoints['left_ankle']]
            right_ankle = lm[self.keypoints['right_ankle']]
            
            # Calculate center of hips
            hip_center_x = (left_hip[0] + right_hip[0]) / 2
            
            # Calculate foot positions
            left_foot_x = left_ankle[0]
            right_foot_x = right_ankle[0]
            foot_width = abs(right_foot_x - left_foot_x)
            
            if foot_width < 0.01:
                weight_ratios.append(0.5)
                continue
            
            # Estimate weight distribution (0 = all left, 1 = all right)
            weight_ratio = (hip_center_x - left_foot_x) / foot_width
            weight_ratio = np.clip(weight_ratio, 0, 1)
            weight_ratios.append(weight_ratio)
        
        if weight_ratios:
            results['weight_distribution'] = weight_ratios
            results['max_weight_shift'] = max(weight_ratios) - min(weight_ratios)
            
            # Score based on adequate weight transfer
            if results['max_weight_shift'] >= BIOMECHANICS['weight_shift_threshold']:
                results['weight_transfer_score'] = min(100, 
                    (results['max_weight_shift'] / BIOMECHANICS['weight_shift_threshold']) * 100)
            else:
                results['weight_transfer_score'] = (results['max_weight_shift'] / 
                    BIOMECHANICS['weight_shift_threshold']) * 100
        
        return results
    
    def calculate_wrist_angles(self, landmarks_sequence: List[np.ndarray],
                              key_positions: dict) -> dict:
        """
        Calculate wrist hinge angles during swing
        
        Args:
            landmarks_sequence: Sequence of pose landmarks
            key_positions: Key swing positions
            
        Returns:
            Dictionary with wrist angle metrics
        """
        results = {
            'wrist_angles': [],
            'backswing_wrist_angle': 0,
            'impact_wrist_angle': 0,
            'wrist_hinge_score': 0
        }
        
        # Get key frames
        top_frame = key_positions.get('top', 0)
        impact_frame = key_positions.get('impact', len(landmarks_sequence) - 1)
        
        # Calculate wrist angle at top of backswing
        if (top_frame < len(landmarks_sequence) and 
            landmarks_sequence[top_frame] is not None):
            lm = landmarks_sequence[top_frame]
            # Right arm: shoulder-elbow-wrist
            wrist_angle = self._get_angle(
                lm[self.keypoints['right_shoulder']],
                lm[self.keypoints['right_elbow']],
                lm[self.keypoints['right_wrist']]
            )
            results['backswing_wrist_angle'] = wrist_angle
        
        # Calculate wrist angle at impact
        if (impact_frame < len(landmarks_sequence) and 
            landmarks_sequence[impact_frame] is not None):
            lm = landmarks_sequence[impact_frame]
            wrist_angle = self._get_angle(
                lm[self.keypoints['right_shoulder']],
                lm[self.keypoints['right_elbow']],
                lm[self.keypoints['right_wrist']]
            )
            results['impact_wrist_angle'] = wrist_angle
        
        # Score wrist hinge
        backswing_error = abs(results['backswing_wrist_angle'] - 
                             BIOMECHANICS['ideal_wrist_hinge_backswing'])
        impact_error = abs(results['impact_wrist_angle'] - 
                          BIOMECHANICS['ideal_wrist_hinge_impact'])
        
        backswing_score = max(0, 100 - (backswing_error / 
                              BIOMECHANICS['wrist_tolerance']) * 50)
        impact_score = max(0, 100 - (impact_error / 
                           BIOMECHANICS['wrist_tolerance']) * 50)
        
        results['wrist_hinge_score'] = (backswing_score + impact_score) / 2
        
        return results
    
    def _get_angle(self, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        """
        Calculate angle at p2 formed by three points
        
        Args:
            p1, p2, p3: 3D points
            
        Returns:
            Angle in degrees
        """
        v1 = p1[:2] - p2[:2]
        v2 = p3[:2] - p2[:2]
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
        
        return angle
    
    def detect_common_errors(self, landmarks_sequence: List[np.ndarray],
                            key_positions: dict,
                            rotation_metrics: dict,
                            weight_metrics: dict) -> List[str]:
        """
        Detect common swing errors
        
        Args:
            landmarks_sequence: Sequence of pose landmarks
            key_positions: Key swing positions
            rotation_metrics: Rotation analysis results
            weight_metrics: Weight transfer results
            
        Returns:
            List of detected error messages
        """
        errors = []
        
        # Early extension check
        if self._check_early_extension(landmarks_sequence, key_positions):
            errors.append('early_extension')
        
        # Over-the-top check
        if self._check_over_the_top(landmarks_sequence, key_positions):
            errors.append('over_the_top')
        
        # Reverse pivot check
        if weight_metrics.get('max_weight_shift', 0) < BIOMECHANICS['weight_shift_threshold'] / 2:
            errors.append('reverse_pivot')
        
        # Poor rotation sequence
        if rotation_metrics.get('rotation_sequence_score', 0) < 50:
            errors.append('flat_shoulder')
        
        # Insufficient weight transfer
        if weight_metrics.get('weight_transfer_score', 0) < 60:
            errors.append('sway')
        
        return errors
    
    def _check_early_extension(self, landmarks_sequence: List[np.ndarray],
                               key_positions: dict) -> bool:
        """
        Check for early extension (standing up during downswing)
        
        Args:
            landmarks_sequence: Sequence of pose landmarks
            key_positions: Key swing positions
            
        Returns:
            True if early extension detected
        """
        top_frame = key_positions.get('top', 0)
        impact_frame = key_positions.get('impact', len(landmarks_sequence) - 1)
        
        if (top_frame >= len(landmarks_sequence) or impact_frame >= len(landmarks_sequence)):
            return False
        
        if (landmarks_sequence[top_frame] is None or 
            landmarks_sequence[impact_frame] is None):
            return False
        
        # Compare hip height at top and impact
        top_hip = (landmarks_sequence[top_frame][self.keypoints['left_hip']][1] +
                   landmarks_sequence[top_frame][self.keypoints['right_hip']][1]) / 2
        impact_hip = (landmarks_sequence[impact_frame][self.keypoints['left_hip']][1] +
                      landmarks_sequence[impact_frame][self.keypoints['right_hip']][1]) / 2
        
        # If hips rise significantly (y decreases in image coords), early extension
        hip_rise = top_hip - impact_hip
        
        return hip_rise > 0.05  # 5% of image height threshold
    
    def _check_over_the_top(self, landmarks_sequence: List[np.ndarray],
                           key_positions: dict) -> bool:
        """
        Check for over-the-top downswing
        
        Args:
            landmarks_sequence: Sequence of pose landmarks
            key_positions: Key swing positions
            
        Returns:
            True if over-the-top detected
        """
        top_frame = key_positions.get('top', 0)
        impact_frame = key_positions.get('impact', len(landmarks_sequence) - 1)
        
        if (top_frame >= len(landmarks_sequence) or impact_frame >= len(landmarks_sequence)):
            return False
        
        # Check if downswing path is outside-in
        wrist_idx = self.keypoints['right_wrist']
        shoulder_idx = self.keypoints['right_shoulder']
        
        downswing_frames = range(top_frame, min(impact_frame + 1, len(landmarks_sequence)))
        
        wrist_path_x = []
        for i in downswing_frames:
            if landmarks_sequence[i] is not None and len(landmarks_sequence[i]) > wrist_idx:
                wrist_x = landmarks_sequence[i][wrist_idx][0]
                shoulder_x = landmarks_sequence[i][shoulder_idx][0]
                wrist_path_x.append(wrist_x - shoulder_x)
        
        if len(wrist_path_x) > 2:
            # Over-the-top shows wrist moving away from body early in downswing
            early_downswing_trend = np.mean(np.diff(wrist_path_x[:len(wrist_path_x)//2]))
            return early_downswing_trend > 0.01
        
        return False
