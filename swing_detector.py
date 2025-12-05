"""
Swing Detection Module
Automatically detects the start and end of golf swing from video
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional
from scipy.signal import savgol_filter
from config import SWING_DETECTION


class SwingDetector:
    """
    Detects golf swing segments in video using motion analysis
    """
    
    def __init__(self, motion_threshold: float = SWING_DETECTION['motion_threshold'],
                 stillness_frames: int = SWING_DETECTION['stillness_frames'],
                 min_swing_duration: int = SWING_DETECTION['min_swing_duration'],
                 max_swing_duration: int = SWING_DETECTION['max_swing_duration']):
        """
        Initialize swing detector
        
        Args:
            motion_threshold: Minimum motion magnitude to detect swing
            stillness_frames: Number of still frames to mark swing end
            min_swing_duration: Minimum frames for valid swing
            max_swing_duration: Maximum frames for valid swing
        """
        self.motion_threshold = motion_threshold
        self.stillness_frames = stillness_frames
        self.min_swing_duration = min_swing_duration
        self.max_swing_duration = max_swing_duration
        
    def calculate_motion_energy(self, landmarks_sequence: List[np.ndarray]) -> np.ndarray:
        """
        Calculate motion energy from pose landmarks over time
        
        Args:
            landmarks_sequence: List of landmark arrays (frames x landmarks x 3)
            
        Returns:
            Array of motion energy values per frame
        """
        if len(landmarks_sequence) < 2:
            return np.zeros(len(landmarks_sequence))
        
        motion_energy = np.zeros(len(landmarks_sequence))
        
        for i in range(1, len(landmarks_sequence)):
            if landmarks_sequence[i] is not None and landmarks_sequence[i-1] is not None:
                # Calculate displacement of key joints
                displacement = np.linalg.norm(
                    landmarks_sequence[i] - landmarks_sequence[i-1], 
                    axis=1
                )
                # Focus on upper body and arms (shoulders, elbows, wrists, hips)
                key_joints = [11, 12, 13, 14, 15, 16, 23, 24]
                motion_energy[i] = np.mean(displacement[key_joints]) * 100
                
        # Smooth motion energy
        if len(motion_energy) > SWING_DETECTION['velocity_smoothing_window']:
            motion_energy = savgol_filter(
                motion_energy, 
                SWING_DETECTION['velocity_smoothing_window'], 
                2
            )
            
        return motion_energy
    
    def detect_swing_phases(self, motion_energy: np.ndarray) -> List[Tuple[int, int, str]]:
        """
        Detect swing start and end points based on motion energy
        
        Args:
            motion_energy: Array of motion energy values
            
        Returns:
            List of tuples (start_frame, end_frame, phase_label)
        """
        swings = []
        in_swing = False
        swing_start = 0
        stillness_counter = 0
        
        for i, energy in enumerate(motion_energy):
            if not in_swing:
                # Detect swing start
                if energy > self.motion_threshold:
                    in_swing = True
                    swing_start = i
                    stillness_counter = 0
            else:
                # Detect swing end
                if energy < self.motion_threshold:
                    stillness_counter += 1
                    if stillness_counter >= self.stillness_frames:
                        swing_end = i - self.stillness_frames
                        swing_duration = swing_end - swing_start
                        
                        # Validate swing duration
                        if (self.min_swing_duration <= swing_duration <= 
                            self.max_swing_duration):
                            swings.append((swing_start, swing_end, 'full_swing'))
                        
                        in_swing = False
                        stillness_counter = 0
                else:
                    stillness_counter = 0
        
        return swings
    
    def identify_swing_positions(self, landmarks_sequence: List[np.ndarray], 
                                 swing_range: Tuple[int, int]) -> dict:
        """
        Identify key positions in swing: address, top, impact, finish
        
        Args:
            landmarks_sequence: Sequence of pose landmarks
            swing_range: (start_frame, end_frame) tuple
            
        Returns:
            Dictionary with frame indices for key positions
        """
        start, end = swing_range
        swing_landmarks = landmarks_sequence[start:end+1]
        
        if len(swing_landmarks) == 0:
            return {}
        
        # Calculate right wrist height (assuming right-handed golfer)
        wrist_heights = []
        for lm in swing_landmarks:
            if lm is not None and len(lm) > 16:
                wrist_heights.append(lm[16, 1])  # y-coordinate (inverted in image)
            else:
                wrist_heights.append(0)
        
        wrist_heights = np.array(wrist_heights)
        
        # Address: first frame
        address_idx = 0
        
        # Top of backswing: maximum wrist height in first half
        backswing_end = len(wrist_heights) // 2
        top_idx = np.argmin(wrist_heights[:backswing_end]) if backswing_end > 0 else 0
        
        # Impact: approximate as 80% through swing
        impact_idx = int(len(wrist_heights) * 0.8)
        
        # Finish: last frame
        finish_idx = len(wrist_heights) - 1
        
        return {
            'address': start + address_idx,
            'top': start + top_idx,
            'impact': start + impact_idx,
            'finish': start + finish_idx
        }
    
    def analyze_tempo(self, landmarks_sequence: List[np.ndarray],
                     swing_range: Tuple[int, int],
                     key_positions: dict) -> dict:
        """
        Analyze swing tempo and timing
        
        Args:
            landmarks_sequence: Sequence of pose landmarks
            swing_range: (start_frame, end_frame) tuple
            key_positions: Dictionary of key position frame indices
            
        Returns:
            Dictionary with tempo metrics
        """
        start, end = swing_range
        total_frames = end - start
        
        backswing_frames = key_positions.get('top', start) - key_positions.get('address', start)
        downswing_frames = key_positions.get('impact', end) - key_positions.get('top', start)
        
        # Ideal ratio is about 3:1 (backswing:downswing)
        tempo_ratio = backswing_frames / max(downswing_frames, 1)
        
        return {
            'total_frames': total_frames,
            'backswing_frames': backswing_frames,
            'downswing_frames': downswing_frames,
            'tempo_ratio': tempo_ratio,
            'tempo_score': self._score_tempo(tempo_ratio)
        }
    
    def _score_tempo(self, ratio: float) -> float:
        """
        Score tempo based on ratio (ideal is 3:1)
        
        Args:
            ratio: Backswing to downswing ratio
            
        Returns:
            Score from 0-100
        """
        ideal_ratio = 3.0
        deviation = abs(ratio - ideal_ratio)
        
        # Perfect score at ideal, decrease with deviation
        score = max(0, 100 - (deviation * 20))
        return score
