# analysis/pillar1_risk_model.py
# Pillar 1: Contract Risk
import networkx as nx
from connectors.db_connector import BigQueryConnector
from connectors.security_api_client import SecurityAPIClient

class ContractRiskAnalyzer:
    """
    Triển khai Trụ cột 1: Phân tích Rủi ro Hợp đồng.
    Kết hợp "Traditional Analysis" (qua API) và "Dependency Risk Analysis"
    (qua BigQuery & networkx) như mô tả trong Hình 1 [cite: 210-212].
    """
    def __init__(self, db: BigQueryConnector, api: SecurityAPIClient):
        self.db = db
        self.api = api
        # Tải danh sách các hợp đồng đã được audit (ví dụ)
        self.known_audited_contracts = self._load_known_audits()

    def _get_internal_risk(self, contract_address: str) -> dict:
        """
        Thực hiện Model 1: Traditional Security Analysis[cite: 211].
        Lấy điểm rủi ro nội bộ (reentrancy, etc.) từ API.
        """
        return self.api.get_contract_internal_risk(contract_address, chain_id="1")

    def _get_dependency_graph(self, contract_address: str) -> nx.DiGraph:
        """
        Thực hiện Model 2: Dependency Risk Analysis[cite: 212].
        Xây dựng đồ thị phụ thuộc bằng cách truy vấn 'traces'
        để tìm 'external calls' và 'delegate calls'[cite: 208].
        """
        print(f"[Pillar 1] Đang xây dựng đồ thị phụ thuộc cho {contract_address}...")
        G = nx.DiGraph()
        
        # Truy vấn BigQuery để tìm các tương tác liên-hợp đồng
        query = f"""
            SELECT
                to_address,
                call_type,
                COUNT(*) AS interaction_count
            FROM `bigquery-public-data.crypto_ethereum.traces`
            WHERE from_address = '{contract_address.lower()}'
              AND call_type IN ('call', 'delegatecall', 'staticcall')
              AND status = 1 -- Chỉ các cuộc gọi thành công
              AND to_address IS NOT NULL
              AND to_address != '{contract_address.lower()}'
            GROUP BY 1, 2
            LIMIT 100 -- Giới hạn để tránh quá tải
        """
        dependencies_df = self.db.query_to_dataframe(query)
        
        if dependencies_df.empty:
            print("ℹ[Pillar 1] Hợp đồng không có tương tác bên ngoài rõ ràng.")
            return G

        # Thêm các cạnh vào đồ thị
        for _, row in dependencies_df.iterrows():
            G.add_edge(
                contract_address.lower(),
                row['to_address'],
                type=row['call_type'],
                weight=row['interaction_count']
            )
        
        print(f"[Pillar 1] Xây dựng đồ thị hoàn tất: {G.number_of_nodes()} nút, {G.number_of_edges()} cạnh.")
        return G

    def _analyze_hidden_risks(self, graph: nx.DiGraph) -> list:
        """
        Phân tích đồ thị để tìm "Hidden Risk"[cite: 212].
        Kiểm tra xem có phụ thuộc nào (nút) không nằm trong danh sách đã audit.
        """
        hidden_risks = []
        for node in graph.nodes():
            if node not in self.known_audited_contracts:
                risk_detail = f"Phụ thuộc vào hợp đồng chưa được xác minh/audit: {node}"
                hidden_risks.append(risk_detail)
        
        if hidden_risks:
            print(f"[Pillar 1] Phát hiện {len(hidden_risks)} rủi ro phụ thuộc tiềm ẩn!")
        return hidden_risks

    def _load_known_audits(self):
        # Trong thực tế, đây là một CSDL nội bộ
        return {
            "0xExampleContractAddress...".lower(), # Hợp đồng của chúng ta
            "0xpriceoracle.eth".lower(), # Giả sử đây là một oracle đã audit
            "0xsomeknownlibrary.eth".lower()
        }

    def run(self, contract_address: str) -> dict:
        """
        Chạy phân tích Pillar 1 đầy đủ.
        """
        print("\n--- Bắt đầu Phân tích Pillar 1: Rủi ro Hợp đồng ---")
        
        # 1. Phân tích Nội bộ
        internal_risk = self._get_internal_risk(contract_address)
        
        # 2. Phân tích Phụ thuộc
        dependency_graph = self._get_dependency_graph(contract_address)
        hidden_risks = self._analyze_hidden_risks(dependency_graph)
        
        # 3. Tính điểm cuối cùng
        # (Logic tính điểm ví dụ: Rủi ro phụ thuộc có trọng số cao hơn)
        internal_score = internal_risk.get('score', 50) / 100.0 # Chuẩn hóa về 0-1
        dependency_risk_count = len(hidden_risks)
        
        # Điểm cuối cùng (0 là rủi ro thấp, 1 là rủi ro cao)
        final_risk_score = (internal_score * 0.4) + (min(dependency_risk_count, 5) / 5.0 * 0.6)
        
        print(f"[Pillar 1] Hoàn tất. Điểm rủi ro cuối cùng: {final_risk_score:.2f}")
        
        return {
            "final_risk_score": final_risk_score,
            "internal_risk": internal_risk,
            "dependency_risks": hidden_risks
        }