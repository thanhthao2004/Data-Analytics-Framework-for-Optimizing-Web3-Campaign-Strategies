# analysis/data_cache.py
"""
Module quản lý lưu trữ và đọc dữ liệu từ file để phân tích offline.
Tiết kiệm chi phí BigQuery và cho phép phân tích lại dữ liệu đã lấy.
Tất cả dữ liệu được lưu dưới dạng CSV để dễ phân tích trong thư mục data/.
"""
import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

class DataCache:
    """
    Lớp quản lý cache dữ liệu cho Framework.
    Lưu và đọc kết quả phân tích vào/từ các file CSV trong thư mục data/.
    """
    
    def __init__(self, base_dir: str = "data"):
        """
        Khởi tạo DataCache.
        
        Args:
            base_dir: Thư mục chứa các file cache (mặc định: "data")
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Tạo các thư mục con
        (self.base_dir / "pillar1_risk").mkdir(exist_ok=True)
        (self.base_dir / "pillar2_gas").mkdir(exist_ok=True)
        (self.base_dir / "pillar2_gas" / "historical").mkdir(exist_ok=True)
        (self.base_dir / "pillar2_gas" / "forecast").mkdir(exist_ok=True)
        (self.base_dir / "pillar3_user").mkdir(exist_ok=True)
        (self.base_dir / "pillar3_user" / "cohort").mkdir(exist_ok=True)
        
    def _get_pillar1_path(self, contract_address: str) -> Path:
        """Tạo đường dẫn file cho Pillar 1 (CSV)."""
        safe_address = contract_address.lower().replace("0x", "")
        return self.base_dir / "pillar1_risk" / f"risk_{safe_address}.csv"
    
    def _get_pillar1_metadata_path(self, contract_address: str) -> Path:
        """Tạo đường dẫn file metadata cho Pillar 1 (JSON - chỉ lưu metadata nhỏ)."""
        safe_address = contract_address.lower().replace("0x", "")
        return self.base_dir / "pillar1_risk" / f"risk_{safe_address}_metadata.json"
    
    def _get_pillar2_forecast_path(self, forecast_days: int = 7) -> Path:
        """Tạo đường dẫn file cho dự báo gas Pillar 2 (CSV)."""
        today = datetime.now().strftime("%Y%m%d")
        return self.base_dir / "pillar2_gas" / "forecast" / f"gas_forecast_{forecast_days}d_{today}.csv"
    
    def _get_pillar2_forecast_metadata_path(self, forecast_days: int = 7) -> Path:
        """Tạo đường dẫn file metadata cho dự báo gas (JSON - chỉ metadata nhỏ)."""
        today = datetime.now().strftime("%Y%m%d")
        return self.base_dir / "pillar2_gas" / "forecast" / f"gas_forecast_{forecast_days}d_{today}_metadata.json"
    
    def _get_pillar2_historical_path(self, days_back: int = 30) -> Path:
        """Tạo đường dẫn file cho dữ liệu gas lịch sử (Pillar 2)."""
        return self.base_dir / "pillar2_gas" / "historical" / f"gas_history_{days_back}d.csv"
    
    def _get_pillar3_path(self, campaign_start_date: str) -> Path:
        """Tạo đường dẫn file cho Pillar 3 (CSV)."""
        safe_date = campaign_start_date.replace("-", "")
        return self.base_dir / "pillar3_user" / f"user_analysis_{safe_date}.csv"
    
    def _get_pillar3_cohort_path(self, campaign_start_date: str) -> Path:
        """Tạo đường dẫn file cho Cohort analysis (CSV)."""
        safe_date = campaign_start_date.replace("-", "")
        return self.base_dir / "pillar3_user" / "cohort" / f"cohort_analysis_{safe_date}.csv"
    
    # ========== PILLAR 1: Risk Analysis ==========
    
    def save_pillar1(self, contract_address: str, risk_data: dict) -> bool:
        """
        Lưu kết quả phân tích rủi ro (Pillar 1) vào file CSV.
        
        Args:
            contract_address: Địa chỉ hợp đồng
            risk_data: Dictionary chứa kết quả phân tích
            
        Returns:
            True nếu lưu thành công, False nếu có lỗi
        """
        try:
            csv_path = self._get_pillar1_path(contract_address)
            metadata_path = self._get_pillar1_metadata_path(contract_address)
            
            # Chuyển đổi dữ liệu thành DataFrame
            rows = []
            
            # Thông tin chính
            rows.append({
                "metric": "final_risk_score",
                "value": risk_data.get("final_risk_score", 0),
                "type": "score"
            })
            
            # Internal risk
            internal_risk = risk_data.get("internal_risk", {})
            # Xử lý đúng: score = 0 là hợp lệ, chỉ dùng default 50 khi không có key 'score'
            internal_score_raw = internal_risk.get("score")
            if internal_score_raw is None:
                internal_score_raw = 50  # Default khi không tìm thấy source code
            internal_score_normalized = internal_score_raw / 100.0
            rows.append({
                "metric": "internal_risk_score",
                "value": internal_score_normalized,
                "type": "score"
            })
            
            # Dependency risks
            dependency_risks = risk_data.get("dependency_risks", [])
            rows.append({
                "metric": "dependency_risk_count",
                "value": len(dependency_risks),
                "type": "count"
            })
            
            # Dependency graph nodes
            dependency_nodes = risk_data.get("dependency_graph_nodes", [])
            rows.append({
                "metric": "dependency_nodes_count",
                "value": len(dependency_nodes),
                "type": "count"
            })
            
            # Lưu danh sách rủi ro vào một cột riêng
            if dependency_risks:
                for i, risk in enumerate(dependency_risks):
                    rows.append({
                        "metric": f"dependency_risk_{i+1}",
                        "value": risk,
                        "type": "risk_description"
                    })
            
            # Lưu danh sách nodes
            if dependency_nodes:
                for i, node in enumerate(dependency_nodes):
                    rows.append({
                        "metric": f"dependency_node_{i+1}",
                        "value": node,
                        "type": "address"
                    })
            
            # Lưu issues từ internal risk
            issues = internal_risk.get("issues_found", [])
            if issues:
                for i, issue in enumerate(issues):
                    rows.append({
                        "metric": f"internal_issue_{i+1}",
                        "value": issue,
                        "type": "issue_description"
                    })
            
            df = pd.DataFrame(rows)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            # Lưu metadata nhỏ (timestamp, contract address)
            metadata = {
                "contract_address": contract_address,
                "timestamp": datetime.now().isoformat(),
                "csv_file": str(csv_path)
            }
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"[Cache] Đã lưu kết quả Pillar 1 vào: {csv_path}")
            return True
            
        except Exception as e:
            print(f"[Cache] Lỗi khi lưu Pillar 1: {e}")
            return False
    
    def load_pillar1(self, contract_address: str) -> dict:
        """
        Đọc kết quả phân tích rủi ro (Pillar 1) từ file CSV.
        
        Args:
            contract_address: Địa chỉ hợp đồng
            
        Returns:
            Dictionary chứa kết quả phân tích, hoặc None nếu không tìm thấy
        """
        try:
            csv_path = self._get_pillar1_path(contract_address)
            metadata_path = self._get_pillar1_metadata_path(contract_address)
            
            if not csv_path.exists():
                return None
            
            df = pd.read_csv(csv_path)
            
            # Đọc metadata
            timestamp = None
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    timestamp = metadata.get('timestamp')
            
            # Khôi phục dữ liệu từ DataFrame
            result = {}
            
            # Đọc các giá trị số
            final_risk_score_row = df[df['metric'] == 'final_risk_score']
            if not final_risk_score_row.empty:
                result['final_risk_score'] = float(final_risk_score_row.iloc[0]['value'])
            
            # Internal risk
            internal_score_row = df[df['metric'] == 'internal_risk_score']
            internal_score = 0.0
            if not internal_score_row.empty:
                internal_score = float(internal_score_row.iloc[0]['value'])
            
            # Issues
            issue_rows = df[df['type'] == 'issue_description']
            issues = issue_rows['value'].tolist() if not issue_rows.empty else []
            
            result['internal_risk'] = {
                "score": int(internal_score * 100),
                "issues_found": issues
            }
            
            # Dependency risks
            risk_rows = df[df['type'] == 'risk_description']
            dependency_risks = risk_rows['value'].tolist() if not risk_rows.empty else []
            result['dependency_risks'] = dependency_risks
            
            # Dependency nodes
            node_rows = df[df['type'] == 'address']
            dependency_nodes = node_rows['value'].tolist() if not node_rows.empty else []
            result['dependency_graph_nodes'] = dependency_nodes
            
            print(f"[Cache] Đã đọc kết quả Pillar 1 từ: {csv_path}")
            if timestamp:
                print(f"[Cache] Timestamp: {timestamp}")
            return result
            
        except Exception as e:
            print(f"[Cache] Lỗi khi đọc Pillar 1: {e}")
            return None
    
    # ========== PILLAR 2: Gas Forecast ==========
    
    def save_pillar2_historical(self, gas_data, days_back: int = 30) -> bool:
        """
        Lưu dữ liệu gas lịch sử vào file CSV.
        
        PHASE 2: Hỗ trợ cả DataFrame (SARIMAX với exog) và Series (old ARIMA).
        
        Args:
            gas_data: Pandas Series hoặc DataFrame chứa dữ liệu gas theo giờ
            days_back: Số ngày lấy dữ liệu
            
        Returns:
            True nếu lưu thành công
        """
        try:
            file_path = self._get_pillar2_historical_path(days_back)
            
            if isinstance(gas_data, pd.DataFrame):
                # PHASE 2: Save full DataFrame with all columns
                df = gas_data.copy()
                df = df.reset_index()  # Move index to column named 'hour'
                if df.columns[0] != 'hour':
                    df.rename(columns={df.columns[0]: 'hour'}, inplace=True)
            else:
                # Old format: Series -> convert to DataFrame
                df = pd.DataFrame({
                    'hour': gas_data.index,
                    'avg_gwei': gas_data.values
                })
            
            df.to_csv(file_path, index=False)
            print(f"[Cache] Đã lưu dữ liệu gas lịch sử ({days_back}d) vào: {file_path}")
            return True
        except Exception as e:
            print(f"[Cache] Lỗi khi lưu dữ liệu gas lịch sử: {e}")
            return False
    
    def load_pillar2_historical(self, days_back: int = 30):
        """
        Đọc dữ liệu gas lịch sử từ file CSV.
        
        PHASE 2: Trả về DataFrame nếu có exogenous variables, Series nếu chỉ có avg_gwei.
        
        Args:
            days_back: Số ngày dữ liệu cần đọc
            
        Returns:
            Pandas DataFrame (SARIMAX) hoặc Series (old ARIMA) hoặc None nếu không tìm thấy
        """
        try:
            file_path = self._get_pillar2_historical_path(days_back)
            
            if not file_path.exists():
                return None
            
            df = pd.read_csv(file_path)
            df['hour'] = pd.to_datetime(df['hour'], utc=True)
            df.set_index('hour', inplace=True)
            
            print(f"[Cache] Đã đọc dữ liệu gas lịch sử ({days_back}d) từ: {file_path}")
            
            # PHASE 2: Check if exogenous variables exist
            exog_cols = [col for col in df.columns if col != 'avg_gwei']
            
            if exog_cols:
                # Return full DataFrame (SARIMAX format)
                print(f"[Cache] Phát hiện exogenous variables: {exog_cols}")
                return df
            else:
                # Return Series (old ARIMA format, backward compatibility)
                print("[Cache] Dữ liệu old format (chỉ có avg_gwei)")
                return df['avg_gwei']
            
        except Exception as e:
            print(f"[Cache] Lỗi khi đọc dữ liệu gas lịch sử: {e}")
            return None
    
    def save_pillar2(self, forecast_data: dict, forecast_days: int = 7) -> bool:
        """
        Lưu kết quả dự báo gas (Pillar 2) vào file CSV.
        
        Args:
            forecast_data: Dictionary chứa kết quả dự báo
            forecast_days: Số ngày dự báo
            
        Returns:
            True nếu lưu thành công
        """
        try:
            csv_path = self._get_pillar2_forecast_path(forecast_days)
            metadata_path = self._get_pillar2_forecast_metadata_path(forecast_days)
            
            # Lưu forecast DataFrame vào CSV
            if "forecast_dataframe" in forecast_data:
                df = forecast_data["forecast_dataframe"]
                df.to_csv(csv_path, index=True)
                print(f"[Cache] Đã lưu forecast DataFrame vào: {csv_path}")
            
            # Lưu metadata (best_window, metrics, accuracy)
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "forecast_days": forecast_days,
                "best_window_start_utc": forecast_data.get("best_window_start_utc"),
                "estimated_avg_gwei": float(forecast_data.get("estimated_avg_gwei", 0)),
                "model_accuracy": forecast_data.get("model_accuracy"),
                "model_fit_metrics": forecast_data.get("model_fit_metrics"),
                "forecast_csv": str(csv_path)
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"[Cache] Đã lưu metadata Pillar 2 vào: {metadata_path}")
            return True
            
        except Exception as e:
            print(f"[Cache] Lỗi khi lưu Pillar 2: {e}")
            return False
    
    def load_pillar2(self, forecast_days: int = 7) -> dict:
        """
        Đọc kết quả dự báo gas (Pillar 2) từ file CSV.
        
        Args:
            forecast_days: Số ngày dự báo
            
        Returns:
            Dictionary chứa kết quả dự báo hoặc None
        """
        try:
            csv_path = self._get_pillar2_forecast_path(forecast_days)
            metadata_path = self._get_pillar2_forecast_metadata_path(forecast_days)
            
            if not csv_path.exists() or not metadata_path.exists():
                return None
            
            # Đọc metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Đọc forecast DataFrame
            forecast_df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            
            result = {
                "best_window_start_utc": metadata.get("best_window_start_utc"),
                "estimated_avg_gwei": metadata.get("estimated_avg_gwei"),
                "forecast_dataframe": forecast_df,
                "model_accuracy": metadata.get("model_accuracy"),
                "model_fit_metrics": metadata.get("model_fit_metrics")
            }
            
            print(f"[Cache] Đã đọc kết quả Pillar 2 từ: {csv_path}")
            print(f"[Cache] Timestamp: {metadata.get('timestamp', 'N/A')}")
            return result
            
        except Exception as e:
            print(f"[Cache] Lỗi khi đọc Pillar 2: {e}")
            return None
    
    # ========== PILLAR 3: User Behavior ==========
    
    def save_pillar3(self, user_data: dict, campaign_start_date: str) -> bool:
        """
        Lưu kết quả phân tích người dùng (Pillar 3) vào file CSV.
        
        Args:
            user_data: Dictionary chứa kết quả phân tích
            campaign_start_date: Ngày bắt đầu chiến dịch
            
        Returns:
            True nếu lưu thành công
        """
        try:
            csv_path = self._get_pillar3_path(campaign_start_date)
            cohort_path = self._get_pillar3_cohort_path(campaign_start_date)
            
            # Chuyển đổi dữ liệu thành DataFrame
            rows = []
            
            # Peak activity hour
            rows.append({
                "metric": "peak_activity_hour",
                "value": user_data.get("peak_activity_hour", 14),
                "type": "hour"
            })
            
            # Sybil analysis
            sybil_analysis = user_data.get("sybil_analysis", {})
            rows.append({
                "metric": "sybil_clusters_count",
                "value": sybil_analysis.get("total_clusters", 0),
                "type": "count"
            })
            
            # Lưu các clusters
            clusters = sybil_analysis.get("clusters", {})
            if clusters:
                for cluster_id, wallets in clusters.items():
                    for i, wallet in enumerate(wallets):
                        rows.append({
                            "metric": f"sybil_cluster_{cluster_id}_wallet_{i+1}",
                            "value": wallet,
                            "type": "wallet_address"
                        })
            
            df = pd.DataFrame(rows)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            # Lưu cohort DataFrame riêng
            if "cohort_analysis" in user_data:
                cohort_df = user_data["cohort_analysis"]
                if isinstance(cohort_df, pd.DataFrame) and not cohort_df.empty:
                    cohort_df.to_csv(cohort_path, index=False)
                    print(f"[Cache] Đã lưu cohort analysis vào: {cohort_path}")
            
            print(f"[Cache] Đã lưu kết quả Pillar 3 vào: {csv_path}")
            return True
            
        except Exception as e:
            print(f"[Cache] Lỗi khi lưu Pillar 3: {e}")
            return False
    
    def load_pillar3(self, campaign_start_date: str) -> dict:
        """
        Đọc kết quả phân tích người dùng (Pillar 3) từ file CSV.
        
        Args:
            campaign_start_date: Ngày bắt đầu chiến dịch
            
        Returns:
            Dictionary chứa kết quả phân tích hoặc None
        """
        try:
            csv_path = self._get_pillar3_path(campaign_start_date)
            cohort_path = self._get_pillar3_cohort_path(campaign_start_date)
            
            if not csv_path.exists():
                return None
            
            df = pd.read_csv(csv_path)
            
            result = {}
            
            # Peak activity hour
            peak_hour_row = df[df['metric'] == 'peak_activity_hour']
            if not peak_hour_row.empty:
                result['peak_activity_hour'] = int(peak_hour_row.iloc[0]['value'])
            else:
                result['peak_activity_hour'] = 14  # Default
            
            # Sybil analysis
            cluster_count_row = df[df['metric'] == 'sybil_clusters_count']
            total_clusters = 0
            if not cluster_count_row.empty:
                total_clusters = int(cluster_count_row.iloc[0]['value'])
            
            # Khôi phục clusters
            clusters = {}
            wallet_rows = df[df['type'] == 'wallet_address']
            if not wallet_rows.empty:
                for _, row in wallet_rows.iterrows():
                    metric = row['metric']
                    # Format: sybil_cluster_{cluster_id}_wallet_{i+1}
                    parts = metric.split('_')
                    if len(parts) >= 4:
                        cluster_id = parts[2]
                        if cluster_id not in clusters:
                            clusters[cluster_id] = []
                        clusters[cluster_id].append(row['value'])
            
            result['sybil_analysis'] = {
                "total_clusters": total_clusters,
                "clusters": clusters
            }
            
            # Đọc cohort DataFrame nếu có
            if cohort_path.exists():
                cohort_df = pd.read_csv(cohort_path)
                result["cohort_analysis"] = cohort_df
            
            print(f"[Cache] Đã đọc kết quả Pillar 3 từ: {csv_path}")
            return result
            
        except Exception as e:
            print(f"[Cache] Lỗi khi đọc Pillar 3: {e}")
            return None
