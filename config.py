"""
Configuration file for SmartSwing Golf Analysis System
"""

# Video Processing Parameters
VIDEO_CONFIG = {
    'fps': 30,
    'frame_skip': 1,  # Process every frame
    'resize_width': 640,
    'resize_height': 480
}

# Pose Estimation Parameters
POSE_CONFIG = {
    'min_detection_confidence': 0.5,
    'min_tracking_confidence': 0.5,
    'model_complexity': 2  # 0, 1, or 2 (higher = more accurate but slower)
}

# Swing Detection Parameters
SWING_DETECTION = {
    'motion_threshold': 5.0,  # Minimum motion to consider swing started
    'stillness_frames': 15,  # Frames of stillness to end swing
    'min_swing_duration': 30,  # Minimum frames for valid swing
    'max_swing_duration': 120,  # Maximum frames for valid swing
    'velocity_smoothing_window': 5
}

# Biomechanical Analysis Parameters
BIOMECHANICS = {
    # Ideal swing plane angle (degrees from horizontal)
    'ideal_swing_plane_angle': 45.0,
    'swing_plane_tolerance': 15.0,
    
    # Hip and shoulder rotation
    'ideal_hip_rotation': 45.0,
    'ideal_shoulder_rotation': 90.0,
    'rotation_tolerance': 10.0,
    
    # Wrist angles
    'ideal_wrist_hinge_backswing': 90.0,
    'ideal_wrist_hinge_impact': 45.0,
    'wrist_tolerance': 15.0,
    
    # Weight transfer
    'weight_shift_threshold': 0.15,  # 15% weight shift expected
    
    # Club path
    'ideal_club_path_deviation': 5.0,  # degrees from target line
}

# Scoring Weights
SCORING_WEIGHTS = {
    'swing_plane_consistency': 0.25,
    'rotation_quality': 0.20,
    'downswing_alignment': 0.20,
    'wrist_hinge': 0.15,
    'weight_transfer': 0.10,
    'tempo': 0.10
}

# Visual Feedback Colors (BGR format for OpenCV)
COLORS = {
    'good': (0, 255, 0),      # Green
    'warning': (0, 165, 255),  # Orange
    'error': (0, 0, 255),      # Red
    'neutral': (255, 255, 255), # White
    'skeleton': (255, 0, 255),  # Magenta
    'swing_plane': (255, 255, 0) # Cyan
}

# Body Keypoints (MediaPipe Pose Landmarks)
KEYPOINTS = {
    'nose': 0,
    'left_eye_inner': 1,
    'left_eye': 2,
    'left_eye_outer': 3,
    'right_eye_inner': 4,
    'right_eye': 5,
    'right_eye_outer': 6,
    'left_ear': 7,
    'right_ear': 8,
    'mouth_left': 9,
    'mouth_right': 10,
    'left_shoulder': 11,
    'right_shoulder': 12,
    'left_elbow': 13,
    'right_elbow': 14,
    'left_wrist': 15,
    'right_wrist': 16,
    'left_pinky': 17,
    'right_pinky': 18,
    'left_index': 19,
    'right_index': 20,
    'left_thumb': 21,
    'right_thumb': 22,
    'left_hip': 23,
    'right_hip': 24,
    'left_knee': 25,
    'right_knee': 26,
    'left_ankle': 27,
    'right_ankle': 28,
    'left_heel': 29,
    'right_heel': 30,
    'left_foot_index': 31,
    'right_foot_index': 32
}

# Storage Configuration
STORAGE = {
    'data_dir': './data',
    'results_dir': './results',
    'sessions_file': 'sessions.json',
    'metrics_dir': './metrics'
}

# Error Messages and Feedback
FEEDBACK_MESSAGES = {
    'early_extension': "Early extension detected - maintain spine angle through impact",
    'over_the_top': "Over-the-top downswing - swing more from inside",
    'reverse_pivot': "Reverse pivot detected - shift weight to back foot in backswing",
    'poor_wrist_hinge': "Insufficient wrist hinge - cock wrists earlier in backswing",
    'flat_shoulder': "Flat shoulder turn - rotate shoulders more vertically",
    'sway': "Lateral sway detected - rotate around spine, don't slide",
    'casting': "Casting detected - maintain wrist angle longer in downswing"
}
