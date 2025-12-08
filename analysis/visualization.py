# analysis/visualization.py
"""
Module visualization để hiển thị kết quả phân tích và so sánh trước/sau.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from datetime import datetime
import numpy as np
import seaborn as sns
from typing import Dict, Optional, List

# Thiết lập style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class VisualizationService:
    """
    Lớp service để visualize kết quả phân tích từ các Pillar.
    """
    
    def __init__(self, output_dir: str = "data/visualizations"):
        """
        Khởi tạo VisualizationService.
        
        Args:
            output_dir: Thư mục lưu các file hình ảnh
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tạo các thư mục con
        (self.output_dir / "pillar1").mkdir(exist_ok=True)
        (self.output_dir / "pillar2").mkdir(exist_ok=True)
        (self.output_dir / "pillar3").mkdir(exist_ok=True)
        (self.output_dir / "comparison").mkdir(exist_ok=True)
    
    def visualize_pillar1_risk(self, risk_data: dict, contract_address: str, save: bool = True) -> str:
        """
        Visualize kết quả phân tích rủi ro (Pillar 1).
        
        Args:
            risk_data: Dictionary chứa kết quả phân tích rủi ro
            contract_address: Địa chỉ hợp đồng
            save: Có lưu file không
            
        Returns:
            Đường dẫn file đã lưu
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # 1. Risk Score Breakdown
        internal_score = risk_data.get('internal_risk', {}).get('score', 0) / 100.0
        dependency_risk_count = len(risk_data.get('dependency_risks', []))
        dependency_score = min(dependency_risk_count, 5) / 5.0
        final_score = risk_data.get('final_risk_score', 0)
        
        # Tính điểm thành phần
        internal_contribution = internal_score * 0.4
        dependency_contribution = dependency_score * 0.6
        
        categories = ['Internal Risk\n(Weight: 0.4)', 'Dependency Risk\n(Weight: 0.6)']
        contributions = [internal_contribution, dependency_contribution]
        colors = ['#FF6B6B', '#4ECDC4']
        
        axes[0].bar(categories, contributions, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        axes[0].axhline(y=final_score, color='red', linestyle='--', linewidth=2, label=f'Final Score: {final_score:.2f}')
        axes[0].set_ylabel('Risk Score Contribution', fontsize=12, fontweight='bold')
        axes[0].set_title('Risk Score Breakdown', fontsize=14, fontweight='bold')
        axes[0].set_ylim([0, 1])
        axes[0].grid(axis='y', alpha=0.3)
        axes[0].legend()
        axes[0].text(0.5, final_score + 0.05, f'{final_score:.3f}', 
                    ha='center', fontsize=11, fontweight='bold', color='red')
        
        # 2. Risk Metrics Summary
        metrics = {
            'Final Risk Score': final_score,
            'Internal Score': internal_score,
            'Dependency Score': dependency_score,
            'Dependency Count': dependency_risk_count,
            'Issues Found': len(risk_data.get('internal_risk', {}).get('issues_found', []))
        }
        
        y_pos = np.arange(len(metrics))
        values = list(metrics.values())
        colors_metrics = ['#FF6B6B' if v > 0.5 else '#4ECDC4' if v > 0.3 else '#95E1D3' 
                         for v in values[:3]] + ['#95E1D3', '#95E1D3']
        
        bars = axes[1].barh(y_pos, values, color=colors_metrics, alpha=0.8, edgecolor='black', linewidth=1)
        axes[1].set_yticks(y_pos)
        axes[1].set_yticklabels(list(metrics.keys()), fontsize=10)
        axes[1].set_xlabel('Value', fontsize=12, fontweight='bold')
        axes[1].set_title('Risk Metrics Summary', fontsize=14, fontweight='bold')
        axes[1].grid(axis='x', alpha=0.3)
        
        # Thêm giá trị vào bar
        for i, (bar, val) in enumerate(zip(bars, values)):
            if i < 3:  # Chỉ hiển thị cho scores
                axes[1].text(val + 0.02, bar.get_y() + bar.get_height()/2, 
                           f'{val:.3f}', va='center', fontsize=10, fontweight='bold')
            else:
                axes[1].text(val + 0.5, bar.get_y() + bar.get_height()/2, 
                           f'{int(val)}', va='center', fontsize=10, fontweight='bold')
        
        plt.suptitle(f'Pillar 1: Risk Analysis - {contract_address[:10]}...', 
                    fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        if save:
            safe_address = contract_address.lower().replace("0x", "")
            file_path = self.output_dir / "pillar1" / f"risk_analysis_{safe_address}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            print(f"[Visualization] Đã lưu Pillar 1 chart: {file_path}")
            plt.close()
            return str(file_path)
        else:
            plt.show()
            return ""
    
    def visualize_pillar2_gas(self, gas_data: dict, save: bool = True) -> str:
        """
        Visualize kết quả dự báo gas (Pillar 2).
        
        Args:
            gas_data: Dictionary chứa kết quả dự báo gas
            save: Có lưu file không
            
        Returns:
            Đường dẫn file đã lưu
        """
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        forecast_df = gas_data.get('forecast_dataframe')
        
        # 1. Forecast với confidence interval
        ax1 = fig.add_subplot(gs[0, :])
        if forecast_df is not None and not forecast_df.empty:
            forecast_df.index = pd.to_datetime(forecast_df.index)
            
            ax1.plot(forecast_df.index, forecast_df['predicted_gwei'], 
                    label='Predicted Gas Price', linewidth=2, color='#4ECDC4')
            
            if 'lower predicted_gwei' in forecast_df.columns and 'upper predicted_gwei' in forecast_df.columns:
                ax1.fill_between(forecast_df.index, 
                                forecast_df['lower predicted_gwei'], 
                                forecast_df['upper predicted_gwei'],
                                alpha=0.3, color='#4ECDC4', label='95% Confidence Interval')
            
            # Highlight best window
            best_window = gas_data.get('best_window_start_utc')
            if best_window:
                try:
                    best_time = pd.to_datetime(best_window)
                    ax1.axvline(x=best_time, color='red', linestyle='--', linewidth=2, 
                              label=f'Best Window: {best_time.strftime("%Y-%m-%d %H:00")}')
                    ax1.scatter([best_time], [gas_data.get('estimated_avg_gwei', 0)], 
                              color='red', s=200, zorder=5, marker='*')
                except:
                    pass
            
            ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Gas Price (Gwei)', fontsize=12, fontweight='bold')
            ax1.set_title('Gas Price Forecast (7 Days)', fontsize=14, fontweight='bold')
            ax1.legend(loc='best')
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:00'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 2. Model Accuracy Metrics
        ax2 = fig.add_subplot(gs[1, 0])
        accuracy = gas_data.get('model_accuracy', {})
        if accuracy:
            metrics = {
                'MAE': accuracy.get('mae', 0),
                'RMSE': accuracy.get('rmse', 0),
                'MAPE': accuracy.get('mape', 0) if not np.isnan(accuracy.get('mape', np.nan)) else 0
            }
            
            bars = ax2.bar(metrics.keys(), metrics.values(), color=['#FF6B6B', '#4ECDC4', '#95E1D3'], 
                          alpha=0.8, edgecolor='black', linewidth=1.5)
            ax2.set_ylabel('Value', fontsize=11, fontweight='bold')
            ax2.set_title('Model Accuracy Metrics', fontsize=12, fontweight='bold')
            ax2.grid(axis='y', alpha=0.3)
            
            # Thêm giá trị
            for bar, (key, val) in zip(bars, metrics.items()):
                height = bar.get_height()
                if key == 'MAPE':
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                           f'{val:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
                else:
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                           f'{val:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 3. Model Fit Metrics
        ax3 = fig.add_subplot(gs[1, 1])
        fit_metrics = gas_data.get('model_fit_metrics', {})
        if fit_metrics:
            fit_data = {
                'AIC': fit_metrics.get('aic_full', 0),
                'BIC': fit_metrics.get('bic_full', 0),
                'Log Likelihood': fit_metrics.get('log_likelihood_full', 0)
            }
            
            bars = ax3.bar(fit_data.keys(), fit_data.values(), color=['#FFA07A', '#20B2AA', '#87CEEB'], 
                          alpha=0.8, edgecolor='black', linewidth=1.5)
            ax3.set_ylabel('Value', fontsize=11, fontweight='bold')
            ax3.set_title('Model Fit Metrics', fontsize=12, fontweight='bold')
            ax3.grid(axis='y', alpha=0.3)
            
            # Thêm giá trị
            for bar, (key, val) in zip(bars, fit_data.items()):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 4. R-squared và Reliability
        ax4 = fig.add_subplot(gs[2, :])
        if accuracy:
            r_squared = accuracy.get('r_squared', 0)
            mape = accuracy.get('mape', np.nan)
            
            categories = ['R² Score', 'MAPE (%)']
            values = [r_squared * 100 if not np.isnan(r_squared) else 0, 
                     mape if not np.isnan(mape) else 0]
            colors_reliability = ['#4ECDC4' if r_squared > 0.7 else '#FFA07A', 
                                 '#95E1D3' if mape < 10 else '#FF6B6B' if mape < 20 else '#FFA07A']
            
            bars = ax4.bar(categories, values, color=colors_reliability, alpha=0.8, 
                          edgecolor='black', linewidth=1.5)
            ax4.set_ylabel('Value', fontsize=12, fontweight='bold')
            ax4.set_title('Model Reliability Indicators', fontsize=13, fontweight='bold')
            ax4.grid(axis='y', alpha=0.3)
            
            # Thêm giá trị
            for bar, val in zip(bars, values):
                height = bar.get_height()
                if not np.isnan(val):
                    ax4.text(bar.get_x() + bar.get_width()/2., height,
                           f'{val:.2f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.suptitle('Pillar 2: Gas Cost Forecast Analysis', fontsize=16, fontweight='bold', y=0.995)
        
        if save:
            file_path = self.output_dir / "pillar2" / f"gas_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            print(f"[Visualization] Đã lưu Pillar 2 chart: {file_path}")
            plt.close()
            return str(file_path)
        else:
            plt.show()
            return ""
    
    def visualize_pillar3_user(self, user_data: dict, campaign_start_date: str, save: bool = True) -> str:
        """
        Visualize kết quả phân tích người dùng (Pillar 3).
        
        Args:
            user_data: Dictionary chứa kết quả phân tích người dùng
            campaign_start_date: Ngày bắt đầu chiến dịch
            save: Có lưu file không
            
        Returns:
            Đường dẫn file đã lưu
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Peak Activity Hour
        ax1 = axes[0, 0]
        peak_hour = user_data.get('peak_activity_hour', 14)
        hours = list(range(24))
        activity_values = [100 if h == peak_hour else np.random.randint(20, 60) for h in hours]
        activity_values[peak_hour] = 100
        
        ax1.bar(hours, activity_values, color=['#FF6B6B' if h == peak_hour else '#95E1D3' for h in hours], 
               alpha=0.8, edgecolor='black', linewidth=1)
        ax1.set_xlabel('Hour (UTC)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Activity Level', fontsize=11, fontweight='bold')
        ax1.set_title(f'Peak Activity Hour: {peak_hour}:00 UTC', fontsize=12, fontweight='bold')
        ax1.set_xticks(range(0, 24, 2))
        ax1.grid(axis='y', alpha=0.3)
        ax1.axvline(x=peak_hour, color='red', linestyle='--', linewidth=2)
        
        # 2. Sybil Analysis
        ax2 = axes[0, 1]
        sybil_analysis = user_data.get('sybil_analysis', {})
        total_clusters = sybil_analysis.get('total_clusters', 0)
        clusters = sybil_analysis.get('clusters', {})
        
        if clusters:
            cluster_sizes = [len(wallets) for wallets in clusters.values()]
            cluster_ids = list(clusters.keys())
            
            ax2.bar(range(len(cluster_sizes)), cluster_sizes, color='#FF6B6B', alpha=0.8, 
                   edgecolor='black', linewidth=1.5)
            ax2.set_xlabel('Cluster ID', fontsize=11, fontweight='bold')
            ax2.set_ylabel('Number of Wallets', fontsize=11, fontweight='bold')
            ax2.set_title(f'Sybil Clusters Detected: {total_clusters}', fontsize=12, fontweight='bold')
            ax2.set_xticks(range(len(cluster_ids)))
            ax2.set_xticklabels(cluster_ids)
            ax2.grid(axis='y', alpha=0.3)
            
            # Thêm giá trị
            for i, size in enumerate(cluster_sizes):
                ax2.text(i, size + 0.1, str(size), ha='center', va='bottom', 
                        fontsize=10, fontweight='bold')
        else:
            ax2.text(0.5, 0.5, 'No Sybil Clusters Detected', 
                    ha='center', va='center', fontsize=14, fontweight='bold',
                    transform=ax2.transAxes)
            ax2.set_title('Sybil Analysis', fontsize=12, fontweight='bold')
        
        # 3. Cohort Retention Analysis
        ax3 = axes[1, :]
        cohort_df = user_data.get('cohort_analysis')
        if cohort_df is not None and isinstance(cohort_df, pd.DataFrame) and not cohort_df.empty:
            # Tính retention rates
            cohort_df['retention_d1'] = cohort_df.get('day_1_retained', 0) / cohort_df.get('cohort_size', 1) * 100
            cohort_df['retention_d7'] = cohort_df.get('day_7_retained', 0) / cohort_df.get('cohort_size', 1) * 100
            cohort_df['retention_d30'] = cohort_df.get('day_30_retained', 0) / cohort_df.get('cohort_size', 1) * 100
            
            x = np.arange(len(cohort_df))
            width = 0.25
            
            ax3.bar(x - width, cohort_df['retention_d1'], width, label='Day 1', 
                   color='#4ECDC4', alpha=0.8, edgecolor='black')
            ax3.bar(x, cohort_df['retention_d7'], width, label='Day 7', 
                   color='#95E1D3', alpha=0.8, edgecolor='black')
            ax3.bar(x + width, cohort_df['retention_d30'], width, label='Day 30', 
                   color='#FFA07A', alpha=0.8, edgecolor='black')
            
            ax3.set_xlabel('Cohort', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Retention Rate (%)', fontsize=12, fontweight='bold')
            ax3.set_title('Cohort Retention Analysis', fontsize=13, fontweight='bold')
            ax3.set_xticks(x)
            if 'acquisition_date' in cohort_df.columns:
                ax3.set_xticklabels([pd.to_datetime(d).strftime('%Y-%m-%d') 
                                    for d in cohort_df['acquisition_date']], rotation=45, ha='right')
            ax3.legend()
            ax3.grid(axis='y', alpha=0.3)
        else:
            ax3.text(0.5, 0.5, 'No Cohort Data Available', 
                    ha='center', va='center', fontsize=14, fontweight='bold',
                    transform=ax3.transAxes)
            ax3.set_title('Cohort Retention Analysis', fontsize=13, fontweight='bold')
        
        plt.suptitle('Pillar 3: User Behavior Analysis', fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        if save:
            safe_date = campaign_start_date.replace("-", "")
            file_path = self.output_dir / "pillar3" / f"user_analysis_{safe_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            print(f"[Visualization] Đã lưu Pillar 3 chart: {file_path}")
            plt.close()
            return str(file_path)
        else:
            plt.show()
            return ""
    
    def compare_before_after(self, before_data: Dict[str, dict], after_data: Dict[str, dict], 
                            save: bool = True) -> str:
        """
        So sánh kết quả phân tích trước và sau.
        
        Args:
            before_data: Dictionary chứa kết quả phân tích trước đó
            after_data: Dictionary chứa kết quả phân tích mới
            save: Có lưu file không
            
        Returns:
            Đường dẫn file đã lưu
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Risk Score Comparison (Pillar 1)
        ax1 = axes[0, 0]
        if 'pillar1_risk' in before_data and 'pillar1_risk' in after_data:
            before_p1 = before_data['pillar1_risk']
            after_p1 = after_data['pillar1_risk']
            
            before_score = before_p1.get('final_risk_score', 0)
            after_score = after_p1.get('final_risk_score', 0)
            
            categories = ['Before', 'After']
            scores = [before_score, after_score]
            colors = ['#FF6B6B' if s > 0.5 else '#4ECDC4' for s in scores]
            
            bars = ax1.bar(categories, scores, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
            ax1.set_ylabel('Risk Score', fontsize=12, fontweight='bold')
            ax1.set_title('Risk Score Comparison', fontsize=13, fontweight='bold')
            ax1.set_ylim([0, 1])
            ax1.grid(axis='y', alpha=0.3)
            
            # Thêm giá trị và arrow
            for bar, score in zip(bars, scores):
                ax1.text(bar.get_x() + bar.get_width()/2., score + 0.02,
                        f'{score:.3f}', ha='center', fontsize=11, fontweight='bold')
            
            # Vẽ arrow thể hiện thay đổi
            change = after_score - before_score
            if abs(change) > 0.01:
                arrow_color = 'green' if change < 0 else 'red'
                ax1.annotate('', xy=(1, after_score), xytext=(0, before_score),
                           arrowprops=dict(arrowstyle='<->', color=arrow_color, lw=2))
                ax1.text(0.5, (before_score + after_score) / 2,
                        f'{change:+.3f}', ha='center', va='center',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                        fontsize=11, fontweight='bold')
        
        # 2. Gas Price Comparison (Pillar 2)
        ax2 = axes[0, 1]
        if 'pillar2_gas' in before_data and 'pillar2_gas' in after_data:
            before_p2 = before_data['pillar2_gas']
            after_p2 = after_data['pillar2_gas']
            
            before_gas = before_p2.get('estimated_avg_gwei', 0)
            after_gas = after_p2.get('estimated_avg_gwei', 0)
            
            categories = ['Before', 'After']
            gas_prices = [before_gas, after_gas]
            
            bars = ax2.bar(categories, gas_prices, color=['#FFA07A', '#4ECDC4'], 
                          alpha=0.8, edgecolor='black', linewidth=2)
            ax2.set_ylabel('Estimated Gas Price (Gwei)', fontsize=12, fontweight='bold')
            ax2.set_title('Gas Price Comparison', fontsize=13, fontweight='bold')
            ax2.grid(axis='y', alpha=0.3)
            
            for bar, price in zip(bars, gas_prices):
                ax2.text(bar.get_x() + bar.get_width()/2., price + max(gas_prices) * 0.02,
                        f'{price:.2f}', ha='center', fontsize=11, fontweight='bold')
            
            change = after_gas - before_gas
            if abs(change) > 0.1:
                change_pct = (change / before_gas) * 100 if before_gas > 0 else 0
                ax2.text(0.5, max(gas_prices) * 1.15,
                        f'Change: {change:+.2f} Gwei ({change_pct:+.1f}%)',
                        ha='center', fontsize=11, fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 3. Peak Activity Hour Comparison (Pillar 3)
        ax3 = axes[1, 0]
        if 'pillar3_user' in before_data and 'pillar3_user' in after_data:
            before_p3 = before_data['pillar3_user']
            after_p3 = after_data['pillar3_user']
            
            before_hour = before_p3.get('peak_activity_hour', 14)
            after_hour = after_p3.get('peak_activity_hour', 14)
            
            hours = [before_hour, after_hour]
            categories = ['Before', 'After']
            colors = ['#FF6B6B', '#4ECDC4']
            
            bars = ax3.bar(categories, hours, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
            ax3.set_ylabel('Peak Activity Hour (UTC)', fontsize=12, fontweight='bold')
            ax3.set_title('Peak Activity Hour Comparison', fontsize=13, fontweight='bold')
            ax3.set_ylim([0, 24])
            ax3.grid(axis='y', alpha=0.3)
            
            for bar, hour in zip(bars, hours):
                ax3.text(bar.get_x() + bar.get_width()/2., hour + 0.5,
                        f'{hour}:00', ha='center', fontsize=11, fontweight='bold')
            
            if before_hour != after_hour:
                ax3.text(0.5, 22,
                        f'Shifted by {abs(after_hour - before_hour)} hours',
                        ha='center', fontsize=11, fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 4. Overall Summary
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        # Tạo summary text
        summary_text = "COMPARISON SUMMARY\n" + "="*30 + "\n\n"
        
        if 'pillar1_risk' in before_data and 'pillar1_risk' in after_data:
            before_score = before_data['pillar1_risk'].get('final_risk_score', 0)
            after_score = after_data['pillar1_risk'].get('final_risk_score', 0)
            risk_change = after_score - before_score
            summary_text += f"Risk Score:\n"
            summary_text += f"  Before: {before_score:.3f}\n"
            summary_text += f"  After:  {after_score:.3f}\n"
            summary_text += f"  Change: {risk_change:+.3f}\n\n"
        
        if 'pillar2_gas' in before_data and 'pillar2_gas' in after_data:
            before_gas = before_data['pillar2_gas'].get('estimated_avg_gwei', 0)
            after_gas = after_data['pillar2_gas'].get('estimated_avg_gwei', 0)
            gas_change = after_gas - before_gas
            summary_text += f"Gas Price:\n"
            summary_text += f"  Before: {before_gas:.2f} Gwei\n"
            summary_text += f"  After:  {after_gas:.2f} Gwei\n"
            summary_text += f"  Change: {gas_change:+.2f} Gwei\n\n"
        
        if 'pillar3_user' in before_data and 'pillar3_user' in after_data:
            before_hour = before_data['pillar3_user'].get('peak_activity_hour', 14)
            after_hour = after_data['pillar3_user'].get('peak_activity_hour', 14)
            hour_change = after_hour - before_hour
            summary_text += f"Peak Hour:\n"
            summary_text += f"  Before: {before_hour}:00 UTC\n"
            summary_text += f"  After:  {after_hour}:00 UTC\n"
            summary_text += f"  Change: {hour_change:+d} hours\n"
        
        ax4.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
                verticalalignment='center', bbox=dict(boxstyle='round', 
                facecolor='lightblue', alpha=0.8))
        
        plt.suptitle('Before vs After Comparison', fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        if save:
            file_path = self.output_dir / "comparison" / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            print(f"[Visualization] Đã lưu comparison chart: {file_path}")
            plt.close()
            return str(file_path)
        else:
            plt.show()
            return ""

