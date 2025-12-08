# Tải API keys, DB credentials, contract addresses
# core/config.py
# Tải API keys, DB credentials, contract addresses
import os
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env ở thư mục gốc
load_dotenv()

class Config:
    """
    Lớp Cấu hình (Config) để chứa tất cả các biến môi trường
    và các thiết lập của dự án.
    """
    
    # === CẤU HÌNH KẾT NỐI ===
    ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY")
    
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_PATH")
    
    # === CẤU HÌNH CHIẾN DỊCH ===
    
    # Địa chỉ hợp đồng mục tiêu mà chiến dịch sẽ tương tác
    # [Pillar 1] Đây là đối tượng phân tích rủi ro chính
    # UPDATED: Chuyển sang UNI (Uniswap) - hợp đồng verified, đơn giản hơn USDT
    # Contract info: https://etherscan.io/address/0x1f9840a85d5af5bf1d1762f925bdaddc4201f984
    TARGET_CONTRACT_ADDRESS = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"  # Uniswap UNI Token
    
    # Danh sách các ví tiềm năng để phân tích Sybil (nếu có)
    # [Pillar 3] Dùng cho phân tích chủ động (proactive)
    POTENTIAL_WALLET_LIST_PATH = "data/potential_wallets.csv"
    
    # Ngày bắt đầu chiến dịch (dùng cho phân tích cohort)
    # [Pillar 3]
    CAMPAIGN_START_DATE = "2025-6-23"
