"""
Progress Tracking Module
Stores and visualizes swing session history
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from config import STORAGE


class ProgressTracker:
    """
    Tracks swing sessions and visualizes progress over time
    """
    
    def __init__(self, data_dir: str = STORAGE['data_dir']):
        """
        Initialize progress tracker
        
        Args:
            data_dir: Directory to store session data
        """
        self.data_dir = data_dir
        self.sessions_file = os.path.join(data_dir, STORAGE['sessions_file'])
        
        # Create directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(STORAGE['results_dir'], exist_ok=True)
        os.makedirs(STORAGE['metrics_dir'], exist_ok=True)
        
        # Load existing sessions
        self.sessions = self._load_sessions()
    
    def _load_sessions(self) -> List[Dict]:
        """
        Load session history from file
        
        Returns:
            List of session dictionaries
        """
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_sessions(self) -> None:
        """Save session history to file"""
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    def add_session(self,
                   video_path: str,
                   analysis_results: dict,
                   score_results: dict) -> str:
        """
        Add new swing session to history
        
        Args:
            video_path: Path to video file
            analysis_results: Complete analysis results
            score_results: Scoring results
            
        Returns:
            Session ID
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        session = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'video_path': video_path,
            'overall_score': score_results.get('overall_score', 0),
            'grade': score_results.get('grade', 'N/A'),
            'component_scores': score_results.get('component_scores', {}),
            'strengths': score_results.get('strengths', []),
            'areas_for_improvement': score_results.get('areas_for_improvement', []),
            'swing_plane_angle': analysis_results.get('swing_plane', {}).get('swing_plane_angle', 0),
            'max_shoulder_rotation': analysis_results.get('rotation', {}).get('max_shoulder_rotation', 0),
            'max_hip_rotation': analysis_results.get('rotation', {}).get('max_hip_rotation', 0),
            'weight_shift': analysis_results.get('weight_transfer', {}).get('max_weight_shift', 0),
            'tempo_ratio': analysis_results.get('tempo', {}).get('tempo_ratio', 0),
            'errors': analysis_results.get('errors', [])
        }
        
        self.sessions.append(session)
        self._save_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get specific session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session dictionary or None
        """
        for session in self.sessions:
            if session['session_id'] == session_id:
                return session
        return None
    
    def get_recent_sessions(self, n: int = 10) -> List[Dict]:
        """
        Get most recent sessions
        
        Args:
            n: Number of sessions to return
            
        Returns:
            List of session dictionaries
        """
        return sorted(self.sessions, 
                     key=lambda x: x['timestamp'], 
                     reverse=True)[:n]
    
    def visualize_progress(self, output_path: str = None) -> None:
        """
        Create progress visualization charts
        
        Args:
            output_path: Path to save visualization
        """
        if not self.sessions:
            print("No sessions to visualize")
            return
        
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))
        
        # Prepare data
        df = pd.DataFrame(self.sessions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # 1. Overall Score Timeline
        ax1 = plt.subplot(3, 2, 1)
        ax1.plot(df['timestamp'], df['overall_score'], 
                marker='o', linewidth=2, markersize=8, color='#2E86AB')
        ax1.axhline(y=80, color='g', linestyle='--', alpha=0.5, label='Good (80)')
        ax1.axhline(y=60, color='orange', linestyle='--', alpha=0.5, label='Fair (60)')
        ax1.set_xlabel('Date', fontsize=10)
        ax1.set_ylabel('Overall Score', fontsize=10)
        ax1.set_title('Swing Score Progress', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        plt.xticks(rotation=45)
        
        # 2. Component Scores Heatmap (last 10 sessions)
        ax2 = plt.subplot(3, 2, 2)
        recent_sessions = df.tail(min(10, len(df)))
        
        if len(recent_sessions) > 0:
            component_data = []
            component_names = []
            
            for idx, session in recent_sessions.iterrows():
                scores = session.get('component_scores', {})
                if not component_names:
                    component_names = [name.replace('_', ' ').title() 
                                      for name in scores.keys()]
                component_data.append(list(scores.values()))
            
            if component_data:
                component_df = pd.DataFrame(component_data, 
                                          columns=component_names)
                sns.heatmap(component_df.T, annot=True, fmt='.1f', 
                           cmap='RdYlGn', center=70, vmin=0, vmax=100,
                           cbar_kws={'label': 'Score'}, ax=ax2)
                ax2.set_xlabel('Session', fontsize=10)
                ax2.set_title('Component Scores (Recent Sessions)', 
                            fontsize=12, fontweight='bold')
        
        # 3. Biomechanical Metrics Over Time
        ax3 = plt.subplot(3, 2, 3)
        ax3_twin = ax3.twinx()
        
        line1 = ax3.plot(df['timestamp'], df['max_shoulder_rotation'], 
                marker='s', label='Shoulder Rotation', color='#A23B72', linewidth=2)
        line2 = ax3.plot(df['timestamp'], df['max_hip_rotation'], 
                marker='^', label='Hip Rotation', color='#F18F01', linewidth=2)
        
        ax3.set_xlabel('Date', fontsize=10)
        ax3.set_ylabel('Rotation (degrees)', fontsize=10)
        ax3.set_title('Body Rotation Metrics', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper left')
        
        # 4. Weight Transfer and Tempo
        ax4 = plt.subplot(3, 2, 4)
        ax4.plot(df['timestamp'], df['weight_shift'] * 100, 
                marker='D', label='Weight Shift (%)', color='#C73E1D', linewidth=2)
        ax4.axhline(y=15, color='g', linestyle='--', alpha=0.5, label='Target (15%)')
        ax4.set_xlabel('Date', fontsize=10)
        ax4.set_ylabel('Weight Shift (%)', fontsize=10)
        ax4.set_title('Weight Transfer Progress', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        plt.xticks(rotation=45)
        
        # 5. Grade Distribution
        ax5 = plt.subplot(3, 2, 5)
        grade_counts = df['grade'].value_counts().sort_index()
        colors_grade = {'A': '#2E7D32', 'B': '#558B2F', 'C': '#FBC02D', 
                       'D': '#F57C00', 'F': '#D32F2F'}
        bar_colors = [colors_grade.get(grade, '#757575') for grade in grade_counts.index]
        
        ax5.bar(grade_counts.index, grade_counts.values, color=bar_colors)
        ax5.set_xlabel('Grade', fontsize=10)
        ax5.set_ylabel('Frequency', fontsize=10)
        ax5.set_title('Grade Distribution', fontsize=12, fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='y')
        
        # 6. Most Common Errors
        ax6 = plt.subplot(3, 2, 6)
        all_errors = []
        for session in self.sessions:
            all_errors.extend(session.get('errors', []))
        
        if all_errors:
            error_counts = pd.Series(all_errors).value_counts().head(5)
            error_labels = [e.replace('_', ' ').title() for e in error_counts.index]
            
            ax6.barh(error_labels, error_counts.values, color='#E63946')
            ax6.set_xlabel('Frequency', fontsize=10)
            ax6.set_title('Most Common Errors', fontsize=12, fontweight='bold')
            ax6.grid(True, alpha=0.3, axis='x')
        else:
            ax6.text(0.5, 0.5, 'No errors detected', 
                    ha='center', va='center', fontsize=12)
            ax6.set_xlim(0, 1)
            ax6.set_ylim(0, 1)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Progress visualization saved to: {output_path}")
        else:
            plt.savefig(os.path.join(STORAGE['metrics_dir'], 'progress_report.png'),
                       dpi=300, bbox_inches='tight')
        
        plt.close()
    
    def generate_progress_report(self) -> str:
        """
        Generate text progress report
        
        Returns:
            Formatted text report
        """
        if not self.sessions:
            return "No sessions recorded yet."
        
        report = []
        report.append("=" * 60)
        report.append("PROGRESS REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary statistics
        df = pd.DataFrame(self.sessions)
        
        report.append(f"Total Sessions: {len(self.sessions)}")
        report.append(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        report.append("")
        
        # Score statistics
        report.append("Score Statistics:")
        report.append("-" * 40)
        report.append(f"  Current Score: {df['overall_score'].iloc[-1]:.1f}")
        report.append(f"  Average Score: {df['overall_score'].mean():.1f}")
        report.append(f"  Best Score: {df['overall_score'].max():.1f}")
        report.append(f"  Improvement: {df['overall_score'].iloc[-1] - df['overall_score'].iloc[0]:.1f} points")
        report.append("")
        
        # Recent trend
        if len(df) >= 3:
            recent_trend = df['overall_score'].tail(3).diff().mean()
            trend_text = "↑ Improving" if recent_trend > 0 else "↓ Declining" if recent_trend < 0 else "→ Stable"
            report.append(f"Recent Trend: {trend_text}")
            report.append("")
        
        # Most improved component
        if len(df) >= 2:
            first_components = df.iloc[0]['component_scores']
            last_components = df.iloc[-1]['component_scores']
            
            improvements = {}
            for component in first_components.keys():
                if component in last_components:
                    improvements[component] = last_components[component] - first_components[component]
            
            if improvements:
                best_component = max(improvements.items(), key=lambda x: x[1])
                worst_component = min(improvements.items(), key=lambda x: x[1])
                
                report.append("Component Improvements:")
                report.append("-" * 40)
                report.append(f"  Most Improved: {best_component[0].replace('_', ' ').title()} "
                            f"(+{best_component[1]:.1f})")
                report.append(f"  Needs Focus: {worst_component[0].replace('_', ' ').title()} "
                            f"({worst_component[1]:+.1f})")
                report.append("")
        
        # Common persistent issues
        recent_sessions = df.tail(5)
        all_recent_errors = []
        for _, session in recent_sessions.iterrows():
            all_recent_errors.extend(session.get('errors', []))
        
        if all_recent_errors:
            error_counts = pd.Series(all_recent_errors).value_counts()
            report.append("Persistent Issues (Last 5 Sessions):")
            report.append("-" * 40)
            for error, count in error_counts.head(3).items():
                report.append(f"  • {error.replace('_', ' ').title()} "
                            f"(appeared {count} times)")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def export_to_csv(self, output_path: str = None) -> None:
        """
        Export session data to CSV
        
        Args:
            output_path: Path to save CSV file
        """
        if not self.sessions:
            print("No sessions to export")
            return
        
        df = pd.DataFrame(self.sessions)
        
        # Flatten component scores
        component_df = pd.json_normalize(df['component_scores'])
        df = pd.concat([df.drop('component_scores', axis=1), component_df], axis=1)
        
        if output_path is None:
            output_path = os.path.join(STORAGE['metrics_dir'], 'sessions_export.csv')
        
        df.to_csv(output_path, index=False)
        print(f"Session data exported to: {output_path}")
