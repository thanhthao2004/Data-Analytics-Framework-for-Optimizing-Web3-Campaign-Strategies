# analysis/pillar2_gas_model.py (KHỚP VỚI SƠ ĐỒ)
import pandas as pd
import numpy as np
from connectors.db_connector import BigQueryConnector
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import warnings

class GasCostForecaster:
    """
    Triển khai Trụ cột 2: Mô hình Kinh tế Gas.
    Khớp với sơ đồ Mermaid P2.
    
    Mô hình Dự báo: ARIMA(1, 1, 1)
    ===============================
    
    Độ tin cậy và Giới hạn:
    ----------------------
    - Mô hình ARIMA(1, 1, 1) phù hợp để nắm bắt xu hướng và tính mùa vụ NGẮN HẠN 
      (dưới 7 ngày) của Base Fee trên Ethereum.
    - Độ chính xác sẽ GIẢM NHANH khi kéo dài dự báo quá 7 ngày do:
      * Base Fee trên Ethereum biến động phụ thuộc vào nhiều yếu tố phức tạp
      * ARIMA là mô hình tuyến tính, có thể bỏ lỡ các mối quan hệ phi tuyến
    
    Độ nhạy và Cảnh báo:
    --------------------
    - Mô hình RẤT NHẠY CẢM với các sự kiện không lường trước (Black Swan events):
      * Nâng cấp mạng (EIP-1559, Merge, các hard fork khác)
      * Sự kiện mint NFT lớn (ví dụ: các dự án NFT hàng đầu phát hành)
      * Tăng đột biến phí giao dịch do cá voi thao túng hoặc flash crash
      * Các sự kiện DeFi lớn (liquidations hàng loạt, bridge hacks)
    - Cần có cơ chế cảnh báo hoặc fallback cho những trường hợp này.
    - Dữ liệu lịch sử chỉ dùng 30 ngày gần nhất để cân bằng giữa độ mới và chi phí truy vấn.
    
    Khuyến nghị Sử dụng:
    -------------------
    - Sử dụng dự báo cho cửa sổ 4 giờ (rolling average) để giảm nhiễu.
    - Kết hợp với các nguồn dữ liệu khác (GasNow, Etherscan forecasters) để xác nhận.
    - Không nên chỉ dựa vào mô hình này cho các quyết định quan trọng về chi phí.
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

    def _calculate_model_accuracy(self, data):
        """
        Tính toán độ chính xác của mô hình ARIMA bằng cách backtesting.
        
        Phương pháp: Walk-forward validation
        - Chia dữ liệu thành train (80%) và test (20%)
        - Huấn luyện trên train, dự báo test
        - Tính các metrics: MAE, RMSE, MAPE
        
        Returns:
            dict: Các metrics độ chính xác
        """
        if len(data) < 48:  # Cần ít nhất 48 giờ (2 ngày) để backtesting
            print("[Pillar 2] Không đủ dữ liệu để đánh giá độ chính xác (cần >= 48 giờ).")
            return None
        
        # Chia dữ liệu: 80% train, 20% test
        split_idx = int(len(data) * 0.8)
        train_data = data[:split_idx]
        test_data = data[split_idx:]
        
        print(f"[Pillar 2] Đang đánh giá độ chính xác: Train={len(train_data)}h, Test={len(test_data)}h...")
        
        warnings.filterwarnings("ignore")
        try:
            # Huấn luyện mô hình trên tập train
            model_val = ARIMA(train_data, order=(1, 1, 1))
            model_fit_val = model_val.fit()
            
            # Dự báo cho tập test
            forecast_test = model_fit_val.get_forecast(steps=len(test_data))
            predicted_values = forecast_test.predicted_mean
            actual_values = test_data.values
            
            # Loại bỏ NaN nếu có
            mask = ~(np.isnan(predicted_values) | np.isnan(actual_values))
            if mask.sum() == 0:
                print("[Pillar 2] Không có dữ liệu hợp lệ để tính toán độ chính xác.")
                return None
                
            predicted_clean = predicted_values[mask]
            actual_clean = actual_values[mask]
            
            # Tính các metrics
            mae = np.mean(np.abs(predicted_clean - actual_clean))
            rmse = np.sqrt(np.mean((predicted_clean - actual_clean) ** 2))
            
            # MAPE: Tránh chia cho 0
            non_zero_mask = actual_clean != 0
            if non_zero_mask.sum() > 0:
                mape = np.mean(np.abs((actual_clean[non_zero_mask] - predicted_clean[non_zero_mask]) / actual_clean[non_zero_mask])) * 100
            else:
                mape = np.nan
            
            # Tính R-squared (coefficient of determination)
            ss_res = np.sum((actual_clean - predicted_clean) ** 2)
            ss_tot = np.sum((actual_clean - np.mean(actual_clean)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else np.nan
            
            # Model fit metrics từ mô hình đã huấn luyện
            aic = model_fit_val.aic
            bic = model_fit_val.bic
            log_likelihood = model_fit_val.llf
            
            accuracy_metrics = {
                "mae": mae,
                "rmse": rmse,
                "mape": mape,
                "r_squared": r_squared,
                "aic": aic,
                "bic": bic,
                "log_likelihood": log_likelihood,
                "test_samples": len(test_data)
            }
            
            warnings.filterwarnings("default")
            return accuracy_metrics
            
        except Exception as e:
            print(f"[Pillar 2] Lỗi khi đánh giá độ chính xác: {e}")
            warnings.filterwarnings("default")
            return None

    def run(self, forecast_days=7, use_cache: bool = False, save_cache: bool = True) -> dict:
        """
        Chạy phân tích Pillar 2 đầy đủ.
        Khớp với luồng: Forecast -> Compute rolling(4h).mean() -> Find min avg_gwei
        
        Args:
            forecast_days: Số ngày dự báo (mặc định: 7)
            use_cache: Nếu True, sẽ đọc từ cache nếu có, không query lại BigQuery
            save_cache: Nếu True, sẽ lưu kết quả vào cache sau khi phân tích
        """
        # Import DataCache ở đây để tránh circular import
        from analysis.data_cache import DataCache
        
        cache = DataCache()
        
        # Thử đọc từ cache nếu được yêu cầu
        if use_cache:
            cached_result = cache.load_pillar2(forecast_days)
            if cached_result is not None:
                print("[Pillar 2] Đã sử dụng dữ liệu từ cache (không query BigQuery).")
                return cached_result
        
        print("\n--- Bắt đầu Phân tích Pillar 2: Chi phí Gas ---")
        
        # Thử đọc dữ liệu lịch sử từ cache trước
        data = None
        if use_cache:
            data = cache.load_pillar2_historical(days_back=30)
        
        # Nếu không có trong cache, query từ BigQuery
        if data is None:
            data = self._fetch_hourly_gas(days_back=30)
            # Lưu dữ liệu lịch sử vào cache
            if save_cache and data is not None:
                cache.save_pillar2_historical(data, days_back=30)
        
        if data is None:
            return {"error": "Không có dữ liệu gas"}
            
        self._train_model(data)
        
        # Tính toán độ chính xác của mô hình (backtesting)
        accuracy_metrics = self._calculate_model_accuracy(data)
        
        # In ra các metrics độ chính xác
        if accuracy_metrics:
            print("\n=== ĐỘ CHÍNH XÁC MÔ HÌNH ARIMA (Backtesting) ===")
            print(f"  • MAE (Mean Absolute Error): {accuracy_metrics['mae']:.4f} Gwei")
            print(f"  • RMSE (Root Mean Squared Error): {accuracy_metrics['rmse']:.4f} Gwei")
            if not np.isnan(accuracy_metrics['mape']):
                print(f"  • MAPE (Mean Absolute Percentage Error): {accuracy_metrics['mape']:.2f}%")
            if not np.isnan(accuracy_metrics['r_squared']):
                print(f"  • R² (Coefficient of Determination): {accuracy_metrics['r_squared']:.4f}")
                print(f"    → Giải thích: {accuracy_metrics['r_squared']*100:.2f}% phương sai được giải thích bởi mô hình")
            print(f"  • AIC (Akaike Information Criterion): {accuracy_metrics['aic']:.2f}")
            print(f"  • BIC (Bayesian Information Criterion): {accuracy_metrics['bic']:.2f}")
            print(f"  • Log Likelihood: {accuracy_metrics['log_likelihood']:.2f}")
            print(f"  • Số mẫu test: {accuracy_metrics['test_samples']} giờ")
            
            # Đánh giá độ tin cậy dựa trên MAPE
            mape = accuracy_metrics.get('mape', np.nan)
            if not np.isnan(mape):
                if mape < 5:
                    reliability = "RẤT CAO"
                elif mape < 10:
                    reliability = "CAO"
                elif mape < 20:
                    reliability = "TRUNG BÌNH"
                else:
                    reliability = "THẤP"
                print(f"\n  📊 ĐỘ TIN CẬY DỰ BÁO: {reliability} (MAPE = {mape:.2f}%)")
            
            print("=" * 50)
        else:
            print("[Pillar 2] Không thể đánh giá độ chính xác (thiếu dữ liệu hoặc lỗi).")
        
        # Lấy các metrics từ mô hình đã huấn luyện (full data)
        if self.model_fit is not None:
            full_model_metrics = {
                "aic_full": self.model_fit.aic,
                "bic_full": self.model_fit.bic,
                "log_likelihood_full": self.model_fit.llf
            }
        else:
            full_model_metrics = {}
        
        steps_to_forecast = forecast_days * 24 # 7 ngày * 24 giờ
        print(f"\n[Pillar 2] Đang dự báo cho {steps_to_forecast} giờ tới...")
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
        
        result = {
            "best_window_start_utc": str(best_window_start),
            "estimated_avg_gwei": best_gas,
            "forecast_dataframe": forecast_df
        }
        
        # Thêm accuracy metrics vào kết quả
        if accuracy_metrics:
            result["model_accuracy"] = accuracy_metrics
        
        if full_model_metrics:
            result["model_fit_metrics"] = full_model_metrics
        
        # Lưu vào cache nếu được yêu cầu
        if save_cache:
            cache.save_pillar2(result, forecast_days)
        
        return result