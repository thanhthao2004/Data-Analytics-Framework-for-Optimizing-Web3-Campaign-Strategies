# Tích hợp 3 trụ cột, thực hiện logic "trade-off"
from analysis.pillar1_risk_model import ContractRiskAnalyzer
from analysis.pillar2_gas_model import GasCostForecaster
from analysis.pillar3_user_model import UserBehaviorAnalyzer
from analysis.visualization import VisualizationService
from analysis.advanced_visualization import AdvancedVisualizationService
import pandas as pd
import numpy as np
from typing import Dict
class AnalysisService:
    """
    Dịch vụ Tích hợp Framework.
    Lớp "nhạc trưởng" này chạy cả 3 trụ cột và thực hiện 
    phân tích "trade-off" để đưa ra khuyến nghị chiến lược[cite: 196].
    
    ================================================================================
    THẢO LUẬN HỌC THUẬT VÀ NOVELTY CỦA FRAMEWORK
    ================================================================================
    
    1. NOVELTY VÀ SỰ KHÁC BIỆT CỦA FRAMEWORK
    ----------------------------------------
    
    Framework này khác biệt so với các công cụ hiện có ở khả năng TÍCH HỢP và 
    PHÂN TÍCH TRADE-OFF đa chiều trong một mô hình duy nhất:
    
    * Pillar 1 (Bảo mật): Tích hợp phân tích mã nguồn tĩnh (Slither) với phân tích
      đồ thị phụ thuộc (Dependency Graph) từ dữ liệu on-chain.
    * Pillar 2 (Chi phí): Sử dụng mô hình dự báo chuỗi thời gian (ARIMA) để tối ưu
      thời điểm triển khai dựa trên dự báo chi phí gas.
    * Pillar 3 (Hiệu quả Marketing): Phân tích hành vi người dùng (Sybil detection,
      Cohort analysis) để đánh giá chất lượng người dùng.
    
    Framework này là một CÔNG CỤ HỖ TRỢ QUYẾT ĐỊNH CHIẾN LƯỢC (Strategic Decision 
    Support Tool) bằng cách CÂN BẰNG các yếu tố Bảo mật, Chi phí, và Hiệu quả Marketing.
    
    So sánh với các công cụ hiện có:
    - Slither, Mythril: Chỉ tập trung vào BẢO MẬT (một chiều)
    - GasNow, Etherscan forecasters: Chỉ tập trung vào TỐI ƯU GAS (một chiều)
    - Dune Analytics, Nansen: Chỉ tập trung vào PHÂN TÍCH USER (một chiều)
    
    → Framework này là DUY NHẤT trong việc kết hợp cả 3 khía cạnh và đưa ra
      khuyến nghị trade-off cụ thể.
    
    
    2. GIỚI HẠN NGHIÊN CỨU (LIMITATIONS)
    ------------------------------------
    
    Pillar 1 - Phân tích Rủi ro Hợp đồng:
    - Phụ thuộc vào dữ liệu Source Code CÔNG KHAI trên Etherscan
    - Không thể phân tích hợp đồng CHƯA XÁC MINH (unverified contracts)
    - Danh sách hợp đồng đã kiểm toán (known_audited_contracts) cần được cập nhật thủ công
    - Phân tích phụ thuộc dựa trên traces 90 ngày gần nhất, có thể bỏ sót
      các phụ thuộc lâu đời nhưng vẫn còn hoạt động
    
    Pillar 2 - Dự báo Chi phí Gas:
    - ARIMA là mô hình TUYẾN TÍNH, có thể bỏ lỡ các mối quan hệ PHI TUYẾN phức tạp
    - Giới hạn bởi chỉ 30 ngày dữ liệu lịch sử (cân bằng chi phí BigQuery)
    - Rất nhạy cảm với các sự kiện Black Swan (network upgrades, flash crashes)
    - Không tính đến các yếu tố vĩ mô như biến động giá ETH, tâm lý thị trường
    
    Pillar 3 - Phân tích Hành vi Người dùng:
    - Phân tích Sybil dựa trên HEURISTICS (funding source, creation time) và có thể
      bỏ sót các bot tinh vi hơn
    - Cohort analysis chỉ áp dụng được sau khi campaign đã triển khai
    - Peak activity hour chỉ dựa trên 90 ngày gần nhất, có thể không phản ánh
      xu hướng dài hạn
    - Không xem xét các yếu tố ngoài chuỗi (off-chain) như social media sentiment,
      influencer marketing
    
    
    3. HƯỚNG PHÁT TRIỂN TƯƠNG LAI (FUTURE WORK)
    -------------------------------------------
    
    Cải thiện Dự báo Gas (Pillar 2):
    - Tích hợp các mô hình HỌC SÂU (Deep Learning/LSTM) để nắm bắt các mối quan hệ
      phi tuyến phức tạp hơn
    - Sử dụng Ensemble methods kết hợp ARIMA với các mô hình khác (Prophet, XGBoost)
    - Tích hợp dữ liệu từ nhiều nguồn (GasNow, Blocknative, Flashbots) để cải thiện
      độ chính xác
    
    Mở rộng Phân tích Người dùng (Pillar 3):
    - Phân tích hành vi người dùng sang dữ liệu ĐA CHUỖI (multi-chain) 
      (Polygon, BSC, Arbitrum, Optimism, Base, v.v.)
    - Sử dụng Machine Learning nâng cao (Graph Neural Networks) để phát hiện Sybil
      chính xác hơn dựa trên đồ thị giao dịch
    - Tích hợp dữ liệu off-chain (social media, on-chain social graphs như Lens Protocol)
    
    Tự động hóa Trade-off:
    - Phát triển mô hình TỐI ƯU HÓA để tìm điểm cân bằng CHÍNH XÁC giữa chi phí Gas
      và ROI người dùng (ví dụ: Multi-objective Optimization với Pareto Frontier)
    - Tích hợp các yếu tố bổ sung: Chi phí thời gian (opportunity cost), rủi ro thanh khoản,
      tác động môi trường (carbon footprint)
    - Xây dựng hệ thống cảnh báo tự động khi phát hiện Black Swan events
    
    Mở rộng Phân tích Rủi ro (Pillar 1):
    - Tích hợp nhiều công cụ phân tích mã nguồn hơn (Mythril, Manticore, Echidna)
    - Phân tích rủi ro từ hợp đồng proxy và upgradeable contracts
    - Xây dựng cơ sở dữ liệu tự động cập nhật về các hợp đồng đã kiểm toán
    """
    def __init__(self, 
                 risk_analyzer: ContractRiskAnalyzer, 
                 gas_forecaster: GasCostForecaster, 
                 user_analyzer: UserBehaviorAnalyzer):
        self.risk_analyzer = risk_analyzer
        self.gas_forecaster = gas_forecaster
        self.user_analyzer = user_analyzer
        self.results = {}
        self.recommendations = []
        self.visualization_service = VisualizationService()
        self.advanced_viz_service = AdvancedVisualizationService()

    def run_full_analysis(self, contract_address: str, wallet_list: list, campaign_start_date: str, 
                         use_cache: bool = False, save_cache: bool = True):
        """
        Chạy tuần tự cả 3 trụ cột phân tích.
        
        Args:
            contract_address: Địa chỉ hợp đồng cần phân tích
            wallet_list: Danh sách ví để phân tích
            campaign_start_date: Ngày bắt đầu chiến dịch
            use_cache: Nếu True, sẽ đọc từ cache nếu có, không query lại BigQuery
            save_cache: Nếu True, sẽ lưu kết quả vào cache sau khi phân tích
        """
        print(" === BẮT ĐẦU CHẠY FRAMEWORK PHÂN TÍCH TỔNG HỢP === ")
        if use_cache:
            print(" [CACHE MODE] Đang sử dụng dữ liệu từ file cache (tiết kiệm chi phí BigQuery).")
        if save_cache:
            print(" [SAVE MODE] Kết quả sẽ được lưu vào file để phân tích lại sau.")
        
        self.results['pillar1_risk'] = self.risk_analyzer.run(contract_address, use_cache=use_cache, save_cache=save_cache)
        self.results['pillar2_gas'] = self.gas_forecaster.run(forecast_days=7, use_cache=use_cache, save_cache=save_cache)
        self.results['pillar3_user'] = self.user_analyzer.run(wallet_list, campaign_start_date, use_cache=use_cache, save_cache=save_cache)
        print("\n === PHÂN TÍCH TỔNG HỢP HOÀN TẤT === ")

    def generate_strategic_recommendations(self):
        """
        Phần cốt lõi: Tổng hợp kết quả và phân tích "Trade-offs"
        giữa các trụ cột [cite: 196, 258-261].
        """
        print("\n === BÁO CÁO HỖ TRỢ QUYẾT ĐỊNH CHIẾN LƯỢC === ")
        self.recommendations = []
        p1 = self.results['pillar1_risk']
        p2 = self.results['pillar2_gas']
        p3 = self.results['pillar3_user']

        # 1. Phân tích P1: Rủi ro Hợp đồng
        risk_score = p1.get('final_risk_score', 0)
        if risk_score > 0.75:
            rec = (f"[CẢNH BÁO P1 - RỦI RO CAO]: Điểm rủi ro hợp đồng là {risk_score:.2f}. "
                   f"Phát hiện {len(p1.get('dependency_risks', []))} rủi ro phụ thuộc. "
                   "Cân nhắc HỦY BỎ hoặc kiểm toán khẩn cấp trước khi triển khai.")
            self.recommendations.append(rec)
        elif risk_score > 0.4:
            rec = (f"[CẢNH BÁO P1 - RỦI RO TRUNG BÌNH]: Điểm rủi ro là {risk_score:.2f}. "
                   "Tiến hành thận trọng, thông báo rủi ro rõ ràng cho người dùng.")
            self.recommendations.append(rec)
        else:
            rec = f"[OK P1]: Điểm rủi ro hợp đồng thấp ({risk_score:.2f}). An toàn để tiếp tục."
            self.recommendations.append(rec)

        # 2. Phân tích P2: Chi phí Gas
        best_window = p2.get('best_window_start_utc', 'N/A')
        rec = f"[THÔNG TIN P2]: Cửa sổ gas tối ưu (rẻ nhất) trong 7 ngày tới " \
              f"dự kiến bắt đầu lúc {best_window} (UTC)."
        self.recommendations.append(rec)
        
        # Hiển thị độ chính xác mô hình nếu có
        if 'model_accuracy' in p2:
            accuracy = p2['model_accuracy']
            mape = accuracy.get('mape', None)
            r_squared = accuracy.get('r_squared', None)
            reliability_text = ""
            if mape is not None and not np.isnan(mape):
                if mape < 5:
                    reliability_text = "RẤT CAO"
                elif mape < 10:
                    reliability_text = "CAO"
                elif mape < 20:
                    reliability_text = "TRUNG BÌNH"
                else:
                    reliability_text = "THẤP"
                rec_accuracy = (f"[ĐỘ TIN CẬY P2]: Mô hình ARIMA có độ chính xác {reliability_text} "
                              f"(MAPE: {mape:.2f}%, RMSE: {accuracy.get('rmse', 0):.4f} Gwei).")
            elif r_squared is not None and not np.isnan(r_squared):
                rec_accuracy = (f"[ĐỘ TIN CẬY P2]: Mô hình ARIMA có R² = {r_squared:.4f} "
                              f"({r_squared*100:.2f}% phương sai được giải thích).")
            else:
                rec_accuracy = f"[ĐỘ TIN CẬY P2]: Mô hình đã được đánh giá (AIC: {accuracy.get('aic', 'N/A'):.2f}, BIC: {accuracy.get('bic', 'N/A'):.2f})."
            self.recommendations.append(rec_accuracy)

        # 3. Phân tích P3: Hành vi Người dùng
        sybil_clusters = p3.get('sybil_analysis', {}).get('total_clusters', 0)
        cohort_df = p3.get('cohort_analysis', pd.DataFrame())
        if sybil_clusters > 0:
             rec = f"[CẢNH BÁO P3]: Phân tích Sybil phát hiện {sybil_clusters} cụm " \
                   "nghi vấn trong danh sách ví. Cần lọc trước khi airdrop."
             self.recommendations.append(rec)
        if not cohort_df.empty:
             avg_retention_d7 = cohort_df['day_7_retained'].sum() / cohort_df['cohort_size'].sum()
             rec = f"[THÔNG TIN P3]: Tỷ lệ giữ chân trung bình (Day 7) là {avg_retention_d7:.2%}."
             self.recommendations.append(rec)

        # 4. Phân tích TRADE-OFF (Tổng hợp) [cite: 260, 261]
        
        # Trade-off P2 vs P3[cite: 260]:
        # (Giả sử phân tích P3 cho thấy giờ hoạt động tốt nhất là 14:00 UTC)
        try:
            best_gas_hour = pd.to_datetime(best_window).hour
           # Lấy giờ User hoạt động mạnh nhất từ kết quả P3 (thay vì hardcode = 14)
            best_user_hour = p3.get('peak_activity_hour', 14)
            print(f" [INFO] So sánh Trade-off: Gas rẻ nhất {best_gas_hour}h vs User đông nhất {best_user_hour}h")
            if abs(best_gas_hour - best_user_hour) > 4:
                # SỬA ĐỔI: Khuyến nghị theo giờ tối ưu của User (best_user_hour) thay vì 14:00 cố định.
                rec = (f"[TRADE-OFF P2 vs P3]: Cửa sổ gas rẻ nhất (P2) lúc {best_gas_hour}:00 "
                       f"KHÔNG trùng với giờ hoạt động của người dùng chất lượng (P3) (Giá trị P3: {best_user_hour}:00). "
                       f"ĐỀ XUẤT: Chấp nhận chi phí gas cao hơn để triển khai lúc {best_user_hour}:00 "
                       "nhằm tối đa hóa ROI người dùng.")
                self.recommendations.append(rec)
            else:
                # Nếu giờ gas rẻ và giờ user gần nhau -> Tuyệt vời
                rec = (f"[CƠ HỘI VÀNG]: Giờ gas rẻ ({best_gas_hour}h) trùng khớp với giờ người dùng hoạt động mạnh. "
                       "Đây là thời điểm triển khai hoàn hảo!")
                self.recommendations.append(rec)
        except Exception as e:
            print(f" [Lỗi logic Trade-off]: {e}")

        # In tất cả khuyến nghị
        for r in self.recommendations:
            print(f" {r}\n")
            
        return self.recommendations
    
    def visualize_results(self, contract_address: str, campaign_start_date: str, save: bool = True) -> dict:
        """
        Visualize tất cả kết quả phân tích từ 3 Pillar.
        
        Args:
            contract_address: Địa chỉ hợp đồng
            campaign_start_date: Ngày bắt đầu chiến dịch
            save: Có lưu file không
            
        Returns:
            Dictionary chứa đường dẫn các file hình ảnh đã tạo
        """
        print("\n=== TẠO BIỂU ĐỒ VISUALIZATION ===")
        
        visualization_paths = {}
        
        # Visualize từng Pillar
        if 'pillar1_risk' in self.results:
            path = self.visualization_service.visualize_pillar1_risk(
                self.results['pillar1_risk'], contract_address, save=save
            )
            visualization_paths['pillar1'] = path
        
        if 'pillar2_gas' in self.results:
            path = self.visualization_service.visualize_pillar2_gas(
                self.results['pillar2_gas'], save=save
            )
            visualization_paths['pillar2'] = path
        
        if 'pillar3_user' in self.results:
            path = self.visualization_service.visualize_pillar3_user(
                self.results['pillar3_user'], campaign_start_date, save=save
            )
            visualization_paths['pillar3'] = path
        
        print("=== HOÀN TẤT VISUALIZATION ===\n")
        return visualization_paths
    
    def compare_with_previous(self, previous_results: dict, save: bool = True) -> str:
        """
        So sánh kết quả hiện tại với kết quả trước đó.
        
        Args:
            previous_results: Dictionary chứa kết quả phân tích trước đó
            save: Có lưu file không
            
        Returns:
            Đường dẫn file comparison đã tạo
        """
        print("\n=== TẠO BIỂU ĐỒ SO SÁNH TRƯỚC/SAU ===")
        
        path = self.visualization_service.compare_before_after(
            previous_results, self.results, save=save
        )
        
        print("=== HOÀN TẤT COMPARISON ===\n")
        return path
    
    def create_executive_dashboard(self, contract_address: str, campaign_start_date: str, save: bool = True) -> str:
        """
        Tạo Executive Dashboard - Tổng hợp tất cả insights chuyên nghiệp.
        Đây là biểu đồ quan trọng nhất cho stakeholders và decision-makers.
        
        Args:
            contract_address: Địa chỉ hợp đồng
            campaign_start_date: Ngày bắt đầu chiến dịch
            save: Có lưu file không
            
        Returns:
            Đường dẫn file dashboard đã tạo
        """
        print("\n=== TẠO EXECUTIVE DASHBOARD ===")
        path = self.advanced_viz_service.create_executive_dashboard(
            self.results, contract_address, campaign_start_date, save=save
        )
        print("=== HOÀN TẤT EXECUTIVE DASHBOARD ===\n")
        return path
    
    def create_advanced_visualizations(self, contract_address: str, save: bool = True) -> Dict:
        """
        Tạo tất cả các advanced visualizations.
        
        Args:
            contract_address: Địa chỉ hợp đồng
            save: Có lưu file không
            
        Returns:
            Dictionary chứa đường dẫn các file đã tạo
        """
        print("\n=== TẠO ADVANCED VISUALIZATIONS ===")
        
        paths = {}
        
        # Trade-off Analysis
        paths['tradeoff'] = self.advanced_viz_service.create_tradeoff_analysis(
            self.results, save=save
        )
        
        # Risk Heatmap
        if 'pillar1_risk' in self.results:
            paths['risk_heatmap'] = self.advanced_viz_service.create_risk_heatmap(
                self.results['pillar1_risk'], contract_address, save=save
            )
        
        print("=== HOÀN TẤT ADVANCED VISUALIZATIONS ===\n")
        return paths