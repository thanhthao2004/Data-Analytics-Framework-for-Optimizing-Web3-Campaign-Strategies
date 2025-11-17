# Tích hợp 3 trụ cột, thực hiện logic "trade-off"
from analysis.pillar1_risk_model import ContractRiskAnalyzer
from analysis.pillar2_gas_model import GasCostForecaster
from analysis.pillar3_user_model import UserBehaviorAnalyzer
import pandas as pd
class AnalysisService:
    """
    Dịch vụ Tích hợp Framework.
    Lớp "nhạc trưởng" này chạy cả 3 trụ cột và thực hiện 
    phân tích "trade-off" để đưa ra khuyến nghị chiến lược[cite: 196].
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

    def run_full_analysis(self, contract_address: str, wallet_list: list, campaign_start_date: str):
        """
        Chạy tuần tự cả 3 trụ cột phân tích.
        """
        print(" === BẮT ĐẦU CHẠY FRAMEWORK PHÂN TÍCH TỔNG HỢP === ")
        self.results['pillar1_risk'] = self.risk_analyzer.run(contract_address)
        self.results['pillar2_gas'] = self.gas_forecaster.run(forecast_days=7)
        self.results['pillar3_user'] = self.user_analyzer.run(wallet_list, campaign_start_date)
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
                rec = (f"[TRADE-OFF P2 vs P3]: Cửa sổ gas rẻ nhất (P2) lúc {best_gas_hour}:00 "
                       f"KHÔNG trùng với giờ hoạt động của người dùng chất lượng (P3) (Giả định {best_user_hour}:00). "
                       "ĐỀ XUẤT: Chấp nhận chi phí gas cao hơn để triển khai lúc 14:00 "
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