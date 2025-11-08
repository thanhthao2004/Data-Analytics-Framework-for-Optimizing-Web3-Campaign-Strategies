# analysis/pillar1_risk_model.py (ĐƯỢC THIẾT KẾ LẠI)
# Pillar 1: Contract Risk
import networkx as nx
import subprocess  # <--- THÊM VÀO
import json        # <--- THÊM VÀO
import os          # <--- THÊM VÀO
import tempfile    # <--- THÊM VÀO
import shutil      # <--- THÊM VÀO
from etherscan import Etherscan # <--- THÊM VÀO
from core.config import Config
from connectors.db_connector import BigQueryConnector
# (Chúng ta không import SecurityAPIClient nữa)

class ContractRiskAnalyzer:
    """
    Triển khai Trụ cột 1 (Open-Source).
    Sử dụng Slither (Phân tích nội bộ) và BigQuery/NetworkX (Phân tích phụ thuộc).
    """
    def __init__(self, db: BigQueryConnector):
        self.db = db
        # Khởi tạo API Etherscan để lấy mã nguồn
        self.etherscan = Etherscan(Config.ETHERSCAN_API_KEY)
        self.known_audited_contracts = self._load_known_audits()

    def _get_internal_risk(self, contract_address: str) -> dict:
        """
        Thực hiện Model 1: Traditional Security Analysis bằng Slither (Open-Source).
        Quy trình:
        1. Lấy mã nguồn từ Etherscan.
        2. Lưu vào thư mục tạm.
        3. Chạy Slither trên thư mục đó.
        4. Đọc và phân tích kết quả JSON.
        5. Dọn dẹp thư mục tạm.
        """
        print(f"[Pillar 1-OS] Đang lấy mã nguồn cho {contract_address}...")
        try:
            source_data = self.etherscan.get_contract_source_code(contract_address)
            if not source_data or not source_data[0].get('SourceCode'):
                print(f"[Pillar 1-OS] Không tìm thấy mã nguồn đã xác thực.")
                return {"score": 50, "issues_found": ["No verified source code"]}
            
            # Etherscan trả về một chuỗi JSON hoặc mã nguồn
            source_code = source_data[0]['SourceCode']
            contract_name = source_data[0]['ContractName']

            # Xử lý mã nguồn (thường là một chuỗi JSON chứa nhiều tệp)
            if source_code.startswith('{{'): # Định dạng JSON của Etherscan
                 source_code_json = json.loads(source_code[1:-1])
                 files_to_write = source_code_json.get('sources', {})
            elif source_code.startswith('{'): # Định dạng JSON cũ hơn
                 source_code_json = json.loads(source_code)
                 files_to_write = source_code_json
            else: # Mã nguồn đơn
                 files_to_write = {f"{contract_name}.sol": {"content": source_code}}

        except Exception as e:
            print(f" [Pillar 1-OS] Lỗi khi lấy/xử lý mã nguồn Etherscan: {e}")
            return {"score": 50, "issues_found": [f"Source fetch error: {e}"]}

        # 2. Lưu vào thư mục tạm
        temp_dir = tempfile.mkdtemp()
        print(f" [Pillar 1-OS] Đã tạo thư mục tạm: {temp_dir}")
        try:
            for file_name, data in files_to_write.items():
                file_path = os.path.join(temp_dir, file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(data['content'])

            # 3. Chạy Slither trên thư mục đó
            json_output_file = os.path.join(temp_dir, 'slither_results.json')
            print(f" [Pillar 1-OS] Đang chạy Slither...")
            
            # Chạy Slither qua subprocess, trỏ vào thư mục tạm
            # --json: Xuất kết quả ra file JSON
            command = ['slither', temp_dir, '--json', json_output_file]
            
            # Ẩn output thông thường, chỉ báo lỗi nếu có
            process = subprocess.run(command, capture_output=True, text=True, timeout=120)

            if process.returncode != 0 and not os.path.exists(json_output_file):
                 # Nếu Slither thất bại VÀ không tạo ra file JSON
                print(f" [Pillar 1-OS] Slither thất bại. Lỗi:\n{process.stderr}")
                return {"score": 50, "issues_found": ["Slither execution failed", process.stderr[:200]]}

            # 4. Đọc và phân tích kết quả JSON
            with open(json_output_file, 'r') as f:
                results = json.load(f)

            if results.get('success', False) and 'results' in results:
                issues = results['results'].get('detectors', [])
                print(f" [Pillar 1-OS] Slither hoàn tất. Phát hiện {len(issues)} vấn đề.")
                
                # Tính điểm đơn giản: 100 - (số vấn đề * 5)
                # (Bạn có thể tinh chỉnh logic này dựa trên 'impact' (mức độ ảnh hưởng))
                score = max(0, 100 - (len(issues) * 5)) 
                return {"score": score, "issues_found": [i['description'] for i in issues]}
            else:
                print(f" [Pillar 1-OS] Slither chạy nhưng kết quả JSON không hợp lệ. Lỗi: {results.get('error')}")
                return {"score": 50, "issues_found": ["Slither JSON error", results.get('error')]}

        except Exception as e:
            print(f" [Pillar 1-OS] Lỗi trong quá trình chạy Slither: {e}")
            return {"score": 50, "issues_found": [f"Slither runtime error: {e}"]}
        
        finally:
            # 5. Dọn dẹp thư mục tạm
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f" [Pillar 1-OS] Đã dọn dẹp thư mục tạm.")

    # ... (Các hàm _get_dependency_graph, _analyze_hidden_risks, _load_known_audits vẫn giữ nguyên) ...
    # ...
    
    def run(self, contract_address: str) -> dict:
        """
        Chạy phân tích Pillar 1 đầy đủ (Phiên bản Open-Source).
        """
        print("\n--- Bắt đầu Phân tích Pillar 1: Rủi ro Hợp đồng ---")
        
        # 1. Phân tích Nội bộ (Đã được thiết kế lại)
        internal_risk = self._get_internal_risk(contract_address)
        
        # 2. Phân tích Phụ thuộc (Giữ nguyên)
        dependency_graph = self._get_dependency_graph(contract_address)
        hidden_risks = self._analyze_hidden_risks(dependency_graph)
        
        # 3. Tính điểm cuối cùng
        internal_score = internal_risk.get('score', 50) / 100.0 # Chuẩn hóa về 0-1
        dependency_risk_count = len(hidden_risks)
        
        final_risk_score = (internal_score * 0.4) + (min(dependency_risk_count, 5) / 5.0 * 0.6)
        
        print(f" [Pillar 1] Hoàn tất. Điểm rủi ro cuối cùng: {final_risk_score:.2f}")
        
        return {
            "final_risk_score": final_risk_score,
            "internal_risk": internal_risk,
            "dependency_risks": hidden_risks
        }