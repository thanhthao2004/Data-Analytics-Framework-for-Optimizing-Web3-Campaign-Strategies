# analysis/pillar3_user_model.py
import pandas as pd
from connectors.db_connector import BigQueryConnector
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from core.config import Config

class UserBehaviorAnalyzer:
    """
    Triển khai Trụ cột 3: Phân tích Hành vi Người dùng.
    Khớp với sơ đồ Mermaid P3.
    """
    def __init__(self, db: BigQueryConnector):
        self.db = db

    def _get_sybil_features(self, wallet_list: list) -> pd.DataFrame:
        """
        Lấy các đặc điểm (features) từ BigQuery để phân cụm Sybil.
        Khớp với luồng: _get_sybil_features() -> BigQuery SQL
        """
        # *** THAY ĐỔI QUAN TRỌNG: Thêm check nếu list rỗng thì không chạy ***
        if not wallet_list:
            print("[Pillar 3] Danh sách ví rỗng. Bỏ qua phân tích Sybil.")
            return pd.DataFrame()
            
        print(f"[Pillar 3] Đang lấy đặc điểm Sybil cho {len(wallet_list)} ví...")
        
        wallet_list_str = "('" + "','".join([w.lower() for w in wallet_list]) + "')"

        # *** THAY ĐỔI QUAN TRỌNG: Thêm bộ lọc 365 ngày để tránh quét toàn bộ bảng ***
        query = f"""
            WITH ranked_tx AS (
                SELECT 
                    from_address, 
                    to_address,
                    block_timestamp,
                    ROW_NUMBER() OVER(PARTITION BY to_address ORDER BY block_timestamp ASC) as rn
                FROM `bigquery-public-data.crypto_ethereum.transactions`
                WHERE to_address IN {wallet_list_str}
                -- TỐI ƯU HÓA CHI PHÍ: Giả định ví phân tích được tạo trong 365 ngày
                AND DATE(block_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
            )
            SELECT 
                to_address AS wallet,
                from_address AS funding_source,
                UNIX_SECONDS(block_timestamp) AS creation_timestamp
            FROM ranked_tx
            WHERE rn = 1
        """
        features_df = self.db.query_to_dataframe(query)
        if features_df.empty:
            print("ℹ[Pillar 3] Không tìm thấy dữ liệu giao dịch cho các ví này (trong 365 ngày).")
            return pd.DataFrame()
            
        # Khớp với luồng: Encode funding_source -> funding_source_id
        features_df['funding_source_id'] = features_df['funding_source'].astype('category').cat.codes
        
        return features_df

    def detect_sybil_clusters(self, wallet_list: list) -> dict:
        """
        Chạy thuật toán phân cụm (DBSCAN) để tìm các cụm Sybil.
        Khớp với luồng: StandardScaler -> DBSCAN
        """
        features_df = self._get_sybil_features(wallet_list)
        if features_df.empty:
            return {"total_clusters": 0, "clusters": {}}

        X = features_df[['funding_source_id', 'creation_timestamp']]
        
        # Khớp với luồng: StandardScaler().fit_transform()
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Khớp với luồng: DBSCAN(eps=0.5, min_samples=3)
        dynamic_min_samples = 2 if len(wallet_list) < 3 else 3
        print(f"[Pillar 3] Chạy DBSCAN với eps=0.5, min_samples={dynamic_min_samples}")
        dbscan = DBSCAN(eps=0.5, min_samples=dynamic_min_samples)
        clusters = dbscan.fit_predict(X_scaled)
        
        features_df['cluster'] = clusters
        
        sybil_df = features_df[features_df['cluster'] != -1]
        cluster_groups = sybil_df.groupby('cluster')['wallet'].apply(list).to_dict()
        
        print(f"[Pillar 3] Phát hiện {len(cluster_groups)} cụm Sybil.")
        return {
            "total_clusters": len(cluster_groups),
            "clusters": cluster_groups
        }

    def run_cohort_analysis(self, campaign_start_date: str) -> pd.DataFrame:
        """
        Thực hiện Phân tích Cohort.
        Khớp với luồng: run_cohort_analysis() -> BigQuery SQL (Cohort)
        """
        print(f"[Pillar 3] Đang chạy Phân tích Cohort (sau ngày {campaign_start_date})...")
        
        # *** THAY ĐỔI QUAN TRỌNG: Sửa lỗi logic và tối ưu hóa truy vấn ***
        # Lỗi gốc: Dùng MIN() trong WHERE
        # Tối ưu hóa: Thêm bộ lọc DATE(block_timestamp) ở cả 2 CTE
        
        query = f"""
            WITH 
            acquisition AS (
                SELECT 
                    from_address AS user,
                    MIN(DATE(block_timestamp)) AS acquisition_date
                FROM `bigquery-public-data.crypto_ethereum.transactions`
                WHERE to_address = '{Config.TARGET_CONTRACT_ADDRESS.lower()}'
                  -- TỐI ƯU HÓA: Chỉ quét các partition sau ngày bắt đầu
                  AND DATE(block_timestamp) >= '{campaign_start_date}'
                GROUP BY 1
            ),
            activity AS (
                SELECT 
                    DISTINCT from_address AS user,
                    DATE(block_timestamp) AS activity_date
                FROM `bigquery-public-data.crypto_ethereum.transactions`
                WHERE from_address IN (SELECT user FROM acquisition)
                  -- TỐI ƯU HÓA: Chỉ quét các partition sau ngày bắt đầu
                  AND DATE(block_timestamp) >= '{campaign_start_date}'
            ),
            cohort_data AS (
                SELECT
                    a.user,
                    ac.acquisition_date,
                    DATE_DIFF(a.activity_date, ac.acquisition_date, DAY) AS day_number
                FROM activity a
                JOIN acquisition ac ON a.user = ac.user
            )
            SELECT
                acquisition_date,
                COUNT(DISTINCT user) AS cohort_size,
                COUNT(DISTINCT CASE WHEN day_number = 1 THEN user END) AS day_1_retained,
                COUNT(DISTINCT CASE WHEN day_number = 7 THEN user END) AS day_7_retained,
                COUNT(DISTINCT CASE WHEN day_number = 30 THEN user END) AS day_30_retained
            FROM cohort_data
            GROUP BY 1
            ORDER BY 1
        """
        cohort_df = self.db.query_to_dataframe(query)
        print("[Pillar 3] Phân tích Cohort hoàn tất.")
        return cohort_df

    def get_peak_activity_hour(self, contract_address: str) -> int:
        """
        Tìm 'Giờ Vàng' - giờ hoạt động cao điểm của người dùng (0-23h UTC) 
        dựa trên lịch sử giao dịch 90 ngày qua.
        """
        print(f"[Pillar 3] Đang phân tích giờ vàng hoạt động cho {contract_address}...")
        
        # Truy vấn BigQuery để đếm số lượng giao dịch theo từng giờ trong ngày (0-23)
        query = f"""
            SELECT 
                EXTRACT(HOUR FROM block_timestamp) as hour_of_day,
                COUNT(*) as tx_count
            FROM `bigquery-public-data.crypto_ethereum.transactions`
            WHERE to_address = '{contract_address.lower()}'
              -- Tối ưu hóa: Chỉ quét 90 ngày gần nhất để tiết kiệm chi phí & lấy xu hướng mới
              AND DATE(block_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT 1
        """
        df = self.db.query_to_dataframe(query)
        
        if df.empty:
            print("[Pillar 3] Không đủ dữ liệu giao dịch. Mặc định chọn 14h UTC.")
            return 14 # Giá trị fallback an toàn nếu contract mới tinh
            
        peak_hour = int(df.iloc[0]['hour_of_day'])
        print(f"[Pillar 3] Phát hiện giờ vàng: {peak_hour}:00 UTC (Volume cao nhất).")
        return peak_hour
    
    def run(self, wallet_list: list, campaign_start_date: str) -> dict:
        """
        Chạy phân tích Pillar 3 đầy đủ.
        """
        print("\n--- Bắt đầu Phân tích Pillar 3: Hành vi Người dùng ---")
        sybil_results = self.detect_sybil_clusters(wallet_list)
        cohort_results = self.run_cohort_analysis(campaign_start_date)

        # Tự động tính giờ vàng thay vì hardcode
        peak_hour = self.get_peak_activity_hour(Config.TARGET_CONTRACT_ADDRESS)
        
        return {
            "sybil_analysis": sybil_results,
            "cohort_analysis": cohort_results,
            "peak_activity_hour": peak_hour # <-- Trả về kết quả mới
        }