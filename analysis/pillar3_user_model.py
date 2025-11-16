# analysis/pillar3_user_model.py (KHỚP VỚI SƠ ĐỒ)
import pandas as pd
from connectors.db_connector import BigQueryConnector
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from core.config import Config # Thêm import Config

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
        print(f"[Pillar 3] Đang lấy đặc điểm Sybil cho {len(wallet_list)} ví...")
        
        wallet_list_str = "('" + "','".join([w.lower() for w in wallet_list]) + "')"

        # Truy vấn này logic tương đương với sơ đồ:
        # Lấy funding_source (from_address của tx đầu tiên)
        # Lấy creation_timestamp (timestamp của tx đầu tiên)
        query = f"""
            WITH ranked_tx AS (
                SELECT 
                    from_address, 
                    to_address,
                    block_timestamp,
                    ROW_NUMBER() OVER(PARTITION BY to_address ORDER BY block_timestamp ASC) as rn
                FROM `bigquery-public-data.crypto_ethereum.transactions`
                WHERE to_address IN {wallet_list_str}
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
            print("ℹ[Pillar 3] Không tìm thấy dữ liệu giao dịch cho các ví này.")
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
        dbscan = DBSCAN(eps=0.5, min_samples=3)
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
        
        # Truy vấn này khớp hoàn toàn với logic trong sơ đồ
        query = f"""
            WITH 
            acquisition AS (
                SELECT 
                    from_address AS user,
                    MIN(DATE(block_timestamp)) AS acquisition_date
                FROM `bigquery-public-data.crypto_ethereum.transactions`
                WHERE to_address = '{Config.TARGET_CONTRACT_ADDRESS.lower()}'
                  AND MIN(DATE(block_timestamp)) >= '{campaign_start_date}'
                GROUP BY 1
            ),
            activity AS (
                SELECT 
                    DISTINCT from_address AS user,
                    MIN(DATE(block_timestamp)) AS activity_date
                FROM `bigquery-public-data.crypto_ethereum.transactions`
                WHERE from_address IN (SELECT user FROM acquisition)
                  AND MIN(DATE(block_timestamp)) >= '{campaign_start_date}'
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

    def run(self, wallet_list: list, campaign_start_date: str) -> dict:
        """
        Chạy phân tích Pillar 3 đầy đủ.
        """
        print("\n--- Bắt đầu Phân tích Pillar 3: Hành vi Người dùng ---")
        sybil_results = self.detect_sybil_clusters(wallet_list)
        cohort_results = self.run_cohort_analysis(campaign_start_date)
        
        return {
            "sybil_analysis": sybil_results,
            "cohort_analysis": cohort_results
        }