# run_analysis.py
# Script chính để chạy toàn bộ phân tích (ĐÃ SỬA LỖI)
import pandas as pd
import argparse
from core.config import Config
from connectors.db_connector import BigQueryConnector
# import connectors.security_api_client (ĐÃ XÓA - Không cần thiết)
from analysis.pillar1_risk_model import ContractRiskAnalyzer
from analysis.pillar2_gas_model import GasCostForecaster
from analysis.pillar3_user_model import UserBehaviorAnalyzer
from analysis.analysis_service import AnalysisService

def load_wallet_list(path: str) -> list:
    """Tiện ích tải danh sách ví từ CSV."""
    try:
        df = pd.read_csv(path)
        if 'wallet_address' in df.columns:
            return df['wallet_address'].tolist()
        print(f" Không tìm thấy cột 'wallet_address' trong {path}")
        return []
    except FileNotFoundError:
        print(f" Không tìm thấy tệp danh sách ví tại: {path}")
        return []

def main():
    """
    Entry point chính của Framework Phân tích.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Framework Phân tích Chiến dịch Web3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Chạy phân tích bình thường (query BigQuery và lưu cache)
  python run_analysis.py

  # Chỉ sử dụng dữ liệu từ cache (không query BigQuery)
  python run_analysis.py --use-cache

  # Query BigQuery nhưng không lưu cache
  python run_analysis.py --no-save-cache

  # Chỉ dùng cache, không lưu gì mới
  python run_analysis.py --use-cache --no-save-cache
        """
    )
    parser.add_argument('--use-cache', action='store_true',
                        help='Sử dụng dữ liệu từ cache nếu có (tiết kiệm chi phí BigQuery)')
    parser.add_argument('--no-save-cache', action='store_true',
                        help='Không lưu kết quả vào cache')
    
    args = parser.parse_args()
    
    use_cache = args.use_cache
    save_cache = not args.no_save_cache
    
    print("=======================================================")
    print(" Khởi tạo Framework Phân tích Chiến dịch Web3")
    print("=======================================================")
    if use_cache:
        print(" [MODE] Sử dụng cache: ON (không query BigQuery)")
    if not save_cache:
        print(" [MODE] Lưu cache: OFF")

    # 1. Khởi tạo các Connectors
    # Nếu dùng cache, có thể không cần kết nối BigQuery
    db_conn = None
    if not use_cache:
        db_conn = BigQueryConnector()
        if not db_conn.client:
            print(" ⚠️  Cảnh báo: Không thể kết nối tới BigQuery.")
            print("    Nếu dùng --use-cache, bạn có thể bỏ qua cảnh báo này.")
            if not use_cache:
                print(" Hủy bỏ: Không thể kết nối tới BigQuery. Vui lòng kiểm tra credentials.")
                return
    else:
        # Tạo mock connector nếu chỉ dùng cache
        print(" [INFO] Bỏ qua kết nối BigQuery (đang dùng cache).")
        from unittest.mock import MagicMock
        db_conn = MagicMock()
        db_conn.client = None

    # 2. Khởi tạo các Trụ cột (Pillars)
    risk_analyzer = ContractRiskAnalyzer(db=db_conn) if db_conn else None
    gas_forecaster = GasCostForecaster(db=db_conn) if db_conn else None
    user_analyzer = UserBehaviorAnalyzer(db=db_conn) if db_conn else None
    
    # Nếu dùng cache, các analyzer có thể None, nhưng chúng sẽ tự xử lý
    if use_cache and (risk_analyzer is None or gas_forecaster is None or user_analyzer is None):
        # Tạo các analyzer với mock db cho cache mode
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        risk_analyzer = ContractRiskAnalyzer(db=mock_db)
        gas_forecaster = GasCostForecaster(db=mock_db)
        user_analyzer = UserBehaviorAnalyzer(db=mock_db)

    # 3. Khởi tạo Dịch vụ Tích hợp (Analysis Service)
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
        campaign_start_date=start_date,
        use_cache=use_cache,
        save_cache=save_cache
    )

    # 6. Lấy các khuyến nghị chiến lược
    analysis_service.generate_strategic_recommendations()
    
    # 7. Tạo visualizations
    print("\n--- Tạo Visualizations ---")
    try:
        # Standard visualizations
        viz_paths = analysis_service.visualize_results(
            contract_address=target_contract,
            campaign_start_date=start_date,
            save=True
        )
        
        # Executive Dashboard (quan trọng nhất)
        dashboard_path = analysis_service.create_executive_dashboard(
            contract_address=target_contract,
            campaign_start_date=start_date,
            save=True
        )
        print(f" Executive Dashboard: {dashboard_path}")
        
        # Advanced visualizations
        advanced_paths = analysis_service.create_advanced_visualizations(
            contract_address=target_contract,
            save=True
        )
        
    except Exception as e:
        print(f"  Lỗi khi tạo visualizations: {e}")
        print("    Bạn vẫn có thể xem kết quả text-based ở trên.")
    
    print("\n=======================================================")
    print(" Phân tích hoàn tất.")
    if save_cache:
        print(" Kết quả đã được lưu vào thư mục data/ để phân tích lại sau.")
    print(" Visualizations đã được lưu vào data/visualizations/")
    print("=======================================================")


if __name__ == "__main__":
    main()