"""
Swing Scoring System
Generates performance scores based on biomechanical analysis
"""

import numpy as np
from typing import Dict, List
from config import SCORING_WEIGHTS, BIOMECHANICS


class SwingScorer:
    """
    Calculates comprehensive swing accuracy score
    """
    
    def __init__(self):
        """Initialize swing scorer"""
        self.weights = SCORING_WEIGHTS
        
    def calculate_swing_score(self,
                             swing_plane_metrics: dict,
                             rotation_metrics: dict,
                             weight_transfer_metrics: dict,
                             wrist_metrics: dict,
                             tempo_metrics: dict) -> dict:
        """
        Calculate overall swing accuracy score (0-100)
        
        Args:
            swing_plane_metrics: Swing plane analysis results
            rotation_metrics: Rotation analysis results
            weight_transfer_metrics: Weight transfer results
            wrist_metrics: Wrist angle results
            tempo_metrics: Tempo analysis results
            
        Returns:
            Dictionary with overall score and component scores
        """
        # Calculate component scores
        plane_score = self._score_swing_plane(swing_plane_metrics)
        rotation_score = self._score_rotation(rotation_metrics)
        downswing_score = self._score_downswing_alignment(rotation_metrics, weight_transfer_metrics)
        wrist_score = wrist_metrics.get('wrist_hinge_score', 0)
        weight_score = weight_transfer_metrics.get('weight_transfer_score', 0)
        tempo_score = tempo_metrics.get('tempo_score', 0)
        
        # Calculate weighted overall score
        overall_score = (
            plane_score * self.weights['swing_plane_consistency'] +
            rotation_score * self.weights['rotation_quality'] +
            downswing_score * self.weights['downswing_alignment'] +
            wrist_score * self.weights['wrist_hinge'] +
            weight_score * self.weights['weight_transfer'] +
            tempo_score * self.weights['tempo']
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'component_scores': {
                'swing_plane_consistency': round(plane_score, 2),
                'rotation_quality': round(rotation_score, 2),
                'downswing_alignment': round(downswing_score, 2),
                'wrist_hinge': round(wrist_score, 2),
                'weight_transfer': round(weight_score, 2),
                'tempo': round(tempo_score, 2)
            },
            'grade': self._get_grade(overall_score),
            'strengths': self._identify_strengths({
                'swing_plane_consistency': plane_score,
                'rotation_quality': rotation_score,
                'downswing_alignment': downswing_score,
                'wrist_hinge': wrist_score,
                'weight_transfer': weight_score,
                'tempo': tempo_score
            }),
            'areas_for_improvement': self._identify_weaknesses({
                'swing_plane_consistency': plane_score,
                'rotation_quality': rotation_score,
                'downswing_alignment': downswing_score,
                'wrist_hinge': wrist_score,
                'weight_transfer': weight_score,
                'tempo': tempo_score
            })
        }
    
    def _score_swing_plane(self, metrics: dict) -> float:
        """
        Score swing plane consistency
        
        Args:
            metrics: Swing plane metrics
            
        Returns:
            Score from 0-100
        """
        if not metrics:
            return 0.0
        
        # Score based on plane consistency
        consistency_score = metrics.get('plane_consistency', 0)
        
        # Score based on angle accuracy
        angle_error = metrics.get('angle_error', 90)
        angle_score = max(0, 100 - (angle_error / BIOMECHANICS['swing_plane_tolerance']) * 50)
        
        # Combined score
        return (consistency_score * 0.6 + angle_score * 0.4)
    
    def _score_rotation(self, metrics: dict) -> float:
        """
        Score hip and shoulder rotation quality
        
        Args:
            metrics: Rotation metrics
            
        Returns:
            Score from 0-100
        """
        if not metrics:
            return 0.0
        
        # Score based on rotation sequence
        sequence_score = metrics.get('rotation_sequence_score', 0)
        
        # Score based on rotation magnitude
        max_shoulder = metrics.get('max_shoulder_rotation', 0)
        max_hip = metrics.get('max_hip_rotation', 0)
        
        # Check if rotations are in ideal range
        shoulder_score = self._score_in_range(
            max_shoulder,
            BIOMECHANICS['ideal_shoulder_rotation'],
            BIOMECHANICS['rotation_tolerance']
        )
        
        hip_score = self._score_in_range(
            max_hip,
            BIOMECHANICS['ideal_hip_rotation'],
            BIOMECHANICS['rotation_tolerance']
        )
        
        # Combined score
        return (sequence_score * 0.4 + shoulder_score * 0.3 + hip_score * 0.3)
    
    def _score_downswing_alignment(self, rotation_metrics: dict, 
                                   weight_metrics: dict) -> float:
        """
        Score downswing path and alignment
        
        Args:
            rotation_metrics: Rotation metrics
            weight_metrics: Weight transfer metrics
            
        Returns:
            Score from 0-100
        """
        # Use rotation sequence and weight transfer as proxies for downswing quality
        rotation_score = rotation_metrics.get('rotation_sequence_score', 0)
        weight_score = weight_metrics.get('weight_transfer_score', 0)
        
        return (rotation_score * 0.6 + weight_score * 0.4)
    
    def _score_in_range(self, value: float, ideal: float, tolerance: float) -> float:
        """
        Score a value based on how close it is to ideal within tolerance
        
        Args:
            value: Measured value
            ideal: Ideal value
            tolerance: Acceptable tolerance
            
        Returns:
            Score from 0-100
        """
        error = abs(value - ideal)
        if error <= tolerance:
            return 100 - (error / tolerance) * 30  # 70-100 within tolerance
        else:
            return max(0, 70 - ((error - tolerance) / tolerance) * 70)
    
    def _get_grade(self, score: float) -> str:
        """
        Convert score to letter grade
        
        Args:
            score: Overall score (0-100)
            
        Returns:
            Letter grade
        """
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _identify_strengths(self, component_scores: dict) -> List[str]:
        """
        Identify top performing components
        
        Args:
            component_scores: Dictionary of component scores
            
        Returns:
            List of strength descriptions
        """
        strengths = []
        
        # Sort components by score
        sorted_components = sorted(component_scores.items(), 
                                  key=lambda x: x[1], reverse=True)
        
        # Identify top performers (>= 80)
        for component, score in sorted_components[:3]:
            if score >= 80:
                strength_msg = self._get_strength_message(component, score)
                if strength_msg:
                    strengths.append(strength_msg)
        
        return strengths if strengths else ["Continue practicing to develop strengths"]
    
    def _identify_weaknesses(self, component_scores: dict) -> List[str]:
        """
        Identify areas needing improvement
        
        Args:
            component_scores: Dictionary of component scores
            
        Returns:
            List of improvement recommendations
        """
        weaknesses = []
        
        # Sort components by score (ascending)
        sorted_components = sorted(component_scores.items(), key=lambda x: x[1])
        
        # Identify bottom performers (< 70)
        for component, score in sorted_components[:3]:
            if score < 70:
                weakness_msg = self._get_weakness_message(component, score)
                if weakness_msg:
                    weaknesses.append(weakness_msg)
        
        return weaknesses if weaknesses else ["Great swing! Keep maintaining your form"]
    
    def _get_strength_message(self, component: str, score: float) -> str:
        """
        Generate strength message for component
        
        Args:
            component: Component name
            score: Component score
            
        Returns:
            Strength description
        """
        messages = {
            'swing_plane_consistency': f"Excellent swing plane consistency ({score:.0f}/100)",
            'rotation_quality': f"Strong body rotation mechanics ({score:.0f}/100)",
            'downswing_alignment': f"Well-aligned downswing path ({score:.0f}/100)",
            'wrist_hinge': f"Good wrist hinge timing ({score:.0f}/100)",
            'weight_transfer': f"Effective weight transfer ({score:.0f}/100)",
            'tempo': f"Smooth swing tempo ({score:.0f}/100)"
        }
        return messages.get(component, "")
    
    def _get_weakness_message(self, component: str, score: float) -> str:
        """
        Generate improvement message for component
        
        Args:
            component: Component name
            score: Component score
            
        Returns:
            Improvement recommendation
        """
        messages = {
            'swing_plane_consistency': f"Work on maintaining consistent swing plane - try half swings ({score:.0f}/100)",
            'rotation_quality': f"Improve body rotation - focus on shoulder turn over hip turn ({score:.0f}/100)",
            'downswing_alignment': f"Improve downswing path - practice inside-out swing path drills ({score:.0f}/100)",
            'wrist_hinge': f"Better wrist hinge needed - practice wrist cock drills ({score:.0f}/100)",
            'weight_transfer': f"Increase weight transfer - practice shift drills from back to front foot ({score:.0f}/100)",
            'tempo': f"Adjust swing tempo - aim for 3:1 backswing to downswing ratio ({score:.0f}/100)"
        }
        return messages.get(component, "")
    
    def generate_detailed_report(self, 
                                analysis_results: dict,
                                score_results: dict) -> str:
        """
        Generate detailed text report of swing analysis
        
        Args:
            analysis_results: Complete analysis results
            score_results: Scoring results
            
        Returns:
            Formatted text report
        """
        report = []
        report.append("=" * 60)
        report.append("SWING ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Overall Score
        report.append(f"Overall Swing Score: {score_results['overall_score']:.1f}/100")
        report.append(f"Grade: {score_results['grade']}")
        report.append("")
        
        # Component Scores
        report.append("Component Scores:")
        report.append("-" * 40)
        for component, score in score_results['component_scores'].items():
            component_name = component.replace('_', ' ').title()
            bar = '█' * int(score / 5) + '░' * (20 - int(score / 5))
            report.append(f"  {component_name:.<30} {score:5.1f}/100 [{bar}]")
        report.append("")
        
        # Strengths
        if score_results['strengths']:
            report.append("Strengths:")
            report.append("-" * 40)
            for strength in score_results['strengths']:
                report.append(f"  ✓ {strength}")
            report.append("")
        
        # Areas for Improvement
        if score_results['areas_for_improvement']:
            report.append("Areas for Improvement:")
            report.append("-" * 40)
            for improvement in score_results['areas_for_improvement']:
                report.append(f"  ⚠ {improvement}")
            report.append("")
        
        # Detailed Metrics
        report.append("Detailed Metrics:")
        report.append("-" * 40)
        
        if 'swing_plane' in analysis_results:
            sp = analysis_results['swing_plane']
            report.append(f"  Swing Plane Angle: {sp.get('swing_plane_angle', 0):.1f}° "
                         f"(ideal: {sp.get('ideal_angle', 0):.1f}°)")
            report.append(f"  Plane Consistency: {sp.get('plane_consistency', 0):.1f}/100")
        
        if 'rotation' in analysis_results:
            rot = analysis_results['rotation']
            report.append(f"  Max Shoulder Rotation: {rot.get('max_shoulder_rotation', 0):.1f}°")
            report.append(f"  Max Hip Rotation: {rot.get('max_hip_rotation', 0):.1f}°")
        
        if 'weight_transfer' in analysis_results:
            wt = analysis_results['weight_transfer']
            report.append(f"  Weight Shift: {wt.get('max_weight_shift', 0):.2%}")
        
        if 'tempo' in analysis_results:
            tempo = analysis_results['tempo']
            report.append(f"  Tempo Ratio: {tempo.get('tempo_ratio', 0):.2f}:1 (backswing:downswing)")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
