# analysis/pillar2_gas_model.py (KHỚP VỚI SƠ ĐỒ)
import pandas as pd
import numpy as np
from connectors.db_connector import BigQueryConnector
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX  # PHASE 2: SARIMAX support
from statsmodels.tsa.stattools import adfuller
from sklearn.model_selection import TimeSeriesSplit  # PHASE 2: Cross-validation
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
        Lấy dữ liệu base_fee trung bình hàng giờ từ BigQuery với exogenous features.
        Khớp với luồng: _fetch_hourly_gas() -> Run BigQuery SQL
        
        PHASE 2 UPGRADE: Thêm exogenous variables cho SARIMAX:
        - network_utilization: AVG(gas_used) / AVG(gas_limit) - mức độ sử dụng mạng
        - transaction_count: Số lượng transactions mỗi giờ
        - day_of_week: 1-7 (Monday-Sunday)
        - hour_of_day: 0-23 (UTC)
        
        NOTE: base_fee_per_gas trong BigQuery đã ở đơn vị Wei (số nguyên).
        Chia cho 1e9 để chuyển sang Gwei.
        
        Returns:
            pandas.DataFrame với columns: avg_gwei, network_utilization, 
            transaction_count, day_of_week, hour_of_day
            hoặc None nếu không có dữ liệu
        """
        print(f"[Pillar 2] Đang lấy dữ liệu gas lịch sử ({days_back} ngày) với exogenous features...")
        
        # PHASE 2: Enhanced query với exogenous variables
        query = f"""
            SELECT
                hour,
                avg_gwei,
                network_utilization,
                transaction_count,
                -- Temporal features: Extract from already-grouped hour
                EXTRACT(DAYOFWEEK FROM hour) AS day_of_week,  -- 1=Sunday, 7=Saturday
                EXTRACT(HOUR FROM hour) AS hour_of_day
            FROM (
                SELECT
                    TIMESTAMP_TRUNC(timestamp, HOUR) AS hour,
                    AVG(base_fee_per_gas) / 1e9 AS avg_gwei,
                    AVG(gas_used) / NULLIF(AVG(gas_limit), 0) AS network_utilization,
                    COUNT(*) AS transaction_count
                FROM `bigquery-public-data.crypto_ethereum.blocks`
                WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)
                  AND base_fee_per_gas IS NOT NULL
                  AND base_fee_per_gas > 0
                  AND gas_used IS NOT NULL
                  AND gas_limit > 0
                GROUP BY 1
            )
            ORDER BY hour
        """
        df = self.db.query_to_dataframe(query)
        if df.empty:
            print("[Pillar 2] Không có dữ liệu gas.")
            return None
        
        df['hour'] = pd.to_datetime(df['hour'], utc=True)
        df.set_index('hour', inplace=True)
        
        # PHASE 2: Ensure correct dtypes for SARIMAX (critical fix)
        # MUST use float64 for all columns - statsmodels doesn't support Int64
        df['avg_gwei'] = pd.to_numeric(df['avg_gwei'], errors='coerce').astype('float64')
        df['network_utilization'] = pd.to_numeric(df['network_utilization'], errors='coerce').astype('float64')
        df['transaction_count'] = pd.to_numeric(df['transaction_count'], errors='coerce').astype('float64')
        df['day_of_week'] = pd.to_numeric(df['day_of_week'], errors='coerce').astype('float64')  # float, not Int64!
        df['hour_of_day'] = pd.to_numeric(df['hour_of_day'], errors='coerce').astype('float64')  # float, not Int64!
        
        # Resample to hourly frequency
        df = df.resample('h').ffill()
        
        # Fill remaining NULLs
        null_counts = df.isnull().sum()
        if null_counts.any():
            print(f"[Pillar 2] ⚠️  Filling {null_counts.sum()} NULL values")
            df = df.fillna(df.mean())
        
        # Validation
        min_gas = df['avg_gwei'].min()
        max_gas = df['avg_gwei'].max()
        mean_gas = df['avg_gwei'].mean()
        print(f"[Pillar 2] Dữ liệu gas: Min={min_gas:.4f} Gwei, Max={max_gas:.4f} Gwei, Mean={mean_gas:.4f} Gwei")
        print(f"[Pillar 2] Network utilization: Mean={df['network_utilization'].mean():.3f}")
        print(f"[Pillar 2] Transaction count: Mean={df['transaction_count'].mean():.0f}")
        
        return df


    def _train_model(self, endog_data, exog_data=None):
        """
        Huấn luyện mô hình SARIMAX (PHASE 2 UPGRADE từ ARIMA).
        
        SARIMAX = Seasonal Auto-Regressive Integrated Moving Average with eXogenous variables
        - Seasonal order (P,D,Q,s): (1,1,1,24) - chu kỳ 24 giờ
        - Exogenous variables: network_utilization, day_of_week, hour_of_day, etc.
        
        Args:
            endog_data: pandas.Series - Target variable (avg_gwei)
            exog_data: pandas.DataFrame - Exogenous variables (optional)
        """
        print("[Pillar 2] Đang huấn luyện mô hình SARIMAX...")
        warnings.filterwarnings("ignore")  # Tắt cảnh báo statsmodels
        
        try:
            # PHASE 2: SARIMAX with seasonal component (24-hour cycle)
            # order=(1,1,1): ARIMA parameters (p,d,q)
            # seasonal_order=(1,1,1,24): Seasonal ARIMA parameters (P,D,Q,s)
            #   s=24: 24-hour cycle (daily seasonality)
            model = SARIMAX(
                endog_data,
                exog=exog_data,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 24),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            self.model_fit = model.fit(disp=False, maxiter=200)
            print("[Pillar 2] Huấn luyện mô hình SARIMAX hoàn tất.")
            
        except Exception as e:
            print(f"[Pillar 2] ⚠️  CẢNH BÁO: SARIMAX training failed: {e}")
            print("[Pillar 2] Fallback to simple ARIMA model...")
            # Fallback to ARIMA if SARIMAX fails
            model = ARIMA(endog_data, order=(1, 1, 1))
            self.model_fit = model.fit()
            print("[Pillar 2] Đã fallback sang ARIMA thành công.")
        
        warnings.filterwarnings("default")


    def _cross_validate_model(self, endog_data, exog_data=None, n_splits=5):
        """
        PHASE 2: Cross-validation cho SARIMAX model.
        
        Sử dụng TimeSeriesSplit để validate model trên nhiều folds.
        Đây là phương pháp robust hơn single train-test split.
        
        Args:
            endog_data: pandas.Series - Target variable (avg_gwei)
            exog_data: pandas.DataFrame - Exogenous variables
            n_splits: int - Số lượng folds (default: 5)
        
        Returns:
            dict: Aggregated metrics với mean và std across folds
        """
        if len(endog_data) < 120:  # Cần ít nhất 120 giờ (5 ngày) cho CV
            print("[Pillar 2] Không đủ dữ liệu cho cross-validation (cần >= 120 giờ).")
            return None
        
        print(f"[Pillar 2] Đang chạy {n_splits}-fold cross-validation với SARIMAX...")
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        fold_metrics = {
            'mae': [],
            'rmse': [],
            'mape': [],
            'r_squared': []
        }
        
        warnings.filterwarnings("ignore")
        
        for fold_idx, (train_idx, test_idx) in enumerate(tscv.split(endog_data)):
            try:
                # Split data
                y_train = endog_data.iloc[train_idx]
                y_test = endog_data.iloc[test_idx]
                
                X_train = exog_data.iloc[train_idx] if exog_data is not None else None
                X_test = exog_data.iloc[test_idx] if exog_data is not None else None
                
                # Train SARIMAX on this fold
                model = SARIMAX(
                    y_train,
                    exog=X_train,
                    order=(1, 1, 1),
                    seasonal_order=(1, 1, 1, 24),
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
                model_fit = model.fit(disp=False, maxiter=100)
                
                # Forecast on test set
                if X_test is not None:
                    forecast = model_fit.get_forecast(steps=len(y_test), exog=X_test)
                else:
                    forecast = model_fit.get_forecast(steps=len(y_test))
                
                y_pred = forecast.predicted_mean
                y_true = y_test.values
                
                # Calculate metrics for this fold
                mask = ~(np.isnan(y_pred) | np.isnan(y_true))
                if mask.sum() > 0:
                    y_pred_clean = y_pred[mask]
                    y_true_clean = y_true[mask]
                    
                    mae = np.mean(np.abs(y_pred_clean - y_true_clean))
                    rmse = np.sqrt(np.mean((y_pred_clean - y_true_clean) ** 2))
                    
                    # MAPE
                    non_zero = y_true_clean != 0
                    if non_zero.sum() > 0:
                        mape = np.mean(np.abs((y_true_clean[non_zero] - y_pred_clean[non_zero]) / 
                                             y_true_clean[non_zero])) * 100
                    else:
                        mape = np.nan
                    
                    # R²
                    ss_res = np.sum((y_true_clean - y_pred_clean) ** 2)
                    ss_tot = np.sum((y_true_clean - np.mean(y_true_clean)) ** 2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else np.nan
                    
                    fold_metrics['mae'].append(mae)
                    fold_metrics['rmse'].append(rmse)
                    if not np.isnan(mape):
                        fold_metrics['mape'].append(mape)
                    if not np.isnan(r_squared):
                        fold_metrics['r_squared'].append(r_squared)
                    
                    print(f"  Fold {fold_idx+1}/{n_splits}: MAE={mae:.4f}, RMSE={rmse:.4f}, "
                          f"MAPE={mape:.2f}%, R²={r_squared:.4f}")
                
            except Exception as e:
                print(f"  Fold {fold_idx+1}/{n_splits}: Failed - {str(e)[:50]}")
                continue
        
        warnings.filterwarnings("default")
        
        # Aggregate results
        if len(fold_metrics['mae']) == 0:
            print("[Pillar 2] Cross-validation failed on all folds.")
            return None
        
        cv_results = {
            'mae_mean': np.mean(fold_metrics['mae']),
            'mae_std': np.std(fold_metrics['mae']),
            'rmse_mean': np.mean(fold_metrics['rmse']),
            'rmse_std': np.std(fold_metrics['rmse']),
            'mape_mean': np.mean(fold_metrics['mape']) if fold_metrics['mape'] else np.nan,
            'mape_std': np.std(fold_metrics['mape']) if fold_metrics['mape'] else np.nan,
            'r_squared_mean': np.mean(fold_metrics['r_squared']) if fold_metrics['r_squared'] else np.nan,
            'r_squared_std': np.std(fold_metrics['r_squared']) if fold_metrics['r_squared'] else np.nan,
            'n_successful_folds': len(fold_metrics['mae']),
            'n_total_folds': n_splits
        }
        
        print(f"\n[Pillar 2] Cross-validation results ({cv_results['n_successful_folds']}/{n_splits} folds):")
        print(f"  MAE: {cv_results['mae_mean']:.4f} ± {cv_results['mae_std']:.4f} Gwei")
        print(f"  RMSE: {cv_results['rmse_mean']:.4f} ± {cv_results['rmse_std']:.4f} Gwei")
        if not np.isnan(cv_results['mape_mean']):
            print(f"  MAPE: {cv_results['mape_mean']:.2f} ± {cv_results['mape_std']:.2f}%")
        if not np.isnan(cv_results['r_squared_mean']):
            print(f"  R²: {cv_results['r_squared_mean']:.4f} ± {cv_results['r_squared_std']:.4f}")
        
        return cv_results

    def _calculate_model_accuracy(self, data, exog_data=None):
        """
        PHASE 2 UPGRADE: Tính toán độ chính xác của mô hình SARIMAX.
        
        Phương pháp:
        1. Ưu tiên: Cross-validation (5-fold) nếu đủ dữ liệu (>= 120 giờ)
        2. Fallback: Single train-test split (80/20) nếu ít dữ liệu hơn
        
        Args:
            data: pandas.Series hoặc pandas.DataFrame - Target variable (avg_gwei)
            exog_data: pandas.DataFrame - Exogenous variables (optional)
        
        Returns:
            dict: Các metrics độ chính xác
        """
        # Extract target variable if data is DataFrame
        if isinstance(data, pd.DataFrame):
            endog_data = data['avg_gwei'] if 'avg_gwei' in data.columns else data.iloc[:, 0]
        else:
            endog_data = data
        
        # PHASE 2: Prefer cross-validation if enough data
        if len(endog_data) >= 120:
            cv_results = self._cross_validate_model(endog_data, exog_data, n_splits=5)
            if cv_results is not None:
                # Convert CV results to standard format
                return {
                    'mae': cv_results['mae_mean'],
                    'mae_std': cv_results['mae_std'],
                    'rmse': cv_results['rmse_mean'],
                    'rmse_std': cv_results['rmse_std'],
                    'mape': cv_results['mape_mean'],
                    'mape_std': cv_results['mape_std'],
                    'r_squared': cv_results['r_squared_mean'],
                    'r_squared_std': cv_results['r_squared_std'],
                    'validation_method': 'cross_validation',
                    'n_folds': cv_results['n_successful_folds']
                }
        
        # Fallback to single train-test split
        if len(endog_data) < 48:
            print("[Pillar 2] Không đủ dữ liệu để đánh giá độ chính xác (cần >= 48 giờ).")
            return None
        
        print("[Pillar 2] Sử dụng single train-test split (80/20)...")
        
        # Chia dữ liệu: 80% train, 20% test
        split_idx = int(len(endog_data) * 0.8)
        y_train = endog_data[:split_idx]
        y_test = endog_data[split_idx:]
        
        X_train = exog_data[:split_idx] if exog_data is not None else None
        X_test = exog_data[split_idx:] if exog_data is not None else None
        
        print(f"[Pillar 2] Đang đánh giá độ chính xác: Train={len(y_train)}h, Test={len(y_test)}h...")
        
        warnings.filterwarnings("ignore")
        try:
            # Train SARIMAX model
            model_val = SARIMAX(
                y_train,
                exog=X_train,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 24),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            model_fit_val = model_val.fit(disp=False, maxiter=100)
            
            # Forecast on test set
            if X_test is not None:
                forecast_test = model_fit_val.get_forecast(steps=len(y_test), exog=X_test)
            else:
                forecast_test = model_fit_val.get_forecast(steps=len(y_test))
            
            predicted_values = forecast_test.predicted_mean
            actual_values = y_test.values
            
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
        
        # PHASE 2: Extract target and exogenous variables
        if isinstance(data, pd.DataFrame):
            endog_data = data['avg_gwei']
            # Exogenous features (all columns except avg_gwei)
            exog_cols = [col for col in data.columns if col != 'avg_gwei']
            exog_data = data[exog_cols] if exog_cols else None
        else:
            # Backward compatibility: if data is Series (old ARIMA cache)
            endog_data = data
            exog_data = None
        
        # Train model with exogenous variables
        self._train_model(endog_data, exog_data)
        
        # PHASE 2: Tính toán độ chính xác với cross-validation
        accuracy_metrics = self._calculate_model_accuracy(endog_data, exog_data)
        
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
            
            # AIC/BIC only available from single model fit, not cross-validation
            if 'aic' in accuracy_metrics:
                print(f"  • AIC (Akaike Information Criterion): {accuracy_metrics['aic']:.2f}")
            if 'bic' in accuracy_metrics:
                print(f"  • BIC (Bayesian Information Criterion): {accuracy_metrics['bic']:.2f}")
            
            # Validation method
            validation_method = accuracy_metrics.get('validation_method', 'unknown')
            print(f"\n📊 Validation Method: {validation_method}")
            
            if 'log_likelihood' in accuracy_metrics: # Added conditional check for log_likelihood
                print(f"  • Log Likelihood: {accuracy_metrics['log_likelihood']:.2f}")
            if 'test_samples' in accuracy_metrics: # Added conditional check for test_samples
                print(f"  • Số mẫu test: {accuracy_metrics['test_samples']} giờ")
            
            # Đánh giá độ tin cậy dựa trên MAPE và R²
            mape = accuracy_metrics.get('mape', np.nan)
            r_squared = accuracy_metrics.get('r_squared', np.nan)
            
            if not np.isnan(mape):
                if mape < 5:
                    reliability = "RẤT CAO"
                    reliability_color = "GREEN"
                elif mape < 10:
                    reliability = "CAO"
                    reliability_color = "GREEN"
                elif mape < 20:
                    reliability = "TRUNG BÌNH"
                    reliability_color = "YELLOW"
                elif mape < 50:
                    reliability = "THẤP"
                    reliability_color = "ORANGE"
                else:
                    reliability = "KHÔNG ĐÁNG TIN CẬY"
                    reliability_color = "RED"
                print(f"\n  📊 ĐỘ TIN CẬY DỰ BÁO: {reliability} (MAPE = {mape:.2f}%)")
            
            # CẢNH BÁO NGHIÊM TRỌNG nếu R² < 0 hoặc MAPE > 100%
            if not np.isnan(r_squared) and r_squared < 0:
                print(f"\n  ⚠️  CẢNH BÁO NGHIÊM TRỌNG: R² = {r_squared:.6f} < 0")
                print(f"     → Mô hình dự báo TỆ HƠN cả việc dự đoán giá trị trung bình!")
                print(f"     → Dự báo gas KHÔNG ĐÁNG TIN CẬY. Nên sử dụng giờ peak user (P3) thay vì gas window (P2).")
            
            if not np.isnan(mape) and mape > 100:
                print(f"\n  ⚠️  CẢNH BÁO NGHIÊM TRỌNG: MAPE = {mape:.2f}% > 100%")
                print(f"     → Mô hình ARIMA KHÔNG PHÙ HỢP với dữ liệu gas hiện tại.")
                print(f"     → Nguyên nhân có thể: Dữ liệu nhiễu cao, mô hình tuyến tính không nắm bắt được tính phi tuyến.")
                print(f"     → KHUYẾN NGHỊ: Bỏ qua dự báo gas (P2), chỉ dựa vào giờ peak user (P3) để quyết định.")
            
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
        
        steps_to_forecast = forecast_days * 24  # 7 ngày * 24 giờ
        print(f"\n[Pillar 2] Đang dự báo cho {steps_to_forecast} giờ tới...")
        
        # PHASE 2: Generate future exogenous features for forecast period
        if exog_data is not None:
            # Get last timestamp from data
            last_time = endog_data.index[-1]
            
            # Generate future timestamps
            future_times = pd.date_range(start=last_time + pd.Timedelta(hours=1), 
                                        periods=steps_to_forecast, freq='H')
            
            # Create future exogenous DataFrame
            future_exog = pd.DataFrame(index=future_times)
            
            # day_of_week: Extract from timestamp (1=Sunday, 7=Saturday)
            if 'day_of_week' in exog_cols:
                future_exog['day_of_week'] = future_times.dayofweek + 2  # Convert to 1-7
                future_exog['day_of_week'] = future_exog['day_of_week'].replace(8, 1)  # Sunday
            
            # hour_of_day: Extract from timestamp (0-23)
            if 'hour_of_day' in exog_cols:
                future_exog['hour_of_day'] = future_times.hour
            
            # network_utilization: Use historical mean (assumption)
            if 'network_utilization' in exog_cols:
                future_exog['network_utilization'] = exog_data['network_utilization'].mean()
            
            # transaction_count: Use historical mean (assumption)
            if 'transaction_count' in exog_cols:
                future_exog['transaction_count'] = exog_data['transaction_count'].mean()
            
            # Reorder columns to match training data
            future_exog = future_exog[exog_cols]
            
            # Forecast with exogenous variables
            forecast = self.model_fit.get_forecast(steps=steps_to_forecast, exog=future_exog.values)
        else:
            # Fallback: forecast without exog (old ARIMA behavior)
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