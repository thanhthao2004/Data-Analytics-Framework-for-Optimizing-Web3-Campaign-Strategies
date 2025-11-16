# connectors/db_connector.py
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from core.config import Config

class BigQueryConnector:
    """
    Lớp xử lý việc kết nối và thực thi truy vấn tới Google BigQuery.
    Nó sử dụng thông tin credentials từ Config.
    """
    def __init__(self):
        try:
            credentials = (
                service_account.Credentials.from_service_account_file(
                    Config.GOOGLE_APPLICATION_CREDENTIALS
                )
            )
            self.client = bigquery.Client(credentials=credentials)
            print(f"[Connector] Đã kết nối thành công tới BigQuery.")
        except Exception as e:
            print(f"[Connector] Lỗi kết nối BigQuery: {e}")
            self.client = None

    def query_to_dataframe(self, sql_query: str) -> pd.DataFrame:
        """
        Thực thi một truy vấn SQL thô và trả về kết quả
        dưới dạng một Pandas DataFrame.
        *** CÓ TÍCH HỢP KIỂM TRA DRY RUN ĐỂ TRÁNH TỐN KÉM ***
        """
        if not self.client:
            print("[Connector] Không thể truy vấn, client chưa được khởi tạo.")
            return pd.DataFrame()
            
        try:
            # === BƯỚC 1: KIỂM TRA CHI PHÍ (DRY RUN) ===
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            dry_run_job = self.client.query(sql_query, job_config=job_config)
            
            bytes_to_scan = dry_run_job.total_bytes_processed
            gb_to_scan = bytes_to_scan / (1024**3) # Đổi sang GB
            
            print(f"[Connector] ƯỚC TÍNH TRUY VẤN: Sẽ quét {gb_to_scan:.4f} GB.")
            
            # === CẦU DAO AN TOÀN: Đặt giới hạn 800GB (dưới 1TB) ===
            SAFETY_LIMIT_GB = 800
            
            if gb_to_scan > SAFETY_LIMIT_GB:
                error_msg = (
                    f"!!! CẢNH BÁO NGHIÊM TRỌNG: Truy vấn này ước tính quét {gb_to_scan:.4f} GB, "
                    f"vượt quá ngưỡng an toàn {SAFETY_LIMIT_GB} GB. HỦY BỎ ĐỂ BẢO VỆ TÀI KHOẢN."
                )
                print(error_msg)
                raise Exception(error_msg)
            
            if gb_to_scan == 0:
                print("[Connector] Ước tính 0 GB (có thể là DDL hoặc đã cache), tiếp tục chạy.")

            # === BƯỚC 2: CHẠY TRUY VẤN THẬT (VÌ ĐÃ AN TOÀN) ===
            print(f"[Connector] Đang thực thi truy vấn...")
            query_job = self.client.query(sql_query) # Chạy truy vấn thật
            results = query_job.result()  # Chờ kết quả
            df = results.to_dataframe()
            print(f"[Connector] Truy vấn thành công, trả về {len(df)} dòng.")
            return df
            
        except Exception as e:
            print(f"[Connector] Lỗi truy vấn (hoặc bị hủy do dry run): {e}")
            return pd.DataFrame()