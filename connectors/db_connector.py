# Class để kết nối và truy vấn (BigQuery, ClickHouse, etc.)
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
        """
        if not self.client:
            print("[Connector] Không thể truy vấn, client chưa được khởi tạo.")
            return pd.DataFrame()
            
        try:
            print(f"Connector] Đang thực thi truy vấn...")
            query_job = self.client.query(sql_query)
            results = query_job.result()  # Chờ kết quả
            df = results.to_dataframe()
            print(f"[Connector] Truy vấn thành công, trả về {len(df)} dòng.")
            return df
        except Exception as e:
            print(f"[Connector] Lỗi truy vấn: {e}")
            return pd.DataFrame()