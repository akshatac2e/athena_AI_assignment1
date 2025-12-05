"""
Demo Script for SmartSwing Golf Analysis System
Demonstrates all functionalities with sample videos
"""

import os
import sys
import time
import cv2
import numpy as np
from smartswing_pipeline import SmartSwingPipeline


def create_synthetic_golf_swing_video(output_path: str, duration: int = 5, fps: int = 30):
    """
    Create a synthetic golf swing video for testing purposes
    
    Args:
        output_path: Path to save video
        duration: Duration in seconds
        fps: Frames per second
    """
    print(f"Creating synthetic golf swing video: {output_path}")
    
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    # Simulate a golfer figure (stick figure)
    for frame_idx in range(total_frames):
        # Create blank frame
        frame = np.ones((height, width, 3), dtype=np.uint8) * 200
        
        # Add grid
        for i in range(0, width, 50):
            cv2.line(frame, (i, 0), (i, height), (220, 220, 220), 1)
        for i in range(0, height, 50):
            cv2.line(frame, (0, i), (width, i), (220, 220, 220), 1)
        
        # Animate swing
        t = frame_idx / total_frames
        
        # Address position (0-20%)
        if t < 0.2:
            body_x = width // 2
            body_y = height // 2
            club_angle = 70
            hip_rotation = 0
            shoulder_rotation = 0
        # Backswing (20-50%)
        elif t < 0.5:
            progress = (t - 0.2) / 0.3
            body_x = width // 2 - int(5 * progress)
            body_y = height // 2
            club_angle = 70 + 110 * progress
            hip_rotation = 45 * progress
            shoulder_rotation = 90 * progress
        # Downswing (50-80%)
        elif t < 0.8:
            progress = (t - 0.5) / 0.3
            body_x = width // 2 + int(10 * progress)
            body_y = height // 2
            club_angle = 180 - 180 * progress
            hip_rotation = 45 - 20 * progress
            shoulder_rotation = 90 - 45 * progress
        # Follow-through (80-100%)
        else:
            progress = (t - 0.8) / 0.2
            body_x = width // 2 + 10
            body_y = height // 2
            club_angle = 0 - 60 * progress
            hip_rotation = 25 + 65 * progress
            shoulder_rotation = 45 + 55 * progress
        
        # Draw stick figure golfer
        # Head
        cv2.circle(frame, (body_x, body_y - 60), 15, (100, 100, 100), -1)
        
        # Body (spine)
        spine_angle = 10 + shoulder_rotation * 0.2
        spine_end_x = int(body_x + 40 * np.sin(np.radians(spine_angle)))
        spine_end_y = int(body_y + 40 * np.cos(np.radians(spine_angle)))
        cv2.line(frame, (body_x, body_y - 45), (spine_end_x, spine_end_y), 
                (50, 50, 150), 4)
        
        # Shoulders
        shoulder_left_x = int(body_x - 30 * np.cos(np.radians(shoulder_rotation)))
        shoulder_left_y = int(body_y - 40 + 10 * np.sin(np.radians(shoulder_rotation)))
        shoulder_right_x = int(body_x + 30 * np.cos(np.radians(shoulder_rotation)))
        shoulder_right_y = int(body_y - 40 - 10 * np.sin(np.radians(shoulder_rotation)))
        
        cv2.line(frame, (shoulder_left_x, shoulder_left_y), 
                (shoulder_right_x, shoulder_right_y), (0, 100, 200), 4)
        
        # Arms (simplified - one line for club path)
        club_length = 80
        club_end_x = int(shoulder_right_x + club_length * np.cos(np.radians(club_angle)))
        club_end_y = int(shoulder_right_y + club_length * np.sin(np.radians(club_angle)))
        
        cv2.line(frame, (shoulder_right_x, shoulder_right_y), 
                (club_end_x, club_end_y), (0, 0, 200), 3)
        
        # Club head
        cv2.circle(frame, (club_end_x, club_end_y), 8, (0, 0, 255), -1)
        
        # Hips
        hip_left_x = int(body_x - 25 * np.cos(np.radians(hip_rotation)))
        hip_left_y = int(body_y + 10 * np.sin(np.radians(hip_rotation)))
        hip_right_x = int(body_x + 25 * np.cos(np.radians(hip_rotation)))
        hip_right_y = int(body_y - 10 * np.sin(np.radians(hip_rotation)))
        
        cv2.line(frame, (hip_left_x, hip_left_y), 
                (hip_right_x, hip_right_y), (100, 150, 0), 4)
        
        # Legs (simplified)
        cv2.line(frame, (hip_left_x, hip_left_y), 
                (body_x - 20, body_y + 80), (50, 50, 150), 4)
        cv2.line(frame, (hip_right_x, hip_right_y), 
                (body_x + 20, body_y + 80), (50, 50, 150), 4)
        
        # Add phase label
        if t < 0.2:
            phase = "ADDRESS"
            color = (0, 255, 0)
        elif t < 0.5:
            phase = "BACKSWING"
            color = (0, 165, 255)
        elif t < 0.8:
            phase = "DOWNSWING"
            color = (0, 0, 255)
        else:
            phase = "FOLLOW-THROUGH"
            color = (255, 0, 255)
        
        cv2.putText(frame, phase, (20, 40), cv2.FONT_HERSHEY_BOLD, 
                   1, color, 2)
        cv2.putText(frame, f"Frame: {frame_idx+1}/{total_frames}", 
                   (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.5, (0, 0, 0), 1)
        
        out.write(frame)
    
    out.release()
    print(f"✓ Synthetic video created: {output_path}")


def demo_single_video_analysis():
    """Demonstrate single video analysis"""
    print("\n" + "="*60)
    print("DEMO 1: Single Video Analysis")
    print("="*60)
    
    # Create sample video
    os.makedirs('./data/videos', exist_ok=True)
    video_path = './data/videos/output_fastest.mp4'
    
    # if not os.path.exists(video_path):
    #     create_synthetic_golf_swing_video(video_path, duration=4, fps=30)
    
    # Initialize pipeline
    pipeline = SmartSwingPipeline()
    
    # Analyze video
    output_path = './results/sample_swing_analyzed.mp4'
    results = pipeline.analyze_video(video_path, output_path)
    
    # Save detailed report
    if 'report' in results:
        report_path = './results/sample_swing_report.txt'
        with open(report_path, 'w') as f:
            f.write(results['report'])
        print(f"\nDetailed report saved to: {report_path}")
    
    return results


def demo_multiple_video_analysis():
    """Demonstrate batch processing of multiple videos"""
    print("\n" + "="*60)
    print("DEMO 2: Multiple Video Analysis")
    print("="*60)

    folder_path = "./data/videos"
    
    # Create multiple sample videos with variations
    video_paths = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]
    
    # for i in range(1, 4):
    #     video_path = f'./data/videos/swing_session_{i}.mp4'
    #     if not os.path.exists(video_path):
    #         # Vary duration slightly for different swings
    #         create_synthetic_golf_swing_video(video_path, duration=3+i, fps=30)
    #     video_paths.append(video_path)
    
    # Initialize pipeline
    pipeline = SmartSwingPipeline()
    
    # Analyze all videos
    results = pipeline.analyze_multiple_videos(video_paths, output_dir='./results')
    
    print(f"\n✓ Analyzed {len(results)} videos")
    
    return results


def demo_progress_tracking():
    """Demonstrate progress tracking and visualization"""
    print("\n" + "="*60)
    print("DEMO 3: Progress Tracking and Visualization")
    print("="*60)
    
    # Initialize pipeline
    pipeline = SmartSwingPipeline()
    
    # Generate progress report
    pipeline.generate_progress_report('./metrics/progress_report.png')
    
    print("\n✓ Progress report generated")


def demo_metrics_export():
    """Demonstrate metrics export"""
    print("\n" + "="*60)
    print("DEMO 4: Metrics Export")
    print("="*60)
    
    pipeline = SmartSwingPipeline()
    
    # Export to CSV
    pipeline.progress_tracker.export_to_csv('./metrics/all_sessions.csv')
    
    print("\n✓ Metrics exported to CSV")


def print_performance_metrics(results_list: list):
    """
    Print performance metrics summary
    
    Args:
        results_list: List of analysis results
    """
    print("\n" + "="*60)
    print("PERFORMANCE METRICS SUMMARY")
    print("="*60)
    
    if not results_list:
        print("No results to summarize")
        return
    
    # Calculate statistics
    processing_times = [r.get('processing_time', 0) for r in results_list]
    overall_scores = [r.get('scores', {}).get('overall_score', 0) for r in results_list]
    
    print(f"\nTotal Videos Analyzed: {len(results_list)}")
    print(f"\nProcessing Times:")
    print(f"  Average: {np.mean(processing_times):.2f}s")
    print(f"  Min: {np.min(processing_times):.2f}s")
    print(f"  Max: {np.max(processing_times):.2f}s")
    
    print(f"\nOverall Scores:")
    print(f"  Average: {np.mean(overall_scores):.1f}/100")
    print(f"  Min: {np.min(overall_scores):.1f}/100")
    print(f"  Max: {np.max(overall_scores):.1f}/100")
    
    # Component-wise statistics
    print(f"\nComponent Scores (Average):")
    print("-" * 40)
    
    all_components = {}
    for result in results_list:
        components = result.get('scores', {}).get('component_scores', {})
        for comp, score in components.items():
            if comp not in all_components:
                all_components[comp] = []
            all_components[comp].append(score)
    
    for comp, scores in sorted(all_components.items()):
        comp_name = comp.replace('_', ' ').title()
        avg_score = np.mean(scores)
        print(f"  {comp_name:.<35} {avg_score:5.1f}/100")
    
    # Error frequency
    print(f"\nCommon Errors Detected:")
    print("-" * 40)
    
    all_errors = []
    for result in results_list:
        errors = result.get('analysis', {}).get('errors', [])
        all_errors.extend(errors)
    
    if all_errors:
        from collections import Counter
        error_counts = Counter(all_errors)
        for error, count in error_counts.most_common(5):
            error_name = error.replace('_', ' ').title()
            print(f"  {error_name}: {count} occurrences")
    else:
        print("  No errors detected")
    
    print("\n" + "="*60)


def main():
    """Main demo execution"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║              SmartSwing Golf Analysis System               ║
    ║         Computer Vision-Based Swing Analysis Demo         ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Create directories
        os.makedirs('./data/videos', exist_ok=True)
        os.makedirs('./results', exist_ok=True)
        os.makedirs('./metrics', exist_ok=True)
        
        all_results = []
        
        # Demo 1: Single video analysis
        result1 = demo_single_video_analysis()
        if 'error' not in result1:
            all_results.append(result1)
        
        # time.sleep(1)-------------------------------------------
    
        # Demo 2: Multiple video analysis
        # results2 = demo_multiple_video_analysis()
        # all_results.extend([r for r in results2 if 'error' not in r])
        
        # time.sleep(1)
        
        # Demo 3: Progress tracking
        demo_progress_tracking()
        
        # time.sleep(1)-------------------------------------------
        
        # Demo 4: Metrics export
        demo_metrics_export()
        
        # Print performance summary
        print_performance_metrics(all_results)
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nGenerated Files:")
        print("  Videos: ./results/")
        print("  Reports: ./results/")
        print("  Metrics: ./metrics/")
        print("  Data: ./data/")
        
        print("\nFeatures Demonstrated:")
        print("  ✓ Automatic swing detection")
        print("  ✓ Pose estimation and keypoint extraction")
        print("  ✓ Biomechanical analysis (swing plane, rotation, weight transfer)")
        print("  ✓ Performance scoring (0-100 scale)")
        print("  ✓ Visual feedback with annotated videos")
        print("  ✓ Progress tracking and visualization")
        print("  ✓ Error detection and corrective guidance")
        print("  ✓ Batch processing capability")
        print("  ✓ Metrics export (CSV)")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
