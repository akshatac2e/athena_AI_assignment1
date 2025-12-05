"""
Visual Feedback Module
Creates annotated videos with swing analysis overlays
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from config import COLORS, KEYPOINTS, FEEDBACK_MESSAGES


class VisualFeedback:
    """
    Generates visual feedback overlays on swing videos
    """
    
    def __init__(self):
        """Initialize visual feedback generator"""
        self.colors = COLORS
        self.keypoints = KEYPOINTS
        
    def create_annotated_video(self,
                               frames: List[np.ndarray],
                               landmarks_sequence: List[np.ndarray],
                               analysis_results: dict,
                               score_results: dict,
                               output_path: str,
                               fps: int = 30) -> None:
        """
        Create video with analysis overlays
        
        Args:
            frames: List of video frames
            landmarks_sequence: List of pose landmarks
            analysis_results: Complete analysis results
            score_results: Scoring results
            output_path: Path to save output video
            fps: Frames per second
        """
        if not frames:
            return
        
        height, width = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        key_positions = analysis_results.get('key_positions', {})
        errors = analysis_results.get('errors', [])
        
        for i, frame in enumerate(frames):
            annotated = frame.copy()
            
            # Draw pose skeleton
            if i < len(landmarks_sequence) and landmarks_sequence[i] is not None:
                annotated = self.draw_skeleton(annotated, landmarks_sequence[i])
            
            # Draw swing plane
            if 'swing_plane' in analysis_results and i < len(landmarks_sequence):
                annotated = self.draw_swing_plane(
                    annotated, 
                    landmarks_sequence[i],
                    analysis_results['swing_plane']
                )
            
            # Highlight key positions
            annotated = self.highlight_key_positions(annotated, i, key_positions)
            
            # Draw info panel
            annotated = self.draw_info_panel(
                annotated,
                score_results,
                i,
                len(frames),
                key_positions
            )
            
            # Draw error messages
            if errors:
                annotated = self.draw_error_messages(annotated, errors)
            
            out.write(annotated)
        
        out.release()
    
    def draw_skeleton(self, frame: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
        """
        Draw pose skeleton on frame
        
        Args:
            frame: Input frame
            landmarks: Pose landmarks
            
        Returns:
            Frame with skeleton drawn
        """
        if landmarks is None:
            return frame
        
        h, w = frame.shape[:2]
        annotated = frame.copy()
        
        # Define connections
        connections = [
            # Torso
            (11, 12), (11, 23), (12, 24), (23, 24),
            # Left arm
            (11, 13), (13, 15),
            # Right arm
            (12, 14), (14, 16),
            # Left leg
            (23, 25), (25, 27),
            # Right leg
            (24, 26), (26, 28)
        ]
        
        # Draw connections
        for connection in connections:
            start_idx, end_idx = connection
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start = landmarks[start_idx]
                end = landmarks[end_idx]
                
                start_point = (int(start[0] * w), int(start[1] * h))
                end_point = (int(end[0] * w), int(end[1] * h))
                
                cv2.line(annotated, start_point, end_point, 
                        self.colors['skeleton'], 2)
        
        # Draw keypoints
        for landmark in landmarks:
            x, y = int(landmark[0] * w), int(landmark[1] * h)
            cv2.circle(annotated, (x, y), 4, self.colors['good'], -1)
            cv2.circle(annotated, (x, y), 5, self.colors['neutral'], 1)
        
        return annotated
    
    def draw_swing_plane(self, 
                        frame: np.ndarray,
                        landmarks: Optional[np.ndarray],
                        swing_plane_metrics: dict) -> np.ndarray:
        """
        Draw swing plane visualization
        
        Args:
            frame: Input frame
            landmarks: Current frame landmarks
            swing_plane_metrics: Swing plane analysis results
            
        Returns:
            Frame with swing plane drawn
        """
        if landmarks is None:
            return frame
        
        h, w = frame.shape[:2]
        annotated = frame.copy()
        
        # Draw plane angle indicator
        angle = swing_plane_metrics.get('swing_plane_angle', 0)
        consistency = swing_plane_metrics.get('plane_consistency', 0)
        
        # Get shoulder center
        if len(landmarks) > max(self.keypoints['left_shoulder'], 
                                self.keypoints['right_shoulder']):
            left_shoulder = landmarks[self.keypoints['left_shoulder']]
            right_shoulder = landmarks[self.keypoints['right_shoulder']]
            shoulder_center = (left_shoulder + right_shoulder) / 2
            
            center_x = int(shoulder_center[0] * w)
            center_y = int(shoulder_center[1] * h)
            
            # Draw plane line
            length = 150
            angle_rad = np.radians(angle)
            end_x = int(center_x + length * np.cos(angle_rad))
            end_y = int(center_y - length * np.sin(angle_rad))
            
            # Color based on consistency
            if consistency >= 80:
                color = self.colors['good']
            elif consistency >= 60:
                color = self.colors['warning']
            else:
                color = self.colors['error']
            
            cv2.line(annotated, (center_x, center_y), (end_x, end_y), color, 3)
            
            # Draw angle text
            cv2.putText(annotated, f"Plane: {angle:.1f}°", 
                       (center_x + 10, center_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated
    
    def highlight_key_positions(self,
                               frame: np.ndarray,
                               current_frame: int,
                               key_positions: dict) -> np.ndarray:
        """
        Highlight key swing positions
        
        Args:
            frame: Input frame
            current_frame: Current frame index
            key_positions: Dictionary of key position frames
            
        Returns:
            Frame with highlights
        """
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Define position labels
        position_labels = {
            'address': 'ADDRESS',
            'top': 'TOP',
            'impact': 'IMPACT',
            'finish': 'FINISH'
        }
        
        # Check if current frame is a key position
        for position, frame_idx in key_positions.items():
            if current_frame == frame_idx:
                label = position_labels.get(position, position.upper())
                
                # Draw banner
                cv2.rectangle(annotated, (0, 0), (w, 50), 
                            self.colors['good'], -1)
                cv2.putText(annotated, label, (w // 2 - 80, 35),
                           cv2.FONT_HERSHEY_BOLD, 1.2, 
                           self.colors['neutral'], 3)
                break
        
        return annotated
    
    def draw_info_panel(self,
                       frame: np.ndarray,
                       score_results: dict,
                       current_frame: int,
                       total_frames: int,
                       key_positions: dict) -> np.ndarray:
        """
        Draw information panel with scores and metrics
        
        Args:
            frame: Input frame
            score_results: Scoring results
            current_frame: Current frame index
            total_frames: Total frames
            key_positions: Key positions
            
        Returns:
            Frame with info panel
        """
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Create semi-transparent panel
        panel_height = 180
        panel = np.zeros((panel_height, w, 3), dtype=np.uint8)
        
        # Draw overall score
        overall_score = score_results.get('overall_score', 0)
        grade = score_results.get('grade', 'N/A')
        
        cv2.putText(panel, f"Swing Score: {overall_score:.1f}/100", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 
                   self.colors['neutral'], 2)
        cv2.putText(panel, f"Grade: {grade}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 
                   self.colors['neutral'], 2)
        
        # Draw component scores (top 3)
        component_scores = score_results.get('component_scores', {})
        sorted_components = sorted(component_scores.items(), 
                                  key=lambda x: x[1], reverse=True)[:3]
        
        y_offset = 90
        for component, score in sorted_components:
            component_name = component.replace('_', ' ').title()
            if len(component_name) > 20:
                component_name = component_name[:17] + "..."
            
            # Color based on score
            if score >= 80:
                color = self.colors['good']
            elif score >= 60:
                color = self.colors['warning']
            else:
                color = self.colors['error']
            
            cv2.putText(panel, f"{component_name}: {score:.0f}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                       color, 1)
            y_offset += 25
        
        # Draw progress bar
        progress = current_frame / max(total_frames, 1)
        bar_width = w - 40
        bar_height = 10
        bar_x = 20
        bar_y = panel_height - 20
        
        cv2.rectangle(panel, (bar_x, bar_y), 
                     (bar_x + bar_width, bar_y + bar_height),
                     self.colors['neutral'], 1)
        cv2.rectangle(panel, (bar_x, bar_y), 
                     (bar_x + int(bar_width * progress), bar_y + bar_height),
                     self.colors['good'], -1)
        
        # Mark key positions on progress bar
        for position, frame_idx in key_positions.items():
            if frame_idx < total_frames:
                pos_x = bar_x + int(bar_width * (frame_idx / total_frames))
                cv2.circle(panel, (pos_x, bar_y + bar_height // 2), 5,
                          self.colors['warning'], -1)
        
        # Blend panel with frame
        alpha = 0.7
        annotated[h - panel_height:h, :] = cv2.addWeighted(
            annotated[h - panel_height:h, :], 1 - alpha,
            panel, alpha, 0
        )
        
        return annotated
    
    def draw_error_messages(self,
                           frame: np.ndarray,
                           errors: List[str]) -> np.ndarray:
        """
        Draw error messages and corrections
        
        Args:
            frame: Input frame
            errors: List of error codes
            
        Returns:
            Frame with error messages
        """
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Draw error banner
        if errors:
            banner_height = 30 + (len(errors) * 25)
            cv2.rectangle(annotated, (w - 450, 10), 
                         (w - 10, 10 + banner_height),
                         (0, 0, 0), -1)
            cv2.rectangle(annotated, (w - 450, 10), 
                         (w - 10, 10 + banner_height),
                         self.colors['error'], 2)
            
            cv2.putText(annotated, "Detected Issues:", 
                       (w - 440, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, self.colors['error'], 2)
            
            y_offset = 55
            for error in errors[:5]:  # Limit to 5 errors
                message = FEEDBACK_MESSAGES.get(error, error)
                # Wrap text if too long
                if len(message) > 50:
                    message = message[:47] + "..."
                
                cv2.putText(annotated, f"• {message}", 
                           (w - 435, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.4, self.colors['warning'], 1)
                y_offset += 25
        
        return annotated
    
    def create_comparison_frame(self,
                               frame1: np.ndarray,
                               frame2: np.ndarray,
                               label1: str = "Current",
                               label2: str = "Previous") -> np.ndarray:
        """
        Create side-by-side comparison frame
        
        Args:
            frame1: First frame
            frame2: Second frame
            label1: Label for first frame
            label2: Label for second frame
            
        Returns:
            Combined comparison frame
        """
        h1, w1 = frame1.shape[:2]
        h2, w2 = frame2.shape[:2]
        
        # Resize frames to same height
        target_height = min(h1, h2)
        frame1_resized = cv2.resize(frame1, (int(w1 * target_height / h1), target_height))
        frame2_resized = cv2.resize(frame2, (int(w2 * target_height / h2), target_height))
        
        # Create combined frame
        combined = np.hstack([frame1_resized, frame2_resized])
        
        # Add labels
        cv2.putText(combined, label1, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, self.colors['good'], 2)
        cv2.putText(combined, label2, (frame1_resized.shape[1] + 10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, self.colors['good'], 2)
        
        return combined
