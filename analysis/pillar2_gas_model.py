# analysis/pillar2_gas_model.py
# Pillar 2: Gas Economics
import pandas as pd
from connectors.db_connector import BigQueryConnector
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import warnings

class GasCostForecaster:
    """
    Triển khai Trụ cột 2: Mô hình Kinh tế Gas.
    Sử dụng mô hình Time-series (ARIMA)  để dự báo 
    các 'khung thời gian chi phí thấp' trong 7 ngày tới[cite: 229].
    """
    def __init__(self, db: BigQueryConnector):
        self.db = db
        self.model_fit = None

    def _fetch_hourly_gas(self, days_back=30):
        """
        Lấy dữ liệu base_fee trung bình hàng giờ từ BigQuery.
        """
        print(f"[Pillar 2] Đang lấy dữ liệu gas lịch sử ({days_back} ngày)...")
        query = f"""
            SELECT
                TIMESTAMP_TRUNC(block_timestamp, HOUR) AS hour,
                AVG(base_fee_per_gas) / 1e9 AS avg_gwei -- Đổi sang Gwei
            FROM `bigquery-public-data.crypto_ethereum.blocks`
            WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)
            GROUP BY 1
            ORDER BY 1
        """
        df = self.db.query_to_dataframe(query)
        if df.empty:
            print("[Pillar 2] Không thể lấy dữ liệu gas.")
            return None
            
        df['hour'] = pd.to_datetime(df['hour'], utc=True)
        df.set_index('hour', inplace=True)
        # Điền các giá trị bị thiếu (nếu có)
        df = df.resample('H').ffill() 
        return df['avg_gwei']

    def _train_model(self, data):
        """
        Huấn luyện mô hình ARIMA.
        Sử dụng (p,d,q) = (1,1,1) làm ví dụ đơn giản.
        """
        print("[Pillar 2] Đang huấn luyện mô hình ARIMA...")
        # (p,d,q) - (AR, I, MA)
        # d=1 vì giá gas thường không ổn định (non-stationary)
        warnings.filterwarnings("ignore") # Tắt cảnh báo statsmodels
        model = ARIMA(data, order=(1, 1, 1))
        self.model_fit = model.fit()
        print("[Pillar 2] Huấn luyện mô hình hoàn tất.")
        warnings.filterwarnings("default")

    def run(self, forecast_days=7) -> dict:
        """
        Chạy phân tích Pillar 2 đầy đủ.
        Mục tiêu: Tìm "optimal 'low-cost windows'"[cite: 229].
        """
        print("\n--- Bắt đầu Phân tích Pillar 2: Chi phí Gas ---")
        
        # 1. Lấy dữ liệu và huấn luyện
        data = self._fetch_hourly_gas(days_back=30)
        if data is None:
            return {"error": "Không có dữ liệu gas"}
            
        self._train_model(data)
        
        # 2. Dự báo
        steps_to_forecast = forecast_days * 24 # 7 ngày * 24 giờ
        print(f"[Pillar 2] Đang dự báo cho {steps_to_forecast} giờ tới...")
        forecast = self.model_fit.get_forecast(steps=steps_to_forecast)
        forecast_df = forecast.conf_int(alpha=0.05)
        forecast_df['predicted_gwei'] = forecast.predicted_mean
        
        # 3. Logic nghiệp vụ: Tìm cửa sổ rẻ nhất
        window_size_hours = 4 # Cửa sổ 4 giờ
        rolling_avg = forecast_df['predicted_gwei'].rolling(window=window_size_hours).mean()
        
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