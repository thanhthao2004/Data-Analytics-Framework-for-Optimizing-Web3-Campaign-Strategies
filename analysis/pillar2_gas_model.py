# analysis/pillar2_gas_model.py (KHỚP VỚI SƠ ĐỒ)
import pandas as pd
from connectors.db_connector import BigQueryConnector
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import warnings

class GasCostForecaster:
    """
    Triển khai Trụ cột 2: Mô hình Kinh tế Gas.
    Khớp với sơ đồ Mermaid P2.
    """
    def __init__(self, db: BigQueryConnector):
        self.db = db
        self.model_fit = None

    def _fetch_hourly_gas(self, days_back=30):
        """
        Lấy dữ liệu base_fee trung bình hàng giờ từ BigQuery.
        Khớp với luồng: _fetch_hourly_gas() -> Run BigQuery SQL
        """
        print(f"[Pillar 2] Đang lấy dữ liệu gas lịch sử ({days_back} ngày)...")
        
        # Truy vấn này khớp với mô tả trong sơ đồ
        query = f"""
            SELECT
                TIMESTAMP_TRUNC(timestamp, HOUR) AS hour,
                AVG(base_fee_per_gas) / 1e9 AS avg_gwei -- Đổi sang Gwei
            FROM `bigquery-public-data.crypto_ethereum.blocks`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)
            GROUP BY 1
            ORDER BY 1
        """
        df = self.db.query_to_dataframe(query)
        if df.empty:
            print("[Pillar 2] Không thể lấy dữ liệu gas.")
            return None
            
        df['hour'] = pd.to_datetime(df['hour'], utc=True)
        df.set_index('hour', inplace=True)
        
        # Khớp với luồng: Resample hourly -> fill missing hours
        df = df.resample('h').ffill() 
        return df['avg_gwei']

    def _train_model(self, data):
        """
        Huấn luyện mô hình ARIMA.
        Khớp với luồng: _train_model() -> ARIMA(1,1,1).fit()
        """
        print("[Pillar 2] Đang huấn luyện mô hình ARIMA...")
        warnings.filterwarnings("ignore") # Tắt cảnh báo statsmodels
        
        # Sơ đồ chỉ định (1,1,1)
        model = ARIMA(data, order=(1, 1, 1))
        self.model_fit = model.fit()
        print("[Pillar 2] Huấn luyện mô hình hoàn tất.")
        warnings.filterwarnings("default")

    def run(self, forecast_days=7) -> dict:
        """
        Chạy phân tích Pillar 2 đầy đủ.
        Khớp với luồng: Forecast -> Compute rolling(4h).mean() -> Find min avg_gwei
        """
        print("\n--- Bắt đầu Phân tích Pillar 2: Chi phí Gas ---")
        
        data = self._fetch_hourly_gas(days_back=30)
        if data is None:
            return {"error": "Không có dữ liệu gas"}
            
        self._train_model(data)
        
        steps_to_forecast = forecast_days * 24 # 7 ngày * 24 giờ
        print(f"[Pillar 2] Đang dự báo cho {steps_to_forecast} giờ tới...")
        forecast = self.model_fit.get_forecast(steps=steps_to_forecast)
        forecast_df = forecast.conf_int(alpha=0.05)
        forecast_df['predicted_gwei'] = forecast.predicted_mean
        
        # Khớp với luồng: Compute rolling(4h).mean()
        window_size_hours = 4
        rolling_avg = forecast_df['predicted_gwei'].rolling(window=window_size_hours).mean()
        
        # Khớp với luồng: Find min avg_gwei -> best_window_start
        best_window_start = rolling_avg.idxmin()
        if pd.isna(best_window_start):
             best_window_start = forecast_df['predicted_gwei'].idxmin()
             
        best_gas = rolling_avg.min()
        
        print(f"[Pillar 2] Hoàn tất. Cửa sổ 4 giờ rẻ nhất bắt đầu lúc: {best_window_start} UTC")
        
        return {
            "best_window_start_utc": str(best_window_start),
            "estimated_avg_gwei": best_gas,
            "forecast_dataframe": forecast_df
        }