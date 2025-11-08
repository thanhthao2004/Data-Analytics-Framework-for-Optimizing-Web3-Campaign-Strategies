# connectors/security_api_client.py
# Class để gọi API bảo mật (GoPlus, Chainalysis...)
import requests
from core.config import Config

class SecurityAPIClient:
    """
    Lớp client để tương tác với API bảo mật bên thứ ba (ví dụ: GoPlus)
    để lấy điểm rủi ro hợp đồng (Pillar 1).
    """
    def __init__(self):
        self.api_key = Config.SECURITY_API_KEY
        self.base_url = Config.SECURITY_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def get_contract_internal_risk(self, contract_address: str, chain_id: str = "1") -> dict:
        """
        Lấy điểm rủi ro nội bộ (traditional analysis) cho một hợp đồng.
        [cite: 201, 202]
        """
        print(f"[SecurityAPI] Đang lấy điểm rủi ro nội bộ cho {contract_address}...")
        
        # Đây là một ví dụ, endpoint thực tế sẽ khác
        endpoint = f"{self.base_url}/contract_security/{contract_address}?chain_id={chain_id}"
        
        try:
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status() # Báo lỗi nếu status code là 4xx/5xx
            
            data = response.json()
            print("[SecurityAPI] Lấy điểm rủi ro thành công.")
            # Trả về một phần của kết quả JSON
            return {
                "score": data.get("result", {}).get("security_score", 50), # Giả lập
                "issues_found": data.get("result", {}).get("issues", []),
            }
        except requests.exceptions.RequestException as e:
            print(f"[SecurityAPI] Lỗi gọi API: {e}")
            return {"score": 50, "issues_found": ["API Error"]} # Trả về mặc định an toàn