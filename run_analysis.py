# run_analysis.py
# Script chính để chạy toàn bộ phân tích
import pandas as pd
from core.config import Config
from connectors.db_connector import BigQueryConnector
from connectors.security_api_client import SecurityAPIClient
from analysis.pillar1_risk_model import ContractRiskAnalyzer
from analysis.pillar2_gas_model import GasCostForecaster
from analysis.pillar3_user_model import UserBehaviorAnalyzer
from analysis.analysis_service import AnalysisService

def load_wallet_list(path: str) -> list:
    """Tiện ích tải danh sách ví từ CSV."""
    try:
        df = pd.read_csv(path)
        # Giả sử cột chứa ví có tên là 'wallet_address'
        if 'wallet_address' in df.columns:
            return df['wallet_address'].tolist()
        return []
    except FileNotFoundError:
        print(f" Không tìm thấy tệp danh sách ví tại: {path}")
        return []

def main():
    """
    Entry point chính của Framework Phân tích.
    """
    print("=======================================================")
    print(" Khởi tạo Framework Phân tích Chiến dịch Web3")
    print("=======================================================")

    # 1. Khởi tạo các Connectors
    db_conn = BigQueryConnector()
    api_client = ContractRiskAnalyzer().etherscan
    
    # Kiểm tra kết nối
    if not db_conn.client:
        print(" Hủy bỏ: Không thể kết nối tới BigQuery. Vui lòng kiểm tra credentials.")
        return

    # 2. Khởi tạo các Trụ cột (Pillars)
    # Các trụ cột nhận connectors làm tham số (Dependency Injection)
    risk_analyzer = ContractRiskAnalyzer(db=db_conn, api=api_client)
    gas_forecaster = GasCostForecaster(db=db_conn)
    user_analyzer = UserBehaviorAnalyzer(db=db_conn)

    # 3. Khởi tạo Dịch vụ Tích hợp (Analysis Service)
    # Service nhận các trụ cột làm tham số
    analysis_service = AnalysisService(
        risk_analyzer=risk_analyzer,
        gas_forecaster=gas_forecaster,
        user_analyzer=user_analyzer
    )

    # 4. Tải dữ liệu đầu vào
    target_contract = Config.TARGET_CONTRACT_ADDRESS
    wallet_list = load_wallet_list(Config.POTENTIAL_WALLET_LIST_PATH)
    start_date = Config.CAMPAIGN_START_DATE

    # 5. Chạy phân tích tổng hợp
    analysis_service.run_full_analysis(
        contract_address=target_contract,
        wallet_list=wallet_list,
        campaign_start_date=start_date
    )

    # 6. Lấy các khuyến nghị chiến lược
    analysis_service.generate_strategic_recommendations()
    
    print("\n=======================================================")
    print(" Phân tích hoàn tất.")
    print("=======================================================")


if __name__ == "__main__":
    # Để chạy, hãy đảm bảo bạn đã tạo file .env
    # và cài đặt các thư viện trong requirements.txt
    main()