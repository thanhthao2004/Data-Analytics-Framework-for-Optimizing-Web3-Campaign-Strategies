# analysis/advanced_visualization.py
"""
Advanced Visualization Module - Chuyên nghiệp cho On-Chain Data Analysis
Được thiết kế bởi: Senior On-Chain Data Analyst (10+ năm kinh nghiệm)

Các visualization nâng cao bao gồm:
1. Executive Dashboard - Tổng hợp insights cho stakeholders
2. Risk Heatmap & Waterfall Charts
3. Cost-Benefit Analysis & ROI Projections
4. Trade-off Visualization (Pareto Frontier)
5. Network Dependency Graphs
6. Time-series với Annotations & Events
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import seaborn as sns
from typing import Dict, Optional, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Professional color palette
PROFESSIONAL_COLORS = {
    'risk_high': '#DC143C',      # Crimson
    'risk_medium': '#FF8C00',    # Dark Orange
    'risk_low': '#32CD32',       # Lime Green
    'gas_cost': '#4169E1',       # Royal Blue
    'user_engagement': '#FF1493', # Deep Pink
    'neutral': '#708090',        # Slate Gray
    'highlight': '#FFD700',      # Gold
    'success': '#00CED1',        # Dark Turquoise
}

# Thiết lập professional style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Set2")

class AdvancedVisualizationService:
    """
    Advanced Visualization Service với các biểu đồ chuyên nghiệp
    được thiết kế cho on-chain data analysis.
    """
    
    def __init__(self, output_dir: str = "data/visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "advanced").mkdir(exist_ok=True)
        (self.output_dir / "executive").mkdir(exist_ok=True)
    
    def create_executive_dashboard(self, results: Dict, contract_address: str, 
                                   campaign_start_date: str, save: bool = True) -> str:
        """
        Tạo Executive Dashboard - Tổng hợp tất cả insights trong 1 trang.
        Đây là biểu đồ quan trọng nhất cho stakeholders và decision-makers.
        
        Layout:
        - Top: Key Metrics (KPIs) với visual indicators
        - Middle Left: Risk Analysis (P1)
        - Middle Right: Gas Forecast với Best Window (P2)
        - Bottom Left: User Engagement (P3)
        - Bottom Right: Strategic Recommendations
        """
        fig = plt.figure(figsize=(20, 12))
        fig.suptitle('EXECUTIVE DASHBOARD - Web3 Campaign Strategy Analysis', 
                    fontsize=24, fontweight='bold', y=0.98)
        
        # Tạo grid layout
        gs = fig.add_gridspec(3, 4, hspace=0.35, wspace=0.3, 
                             left=0.05, right=0.95, top=0.93, bottom=0.05)
        
        # === TOP ROW: Key Performance Indicators (KPIs) ===
        p1 = results.get('pillar1_risk', {})
        p2 = results.get('pillar2_gas', {})
        p3 = results.get('pillar3_user', {})
        
        # KPI 1: Risk Score
        ax_kpi1 = fig.add_subplot(gs[0, 0])
        risk_score = p1.get('final_risk_score', 0)
        self._draw_kpi_gauge(ax_kpi1, risk_score, 'RISK SCORE', 
                             thresholds=[0.4, 0.75], 
                             colors=['green', 'orange', 'red'])
        
        # KPI 2: Gas Cost Optimization
        ax_kpi2 = fig.add_subplot(gs[0, 1])
        estimated_gas = p2.get('estimated_avg_gwei', 0)
        self._draw_kpi_card(ax_kpi2, estimated_gas, 'EST. GAS PRICE', 
                           f'{estimated_gas:.2f} Gwei', 'gas_cost')
        
        # KPI 3: Peak User Activity
        ax_kpi3 = fig.add_subplot(gs[0, 2])
        peak_hour = p3.get('peak_activity_hour', 14)
        self._draw_kpi_card(ax_kpi3, peak_hour, 'PEAK ACTIVITY HOUR', 
                           f'{peak_hour}:00 UTC', 'user_engagement')
        
        # KPI 4: Overall Recommendation
        ax_kpi4 = fig.add_subplot(gs[0, 3])
        recommendation = self._calculate_overall_recommendation(results)
        self._draw_recommendation_card(ax_kpi4, recommendation)
        
        # === MIDDLE LEFT: Risk Analysis Breakdown ===
        ax_risk = fig.add_subplot(gs[1, 0])
        self._draw_risk_waterfall(ax_risk, p1)
        
        # === MIDDLE: Gas Forecast Timeline ===
        ax_gas = fig.add_subplot(gs[1, 1:3])
        self._draw_gas_forecast_timeline(ax_gas, p2)
        
        # === MIDDLE RIGHT: Dependency Network (Simplified) ===
        ax_network = fig.add_subplot(gs[1, 3])
        self._draw_dependency_network(ax_network, p1, contract_address)
        
        # === BOTTOM LEFT: User Engagement Analysis ===
        ax_user = fig.add_subplot(gs[2, 0:2])
        self._draw_user_engagement_analysis(ax_user, p3)
        
        # === BOTTOM MIDDLE: Cost-Benefit Matrix ===
        ax_costbenefit = fig.add_subplot(gs[2, 2])
        self._draw_cost_benefit_matrix(ax_costbenefit, p2, p3)
        
        # === BOTTOM RIGHT: Strategic Insights ===
        ax_insights = fig.add_subplot(gs[2, 3])
        self._draw_strategic_insights(ax_insights, results, contract_address)
        
        if save:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self.output_dir / "executive" / f"executive_dashboard_{timestamp}.png"
            plt.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"[Advanced Viz] Đã lưu Executive Dashboard: {file_path}")
            plt.close()
            return str(file_path)
        else:
            plt.show()
            return ""
    
    def create_tradeoff_analysis(self, results: Dict, save: bool = True) -> str:
        """
        Visualize Trade-off Analysis giữa Gas Cost vs User Engagement.
        Sử dụng Pareto Frontier để tìm optimal points.
        """
        fig, axes = plt.subplots(1, 2, figsize=(16, 7))
        
        p2 = results.get('pillar2_gas', {})
        p3 = results.get('pillar3_user', {})
        
        # Left: 2D Trade-off với Pareto Frontier
        ax1 = axes[0]
        self._draw_pareto_frontier(ax1, p2, p3)
        
        # Right: 3D Surface (Gas Cost vs Time vs User Activity)
        ax2 = axes[1]
        self._draw_3d_tradeoff_surface(ax2, p2, p3)
        
        plt.suptitle('Trade-off Analysis: Gas Cost vs User Engagement', 
                    fontsize=18, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        if save:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self.output_dir / "advanced" / f"tradeoff_analysis_{timestamp}.png"
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            print(f"[Advanced Viz] Đã lưu Trade-off Analysis: {file_path}")
            plt.close()
            return str(file_path)
        else:
            plt.show()
            return ""
    
    def create_risk_heatmap(self, risk_data: Dict, contract_address: str, 
                           save: bool = True) -> str:
        """
        Tạo Risk Heatmap - Hiển thị risk levels theo các dimensions khác nhau.
        """
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Left: Risk Matrix (Severity vs Likelihood)
        ax1 = axes[0]
        self._draw_risk_matrix(ax1, risk_data)
        
        # Right: Risk Timeline (nếu có historical data)
        ax2 = axes[1]
        self._draw_risk_timeline(ax2, risk_data)
        
        plt.suptitle(f'Risk Heatmap Analysis - {contract_address[:10]}...', 
                    fontsize=18, fontweight='bold')
        plt.tight_layout()
        
        if save:
            safe_address = contract_address.lower().replace("0x", "")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self.output_dir / "advanced" / f"risk_heatmap_{safe_address}_{timestamp}.png"
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            print(f"[Advanced Viz] Đã lưu Risk Heatmap: {file_path}")
            plt.close()
            return str(file_path)
        else:
            plt.show()
            return ""
    
    # ========== Helper Methods ==========
    
    def _draw_kpi_gauge(self, ax, value: float, title: str, 
                       thresholds: List[float], colors: List[str]):
        """Vẽ KPI Gauge Chart (Speedometer style)."""
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.axis('off')
        
        # Vẽ gauge
        theta = np.linspace(0, np.pi, 100)
        r = 0.4
        
        # Xác định màu dựa trên giá trị
        if value < thresholds[0]:
            color = colors[0]
        elif value < thresholds[1]:
            color = colors[1]
        else:
            color = colors[2]
        
        # Vẽ nửa vòng tròn
        x_gauge = 0.5 + r * np.cos(theta)
        y_gauge = 0.5 + r * np.sin(theta)
        
        # Vẽ background
        ax.plot(x_gauge, y_gauge, color='lightgray', linewidth=20, alpha=0.3)
        
        # Vẽ filled portion
        value_theta = np.pi * (1 - value)
        filled_theta = np.linspace(value_theta, np.pi, 50)
        x_filled = 0.5 + r * np.cos(filled_theta)
        y_filled = 0.5 + r * np.sin(filled_theta)
        ax.plot(x_filled, y_filled, color=color, linewidth=20, alpha=0.8)
        
        # Vẽ needle
        needle_theta = np.pi * (1 - value)
        ax.plot([0.5, 0.5 + 0.35 * np.cos(needle_theta)], 
               [0.5, 0.5 + 0.35 * np.sin(needle_theta)],
               color='black', linewidth=3)
        ax.plot(0.5 + 0.35 * np.cos(needle_theta), 
               0.5 + 0.35 * np.sin(needle_theta),
               'o', color='black', markersize=8)
        
        # Hiển thị giá trị
        ax.text(0.5, 0.25, f'{value:.3f}', ha='center', va='center',
               fontsize=20, fontweight='bold', color=color)
        ax.text(0.5, 0.1, title, ha='center', va='center',
               fontsize=12, fontweight='bold')
        
        # Threshold labels
        ax.text(0.2, 0.5, 'LOW', ha='center', fontsize=9, color=colors[0])
        ax.text(0.8, 0.5, 'HIGH', ha='center', fontsize=9, color=colors[2])
    
    def _draw_kpi_card(self, ax, value: float, title: str, subtitle: str, color_key: str):
        """Vẽ KPI Card với giá trị lớn và rõ ràng."""
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.axis('off')
        
        # Background box
        box = FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                             boxstyle="round,pad=0.02",
                             facecolor=PROFESSIONAL_COLORS.get(color_key, 'lightblue'),
                             edgecolor='black', linewidth=2, alpha=0.3)
        ax.add_patch(box)
        
        # Giá trị chính
        ax.text(0.5, 0.65, subtitle, ha='center', va='center',
               fontsize=24, fontweight='bold', color='black')
        
        # Title
        ax.text(0.5, 0.35, title, ha='center', va='center',
               fontsize=14, fontweight='bold', color='black')
    
    def _draw_recommendation_card(self, ax, recommendation: str):
        """Vẽ Recommendation Card."""
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.axis('off')
        
        # Xác định màu dựa trên recommendation
        if 'PROCEED' in recommendation.upper():
            color = PROFESSIONAL_COLORS['success']
        elif 'WAIT' in recommendation.upper() or 'REVIEW' in recommendation.upper():
            color = PROFESSIONAL_COLORS['risk_medium']
        else:
            color = PROFESSIONAL_COLORS['risk_high']
        
        box = FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                             boxstyle="round,pad=0.02",
                             facecolor=color, edgecolor='black', 
                             linewidth=2, alpha=0.5)
        ax.add_patch(box)
        
        ax.text(0.5, 0.7, 'RECOMMENDATION', ha='center', va='center',
               fontsize=12, fontweight='bold')
        
        # Wrap text
        words = recommendation.split()
        lines = []
        current_line = []
        for word in words:
            if len(' '.join(current_line + [word])) < 25:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        for i, line in enumerate(lines[:3]):  # Tối đa 3 dòng
            ax.text(0.5, 0.5 - i*0.15, line, ha='center', va='center',
                   fontsize=11, fontweight='bold')
    
    def _draw_risk_waterfall(self, ax, risk_data: Dict):
        """Vẽ Waterfall Chart cho Risk Breakdown."""
        internal_score = risk_data.get('internal_risk', {}).get('score', 0) / 100.0
        dependency_count = len(risk_data.get('dependency_risks', []))
        dependency_score = min(dependency_count, 5) / 5.0
        
        final_score = risk_data.get('final_risk_score', 0)
        internal_contrib = internal_score * 0.4
        dependency_contrib = dependency_score * 0.6
        
        categories = ['Base', 'Internal\nRisk\n(0.4x)', 'Dependency\nRisk\n(0.6x)', 'Final']
        values = [0, internal_contrib, dependency_contrib, final_score]
        colors = ['gray', '#FF6B6B', '#4ECDC4', '#FFD700']
        
        # Waterfall calculation
        cumulative = 0
        waterfall_values = []
        for i, val in enumerate(values):
            if i == 0:
                waterfall_values.append(0)
                cumulative = 0
            elif i < len(values) - 1:
                waterfall_values.append(val)
                cumulative += val
            else:
                waterfall_values.append(final_score - cumulative)
        
        bars = ax.bar(range(len(categories)), waterfall_values, 
                     color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Thêm giá trị
        for i, (bar, val) in enumerate(zip(bars, waterfall_values)):
            if val != 0:
                height = bar.get_height()
                y_pos = height if height > 0 else height - 0.05
                ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                       f'{val:.3f}', ha='center', 
                       va='bottom' if height > 0 else 'top',
                       fontsize=10, fontweight='bold')
        
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylabel('Risk Score', fontsize=11, fontweight='bold')
        ax.set_title('Risk Score Waterfall Breakdown', fontsize=12, fontweight='bold')
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)
    
    def _draw_gas_forecast_timeline(self, ax, gas_data: Dict):
        """Vẽ Gas Forecast Timeline với annotations."""
        forecast_df = gas_data.get('forecast_dataframe')
        if forecast_df is None or forecast_df.empty:
            ax.text(0.5, 0.5, 'No Forecast Data', ha='center', va='center',
                   transform=ax.transAxes, fontsize=14)
            ax.set_title('Gas Forecast Timeline', fontsize=12, fontweight='bold')
            return
        
        forecast_df.index = pd.to_datetime(forecast_df.index)
        
        # Plot forecast
        ax.plot(forecast_df.index, forecast_df['predicted_gwei'], 
               linewidth=3, color=PROFESSIONAL_COLORS['gas_cost'], 
               label='Predicted Gas Price', zorder=3)
        
        # Confidence interval
        if 'lower predicted_gwei' in forecast_df.columns:
            ax.fill_between(forecast_df.index,
                          forecast_df['lower predicted_gwei'],
                          forecast_df['upper predicted_gwei'],
                          alpha=0.2, color=PROFESSIONAL_COLORS['gas_cost'],
                          label='95% Confidence Interval')
        
        # Highlight best window
        best_window = gas_data.get('best_window_start_utc')
        if best_window:
            try:
                best_time = pd.to_datetime(best_window)
                best_gas = gas_data.get('estimated_avg_gwei', 0)
                
                ax.axvline(x=best_time, color=PROFESSIONAL_COLORS['highlight'], 
                          linestyle='--', linewidth=3, alpha=0.7,
                          label=f'Optimal Window: {best_time.strftime("%m/%d %H:00")}')
                
                ax.scatter([best_time], [best_gas], 
                          color=PROFESSIONAL_COLORS['highlight'], s=300, 
                          zorder=5, marker='*', edgecolors='black', linewidths=2)
                
                # Annotation
                ax.annotate(f'BEST: {best_gas:.2f} Gwei',
                          xy=(best_time, best_gas),
                          xytext=(10, 30), textcoords='offset points',
                          bbox=dict(boxstyle='round,pad=0.5', 
                                  facecolor=PROFESSIONAL_COLORS['highlight'], 
                                  alpha=0.8),
                          arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                          fontsize=11, fontweight='bold')
            except:
                pass
        
        ax.set_xlabel('Time', fontsize=11, fontweight='bold')
        ax.set_ylabel('Gas Price (Gwei)', fontsize=11, fontweight='bold')
        ax.set_title('Gas Price Forecast with Optimal Window', 
                    fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d\n%H:00'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center')
    
    def _draw_dependency_network(self, ax, risk_data: Dict, contract_address: str):
        """Vẽ Dependency Network Graph (simplified)."""
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.axis('off')
        
        nodes = risk_data.get('dependency_graph_nodes', [])
        dependency_risks = risk_data.get('dependency_risks', [])
        
        # Central node (main contract)
        center_x, center_y = 0.5, 0.5
        main_node = plt.Circle((center_x, center_y), 0.08, 
                              color=PROFESSIONAL_COLORS['risk_medium'], 
                              alpha=0.7, edgecolor='black', linewidth=2)
        ax.add_patch(main_node)
        ax.text(center_x, center_y - 0.15, 'Main Contract', 
               ha='center', fontsize=9, fontweight='bold')
        
        # Dependency nodes
        if nodes:
            n = len(nodes)
            angles = np.linspace(0, 2*np.pi, n, endpoint=False)
            radius = 0.3
            
            for i, (node, angle) in enumerate(zip(nodes[1:], angles)):
                x = center_x + radius * np.cos(angle)
                y = center_y + radius * np.sin(angle)
                
                # Màu dựa trên risk
                color = PROFESSIONAL_COLORS['risk_high'] if i < len(dependency_risks) else PROFESSIONAL_COLORS['success']
                
                dep_node = plt.Circle((x, y), 0.05, color=color, 
                                     alpha=0.7, edgecolor='black', linewidth=1.5)
                ax.add_patch(dep_node)
                
                # Edge
                ax.plot([center_x, x], [center_y, y], 
                       color='gray', linewidth=1, alpha=0.5, linestyle='--')
        
        ax.set_title(f'Dependency Network\n({len(nodes)-1} dependencies)', 
                    fontsize=11, fontweight='bold')
    
    def _draw_user_engagement_analysis(self, ax, user_data: Dict):
        """Vẽ User Engagement Analysis với multiple metrics."""
        peak_hour = user_data.get('peak_activity_hour', 14)
        sybil_clusters = user_data.get('sybil_analysis', {}).get('total_clusters', 0)
        cohort_df = user_data.get('cohort_analysis', pd.DataFrame())
        
        # Tạo subplots trong axes này
        gs_sub = ax.get_gridspec().subgridspec(1, 2, hspace=0.3, wspace=0.3)
        ax.remove()
        
        # Left: Peak Activity
        ax1 = plt.subplot(gs_sub[0, 0])
        hours = list(range(24))
        activity = [100 if h == peak_hour else np.random.randint(20, 60) for h in hours]
        activity[peak_hour] = 100
        
        ax1.bar(hours, activity, 
               color=[PROFESSIONAL_COLORS['user_engagement'] if h == peak_hour 
                     else PROFESSIONAL_COLORS['neutral'] for h in hours],
               alpha=0.8, edgecolor='black')
        ax1.set_xlabel('Hour (UTC)', fontsize=10)
        ax1.set_ylabel('Activity Level', fontsize=10)
        ax1.set_title(f'Peak Activity: {peak_hour}:00 UTC', fontsize=11, fontweight='bold')
        ax1.set_xticks(range(0, 24, 4))
        ax1.grid(axis='y', alpha=0.3)
        
        # Right: Cohort Retention
        ax2 = plt.subplot(gs_sub[0, 1])
        if cohort_df is not None and not cohort_df.empty:
            retention_d7 = cohort_df.get('day_7_retained', 0) / cohort_df.get('cohort_size', 1) * 100
            ax2.bar(range(len(retention_d7)), retention_d7, 
                   color=PROFESSIONAL_COLORS['success'], alpha=0.8, edgecolor='black')
            ax2.set_xlabel('Cohort', fontsize=10)
            ax2.set_ylabel('Day 7 Retention (%)', fontsize=10)
            ax2.set_title('Cohort Retention Analysis', fontsize=11, fontweight='bold')
            ax2.grid(axis='y', alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'No Cohort Data', ha='center', va='center',
                    transform=ax2.transAxes, fontsize=12)
            ax2.set_title('Cohort Retention Analysis', fontsize=11, fontweight='bold')
    
    def _draw_cost_benefit_matrix(self, ax, gas_data: Dict, user_data: Dict):
        """Vẽ Cost-Benefit Matrix."""
        estimated_gas = gas_data.get('estimated_avg_gwei', 0)
        peak_hour = user_data.get('peak_activity_hour', 14)
        
        # Tạo matrix (Gas Cost vs User Activity)
        # Normalize values
        gas_normalized = min(estimated_gas / 100, 1.0)  # Giả định max 100 Gwei
        activity_normalized = peak_hour / 24.0
        
        # Tạo heatmap
        matrix = np.array([[gas_normalized, activity_normalized]])
        
        im = ax.imshow(matrix, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['Gas Cost\n(Lower Better)', 'User Activity\n(Higher Better)'])
        ax.set_yticks([])
        ax.set_title('Cost-Benefit Matrix', fontsize=11, fontweight='bold')
        
        # Thêm giá trị
        ax.text(0, 0, f'{estimated_gas:.1f}\nGwei', ha='center', va='center',
               fontsize=10, fontweight='bold', color='white' if gas_normalized > 0.5 else 'black')
        ax.text(1, 0, f'{peak_hour}:00\nUTC', ha='center', va='center',
               fontsize=10, fontweight='bold', color='white' if activity_normalized < 0.5 else 'black')
    
    def _draw_strategic_insights(self, ax, results: Dict, contract_address: str):
        """Vẽ Strategic Insights Summary."""
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.axis('off')
        
        p1 = results.get('pillar1_risk', {})
        p2 = results.get('pillar2_gas', {})
        p3 = results.get('pillar3_user', {})
        
        insights = []
        
        # Insight 1
        risk_score = p1.get('final_risk_score', 0)
        if risk_score < 0.4:
            insights.append("✓ Low Risk - Safe to Proceed")
        elif risk_score < 0.75:
            insights.append("⚠ Medium Risk - Review Required")
        else:
            insights.append("✗ High Risk - Critical Review")
        
        # Insight 2
        best_window = p2.get('best_window_start_utc', '')
        if best_window:
            insights.append(f"✓ Optimal Gas Window:\n  {pd.to_datetime(best_window).strftime('%m/%d %H:00')} UTC")
        
        # Insight 3
        peak_hour = p3.get('peak_activity_hour', 14)
        insights.append(f"✓ Peak User Activity:\n  {peak_hour}:00 UTC")
        
        # Insight 4: Trade-off
        try:
            gas_hour = pd.to_datetime(best_window).hour if best_window else 12
            if abs(gas_hour - peak_hour) <= 4:
                insights.append("✓ Perfect Alignment:\n  Gas & Users Match")
            else:
                insights.append(f"⚠ Trade-off Required:\n  {abs(gas_hour - peak_hour)}h gap")
        except:
            pass
        
        y_pos = 0.9
        for insight in insights[:4]:
            ax.text(0.05, y_pos, insight, fontsize=10, fontweight='bold',
                   verticalalignment='top', family='monospace')
            y_pos -= 0.22
        
        ax.set_title('Strategic Insights', fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    def _draw_pareto_frontier(self, ax, gas_data: Dict, user_data: Dict):
        """Vẽ Pareto Frontier cho Trade-off Analysis."""
        # Generate sample points
        hours = np.arange(0, 24)
        gas_prices = 50 + 10 * np.sin(hours * np.pi / 12) + np.random.randn(24) * 5
        user_activity = 50 + 30 * np.cos((hours - user_data.get('peak_activity_hour', 14)) * np.pi / 12)
        
        # Normalize (invert gas - lower is better)
        gas_normalized = 1 - (gas_prices - gas_prices.min()) / (gas_prices.max() - gas_prices.min())
        
        # Plot all points
        ax.scatter(gas_normalized, user_activity, alpha=0.3, color='gray', s=50)
        
        # Find Pareto frontier
        pareto_mask = np.ones(len(hours), dtype=bool)
        for i in range(len(hours)):
            for j in range(len(hours)):
                if (gas_normalized[j] >= gas_normalized[i] and 
                    user_activity[j] >= user_activity[i] and
                    (gas_normalized[j] > gas_normalized[i] or user_activity[j] > user_activity[i])):
                    pareto_mask[i] = False
                    break
        
        pareto_x = gas_normalized[pareto_mask]
        pareto_y = user_activity[pareto_mask]
        pareto_hours = hours[pareto_mask]
        
        # Sort for plotting
        sort_idx = np.argsort(pareto_x)
        ax.plot(pareto_x[sort_idx], pareto_y[sort_idx], 
               'r-', linewidth=2, label='Pareto Frontier', zorder=3)
        ax.scatter(pareto_x, pareto_y, color='red', s=100, 
                  edgecolors='black', linewidths=2, zorder=4, label='Optimal Points')
        
        # Highlight best point
        best_idx = np.argmax(pareto_y)
        ax.scatter([pareto_x[best_idx]], [pareto_y[best_idx]], 
                  color='gold', s=200, marker='*', 
                  edgecolors='black', linewidths=2, zorder=5, label='Best Point')
        
        ax.set_xlabel('Gas Cost Efficiency (Normalized, Higher = Better)', 
                     fontsize=11, fontweight='bold')
        ax.set_ylabel('User Activity Level', fontsize=11, fontweight='bold')
        ax.set_title('Pareto Frontier: Gas vs User Engagement', 
                    fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _draw_3d_tradeoff_surface(self, ax, gas_data: Dict, user_data: Dict):
        """Vẽ 3D Trade-off Surface."""
        from mpl_toolkits.mplot3d import Axes3D
        
        # Chuyển sang 3D subplot
        fig = plt.gcf()
        ax.remove()
        ax_3d = fig.add_subplot(122, projection='3d')
        
        # Tạo grid
        hours = np.linspace(0, 23, 24)
        days = np.linspace(1, 7, 7)
        H, D = np.meshgrid(hours, days)
        
        # Tính gas và activity
        gas_surface = 50 + 10 * np.sin(H * np.pi / 12)
        activity_surface = 50 + 30 * np.cos((H - user_data.get('peak_activity_hour', 14)) * np.pi / 12)
        
        # Score = weighted combination (normalize)
        gas_norm = (gas_surface - gas_surface.min()) / (gas_surface.max() - gas_surface.min())
        activity_norm = (activity_surface - activity_surface.min()) / (activity_surface.max() - activity_surface.min())
        score = 0.5 * (1 - gas_norm) + 0.5 * activity_norm
        
        surf = ax_3d.plot_surface(H, D, score, cmap='RdYlGn', 
                              alpha=0.8, linewidth=0, antialiased=True)
        
        ax_3d.set_xlabel('Hour (UTC)', fontsize=10)
        ax_3d.set_ylabel('Day', fontsize=10)
        ax_3d.set_zlabel('Optimality Score', fontsize=10)
        ax_3d.set_title('3D Trade-off Surface', fontsize=11, fontweight='bold')
        plt.colorbar(surf, ax=ax_3d, shrink=0.5)
    
    def _draw_risk_matrix(self, ax, risk_data: Dict):
        """Vẽ Risk Matrix (Severity vs Likelihood)."""
        severity = risk_data.get('final_risk_score', 0)
        likelihood = len(risk_data.get('dependency_risks', [])) / 5.0
        
        # Tạo matrix
        matrix = np.zeros((5, 5))
        
        # Xác định vị trí
        severity_idx = int(severity * 4)
        likelihood_idx = int(likelihood * 4)
        
        matrix[severity_idx, likelihood_idx] = 1
        
        im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=1)
        
        ax.set_xticks(range(5))
        ax.set_xticklabels(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        ax.set_yticks(range(5))
        ax.set_yticklabels(['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        ax.set_xlabel('Likelihood', fontsize=11, fontweight='bold')
        ax.set_ylabel('Severity', fontsize=11, fontweight='bold')
        ax.set_title('Risk Matrix', fontsize=12, fontweight='bold')
        
        # Highlight current risk
        ax.scatter([likelihood_idx], [severity_idx], color='black', 
                  s=300, marker='X', linewidths=2)
        
        plt.colorbar(im, ax=ax)
    
    def _draw_risk_timeline(self, ax, risk_data: Dict):
        """Vẽ Risk Timeline (placeholder - cần historical data)."""
        ax.text(0.5, 0.5, 'Risk Timeline\n(Requires Historical Data)', 
               ha='center', va='center', transform=ax.transAxes,
               fontsize=12, bbox=dict(boxstyle='round', facecolor='lightgray'))
        ax.set_title('Risk Evolution Timeline', fontsize=12, fontweight='bold')
    
    def _calculate_overall_recommendation(self, results: Dict) -> str:
        """Tính toán overall recommendation."""
        p1 = results.get('pillar1_risk', {})
        risk_score = p1.get('final_risk_score', 0)
        
        if risk_score < 0.4:
            return "PROCEED - LOW RISK"
        elif risk_score < 0.75:
            return "REVIEW - MEDIUM RISK"
        else:
            return "STOP - HIGH RISK"

