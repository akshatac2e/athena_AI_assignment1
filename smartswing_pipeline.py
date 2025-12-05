"""
SmartSwing Golf Analysis Pipeline
Main pipeline integrating all modules for complete swing analysis
"""

import os
import cv2
import numpy as np
from typing import Dict, Tuple, Optional
import time

from pose_estimator import PoseEstimator
from swing_detector import SwingDetector
from biomechanical_analyzer import BiomechanicalAnalyzer
from swing_scorer import SwingScorer
from visual_feedback import VisualFeedback
from progress_tracker import ProgressTracker
from config import VIDEO_CONFIG


class SmartSwingPipeline:
    """
    Complete pipeline for golf swing analysis
    """
    
    def __init__(self):
        """Initialize all pipeline components"""
        print("Initializing SmartSwing Pipeline...")
        
        self.pose_estimator = PoseEstimator()
        self.swing_detector = SwingDetector()
        self.bio_analyzer = BiomechanicalAnalyzer()
        self.scorer = SwingScorer()
        self.visual_feedback = VisualFeedback()
        self.progress_tracker = ProgressTracker()
        
        print("✓ Pipeline initialized successfully")
    
    def analyze_video(self, video_path: str, 
                     output_video_path: Optional[str] = None,
                     save_session: bool = True) -> Dict:
        """
        Complete analysis of golf swing video
        
        Args:
            video_path: Path to input video
            output_video_path: Path to save annotated video (optional)
            save_session: Whether to save session to history
            
        Returns:
            Dictionary with complete analysis results
        """
        print(f"\n{'='*60}")
        print(f"Analyzing video: {video_path}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Step 1: Extract pose landmarks
        print("Step 1: Extracting pose landmarks...")
        step_start = time.time()
        frames, landmarks_sequence, video_info = self.pose_estimator.process_video(video_path)
        print(f"✓ Extracted {len(frames)} frames in {time.time() - step_start:.2f}s")
        
        # Step 2: Detect swing segments
        print("\nStep 2: Detecting swing segments...")
        step_start = time.time()
        motion_energy = self.swing_detector.calculate_motion_energy(landmarks_sequence)
        swing_segments = self.swing_detector.detect_swing_phases(motion_energy)
        
        if not swing_segments:
            print("⚠ No valid swing detected in video")
            return {'error': 'No swing detected'}
        
        print(f"✓ Detected {len(swing_segments)} swing(s) in {time.time() - step_start:.2f}s")
        
        # Analyze first (primary) swing
        swing_start, swing_end, _ = swing_segments[0]
        print(f"  Primary swing: frames {swing_start} to {swing_end}")
        
        # Step 3: Identify key positions
        print("\nStep 3: Identifying key positions...")
        step_start = time.time()
        key_positions = self.swing_detector.identify_swing_positions(
            landmarks_sequence, (swing_start, swing_end)
        )
        print(f"✓ Key positions identified in {time.time() - step_start:.2f}s")
        for position, frame_idx in key_positions.items():
            print(f"  {position.capitalize()}: frame {frame_idx}")
        
        # Step 4: Biomechanical analysis
        print("\nStep 4: Performing biomechanical analysis...")
        step_start = time.time()
        
        # Swing plane analysis
        swing_plane = self.bio_analyzer.calculate_swing_plane(
            landmarks_sequence, key_positions
        )
        print(f"  Swing plane angle: {swing_plane.get('swing_plane_angle', 0):.1f}°")
        print(f"  Plane consistency: {swing_plane.get('plane_consistency', 0):.1f}/100")
        
        # Rotation analysis
        rotation = self.bio_analyzer.calculate_rotation_metrics(
            landmarks_sequence, key_positions
        )
        print(f"  Max shoulder rotation: {rotation.get('max_shoulder_rotation', 0):.1f}°")
        print(f"  Max hip rotation: {rotation.get('max_hip_rotation', 0):.1f}°")
        
        # Weight transfer analysis
        weight_transfer = self.bio_analyzer.calculate_weight_transfer(
            landmarks_sequence, key_positions
        )
        print(f"  Weight shift: {weight_transfer.get('max_weight_shift', 0):.2%}")
        
        # Wrist analysis
        wrist = self.bio_analyzer.calculate_wrist_angles(
            landmarks_sequence, key_positions
        )
        print(f"  Backswing wrist angle: {wrist.get('backswing_wrist_angle', 0):.1f}°")
        
        # Tempo analysis
        tempo = self.swing_detector.analyze_tempo(
            landmarks_sequence, (swing_start, swing_end), key_positions
        )
        print(f"  Tempo ratio: {tempo.get('tempo_ratio', 0):.2f}:1")
        
        # Error detection
        errors = self.bio_analyzer.detect_common_errors(
            landmarks_sequence, key_positions, rotation, weight_transfer
        )
        if errors:
            print(f"  Detected errors: {', '.join(errors)}")
        
        print(f"✓ Biomechanical analysis completed in {time.time() - step_start:.2f}s")
        
        # Step 5: Calculate scores
        print("\nStep 5: Calculating swing scores...")
        step_start = time.time()
        score_results = self.scorer.calculate_swing_score(
            swing_plane, rotation, weight_transfer, wrist, tempo
        )
        print(f"✓ Overall Score: {score_results['overall_score']:.1f}/100 "
              f"(Grade: {score_results['grade']})")
        print(f"  Calculation time: {time.time() - step_start:.2f}s")
        
        # Compile results
        analysis_results = {
            'video_info': video_info,
            'swing_segment': (swing_start, swing_end),
            'key_positions': key_positions,
            'swing_plane': swing_plane,
            'rotation': rotation,
            'weight_transfer': weight_transfer,
            'wrist': wrist,
            'tempo': tempo,
            'errors': errors,
            'motion_energy': motion_energy.tolist()
        }
        
        # Step 6: Generate visual feedback
        if output_video_path:
            print("\nStep 6: Generating annotated video...")
            step_start = time.time()
            
            # Extract swing frames
            swing_frames = frames[swing_start:swing_end+1]
            swing_landmarks = landmarks_sequence[swing_start:swing_end+1]
            
            self.visual_feedback.create_annotated_video(
                swing_frames,
                swing_landmarks,
                analysis_results,
                score_results,
                output_video_path,
                video_info['fps']
            )
            print(f"✓ Annotated video saved to: {output_video_path}")
            print(f"  Generation time: {time.time() - step_start:.2f}s")
        
        # Step 7: Save session
        if save_session:
            print("\nStep 7: Saving session to history...")
            session_id = self.progress_tracker.add_session(
                video_path, analysis_results, score_results
            )
            print(f"✓ Session saved with ID: {session_id}")
        
        # Generate detailed report
        report = self.scorer.generate_detailed_report(
            analysis_results, score_results
        )
        
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"Analysis completed in {total_time:.2f}s")
        print(f"{'='*60}\n")
        
        print(report)
        
        return {
            'analysis': analysis_results,
            'scores': score_results,
            'report': report,
            'processing_time': total_time
        }
    
    def analyze_multiple_videos(self, video_paths: list, 
                               output_dir: str = './results') -> list:
        """
        Analyze multiple videos
        
        Args:
            video_paths: List of video paths
            output_dir: Directory to save results
            
        Returns:
            List of analysis results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for i, video_path in enumerate(video_paths, 1):
            print(f"\n{'#'*60}")
            print(f"Processing video {i}/{len(video_paths)}")
            print(f"{'#'*60}")
            
            # Generate output path
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_video = os.path.join(output_dir, f"{video_name}_analyzed.mp4")
            
            # Analyze
            result = self.analyze_video(video_path, output_video)
            results.append(result)
            
            # Save report
            if 'report' in result:
                report_path = os.path.join(output_dir, f"{video_name}_report.txt")
                with open(report_path, 'w') as f:
                    f.write(result['report'])
                print(f"Report saved to: {report_path}")
        
        return results
    
    def generate_progress_report(self, output_path: str = None):
        """
        Generate progress report and visualizations
        
        Args:
            output_path: Path to save visualization
        """
        print("\nGenerating progress report...")
        
        # Text report
        report = self.progress_tracker.generate_progress_report()
        print(report)
        
        # Visualizations
        if output_path is None:
            output_path = './metrics/progress_report.png'
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.progress_tracker.visualize_progress(output_path)
        
        # Export CSV
        csv_path = output_path.replace('.png', '.csv')
        self.progress_tracker.export_to_csv(csv_path)
    
    def compare_sessions(self, session_id1: str, session_id2: str) -> str:
        """
        Compare two sessions
        
        Args:
            session_id1: First session ID
            session_id2: Second session ID
            
        Returns:
            Comparison report
        """
        session1 = self.progress_tracker.get_session(session_id1)
        session2 = self.progress_tracker.get_session(session_id2)
        
        if not session1 or not session2:
            return "One or both sessions not found"
        
        report = []
        report.append("=" * 60)
        report.append("SESSION COMPARISON")
        report.append("=" * 60)
        report.append("")
        
        report.append(f"Session 1: {session1['session_id']}")
        report.append(f"Session 2: {session2['session_id']}")
        report.append("")
        
        # Compare overall scores
        score_diff = session2['overall_score'] - session1['overall_score']
        report.append(f"Overall Score Change: {score_diff:+.1f}")
        report.append(f"  Session 1: {session1['overall_score']:.1f}")
        report.append(f"  Session 2: {session2['overall_score']:.1f}")
        report.append("")
        
        # Compare components
        report.append("Component Changes:")
        report.append("-" * 40)
        for component in session1['component_scores'].keys():
            if component in session2['component_scores']:
                diff = (session2['component_scores'][component] - 
                       session1['component_scores'][component])
                component_name = component.replace('_', ' ').title()
                report.append(f"  {component_name}: {diff:+.1f}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def create_sample_video_info():
    """
    Print information about how to obtain sample golf swing videos
    """
    info = """
    ╔════════════════════════════════════════════════════════════╗
    ║          Sample Golf Swing Video Sources                  ║
    ╚════════════════════════════════════════════════════════════╝
    
    To test this pipeline, you can use golf swing videos from:
    
    1. Open Source Datasets:
       - YouTube (search for "golf swing slow motion")
       - Kaggle golf swing datasets
       - Sports analysis datasets
    
    2. Record Your Own:
       - Use smartphone camera
       - Film from side angle (down-the-line view)
       - Ensure full body is visible
       - Use tripod for stable footage
    
    3. Sample Video Requirements:
       - Format: MP4, AVI, MOV
       - Duration: 5-15 seconds
       - Resolution: 480p or higher
       - Frame rate: 30 fps or higher
       - Clear view of golfer's body
    
    Place videos in: ./data/videos/
    """
    print(info)


if __name__ == "__main__":
    # Display sample video information
    create_sample_video_info()
    
    # Example usage
    print("\nSmartSwing Pipeline Ready!")
    print("To analyze a video:")
    print("  pipeline = SmartSwingPipeline()")
    print("  results = pipeline.analyze_video('path/to/video.mp4')")
