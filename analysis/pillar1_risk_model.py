# analysis/pillar1_risk_model.py
import networkx as nx
import subprocess
import json
import os
import tempfile
import shutil
from etherscan.client import Client
from core.config import Config
from connectors.db_connector import BigQueryConnector
import pandas as pd

class ContractRiskAnalyzer:
    """
    Triển khai Trụ cột 1 (Open-Source).
    Sử dụng Slither (Phân tích nội bộ) và BigQuery (Phân tích phụ thuộc).
    """
    def __init__(self, db: BigQueryConnector):
        self.db = db
        self.api_key = Config.ETHERSCAN_API_KEY
        self.known_audited_contracts = self._load_known_audits()
        print("[Pillar 1] Đã khởi tạo ContractRiskAnalyzer.")

    def _load_known_audits(self) -> set:
        """
        Tải danh sách các hợp đồng đã được kiểm toán (audited) đã biết.
        (Đây là hàm giả lập, bạn có thể thay thế bằng việc đọc từ file CSV/JSON)
        """
        print("[Pillar 1] Đang tải danh sách hợp đồng đã kiểm toán...")
        return {
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48".lower(), # USDC 
            "0xdac17f958d2ee523a2206206994597c13d831ec7".lower()  # Tether (USDT)
        }

    def _get_internal_risk(self, contract_address: str) -> dict:
        """
        Thực hiện Model 1: Traditional Security Analysis bằng Slither (Open-Source).
        Khớp với luồng: get_verified_source -> Run Slither -> Parse slither_results.json
        """
        print(f"[Pillar 1-OS] Đang lấy mã nguồn cho {contract_address}...")
        try:
            client = Client(address=contract_address, api_key=self.api_key)
            source_data = client.get_source_code()
            if not source_data or not source_data[0].get('SourceCode'):
                print(f"[Pillar 1-OS] Không tìm thấy mã nguồn đã xác thực.")
                return {"score": 50, "issues_found": ["No verified source code"]}
            
            source_code = source_data[0]['SourceCode']
            contract_name = source_data[0]['ContractName']

            if source_code.startswith('{{'):
                 source_code_json = json.loads(source_code[1:-1])
                 files_to_write = source_code_json.get('sources', {})
            elif source_code.startswith('{'):
                 source_code_json = json.loads(source_code)
                 files_to_write = source_code_json
            else:
                 files_to_write = {f"{contract_name}.sol": {"content": source_code}}

        except Exception as e:
            print(f" [Pillar 1-OS] Lỗi khi lấy/xử lý mã nguồn Etherscan: {e}")
            return {"score": 50, "issues_found": [f"Source fetch error: {e}"]}

        temp_dir = tempfile.mkdtemp()
        print(f" [Pillar 1-OS] Đã tạo thư mục tạm: {temp_dir}")
        try:
            for file_name, data in files_to_write.items():
                file_path = os.path.join(temp_dir, file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(data['content'])

            json_output_file = os.path.join(temp_dir, 'slither_results.json')
            print(f" [Pillar 1-OS] Đang chạy Slither...")
            
            command = ['slither', temp_dir, '--json', json_output_file]
            process = subprocess.run(command, capture_output=True, text=True, timeout=120)

            if process.returncode != 0 and not os.path.exists(json_output_file):
                print(f" [Pillar 1-OS] Slither thất bại. Lỗi:\n{process.stderr}")
                return {"score": 50, "issues_found": ["Slither execution failed", process.stderr[:200]]}

            # Xử lý trường hợp Slither không tìm thấy file json nhưng vẫn thoát code 0
            if not os.path.exists(json_output_file):
                print(f" [Pillar 1-OS] Slither chạy nhưng không tạo file JSON. Output:\n{process.stdout}")
                return {"score": 50, "issues_found": ["Slither JSON output not found"]}

            with open(json_output_file, 'r') as f:
                results = json.load(f)

            if results.get('success', False) and 'results' in results:
                issues = results['results'].get('detectors', [])
                print(f" [Pillar 1-OS] Slither hoàn tất. Phát hiện {len(issues)} vấn đề.")
                
                # Tính điểm theo sơ đồ: 100 - (số vấn đề * 5)
                score = max(0, 100 - (len(issues) * 5)) 
                return {"score": score, "issues_found": [i['description'] for i in issues]}
            else:
                print(f" [Pillar 1-OS] Slither chạy nhưng kết quả JSON không hợp lệ. Lỗi: {results.get('error')}")
                return {"score": 50, "issues_found": ["Slither JSON error", results.get('error')]}

        except Exception as e:
            print(f" [Pillar 1-OS] Lỗi trong quá trình chạy Slither: {e}")
            return {"score": 50, "issues_found": [f"Slither runtime error: {e}"]}
        
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f" [Pillar 1-OS] Đã dọn dẹp thư mục tạm.")

    def _get_dependency_graph(self, contract_address: str) -> nx.DiGraph:
        """
        Xây dựng đồ thị phụ thuộc (Dependency Graph).
        Khớp với luồng: get_dependency_graph() -> Query traces -> build nx.DiGraph()
        """
        print(f"[Pillar 1] Đang xây dựng đồ thị phụ thuộc cho {contract_address}...")
        G = nx.DiGraph()
        G.add_node(contract_address, audited=(contract_address in self.known_audited_contracts))
        
        # *** THAY ĐỔI QUAN TRỌNG: Thêm bộ lọc 90 ngày để tránh quét toàn bộ bảng ***
        query = f"""
            SELECT 
                to_address
            FROM `bigquery-public-data.crypto_ethereum.traces`
            WHERE from_address = '{contract_address.lower()}'
              AND (call_type = 'delegatecall' OR call_type = 'call')
              AND to_address != '{contract_address.lower()}'
              -- TỐI ƯU HÓA CHI PHÍ BIGQUERY: Chỉ quét 90 ngày gần nhất
              AND DATE(block_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            GROUP BY 1
            LIMIT 30 -- Giới hạn để tránh quá tải
        """
        try:
            df = self.db.query_to_dataframe(query)
            if df.empty:
                print("[Pillar 1] Không tìm thấy phụ thuộc (traces) nào trong 90 ngày gần nhất.")
                return G
            
            for _, row in df.iterrows():
                dep_address = row['to_address'].lower()
                is_audited = (dep_address in self.known_audi