# Cấu trúc thư mục Cache

Dữ liệu cache được lưu tự động trong thư mục `data/` của project. Framework sẽ tự động tạo các thư mục con khi cần thiết.

## Cấu trúc thư mục

```
data/
├── potential_wallets.csv          # Danh sách ví đầu vào (nếu có)
│
├── pillar1_risk/                  # Kết quả phân tích rủi ro hợp đồng
│   ├── risk_{contract_address}.csv
│   │   Ví dụ: risk_b8c77482e45f1f44de1745f52c74426c631bdd52.csv
│   └── risk_{contract_address}_metadata.json  # Metadata nhỏ (timestamp)
│
├── pillar2_gas/                   # Dự báo chi phí gas
│   ├── historical/                # Dữ liệu gas lịch sử
│   │   └── gas_history_{days}d.csv
│   │       Ví dụ: gas_history_30d.csv
│   │
│   └── forecast/                  # Dự báo gas
│       ├── gas_forecast_{days}d_{date}.csv
│       │   Ví dụ: gas_forecast_7d_20250123.csv  # DataFrame forecast
│       └── gas_forecast_{days}d_{date}_metadata.json  # Metadata (best_window, metrics)
│
└── pillar3_user/                  # Phân tích hành vi người dùng
    ├── user_analysis_{date}.csv
    │   Ví dụ: user_analysis_20250623.csv  # Sybil analysis, peak hour
    └── cohort/                    # Cohort analysis
        └── cohort_analysis_{date}.csv
            Ví dụ: cohort_analysis_20250623.csv
```

## Đường dẫn tuyệt đối

Dữ liệu cache được lưu tại:
```
/Users/tranthithanhthao/Documents/GitHub/Data-Analytics-Framework-for-Optimizing-Web3-Campaign-Strategies/data/
```

## Định dạng file

**TẤT CẢ DỮ LIỆU ĐƯỢC LƯU DƯỚI DẠNG CSV** để dễ phân tích và xử lý.

### Pillar 1 (Risk Analysis)
- **Format**: CSV (chính) + JSON (metadata nhỏ)
- **CSV**: Kết quả phân tích rủi ro hợp đồng (metric, value, type)
  - Columns: `metric`, `value`, `type`
  - Chứa: risk scores, dependency risks, internal issues, dependency nodes
- **JSON metadata**: Timestamp, contract address
- **Tên file**: `risk_{contract_address}.csv` (địa chỉ hợp đồng được làm sạch)

### Pillar 2 (Gas Forecast)
- **Historical CSV**: Dữ liệu gas lịch sử (hour, avg_gwei)
- **Forecast CSV**: DataFrame chứa dự báo chi tiết theo giờ
  - Index: Timestamp
  - Columns: predicted_gwei, confidence intervals
- **JSON metadata**: Best window, model accuracy metrics, timestamp
- **Tên file forecast**: `gas_forecast_{số_ngày}d_{YYYYMMDD}.csv`

### Pillar 3 (User Behavior)
- **CSV chính**: Sybil analysis, peak activity hour
  - Columns: `metric`, `value`, `type`
  - Chứa: peak_activity_hour, sybil clusters, wallet addresses
- **CSV cohort**: Cohort analysis DataFrame
  - Columns: acquisition_date, cohort_size, day_X_retained
- **Tên file**: `user_analysis_{YYYYMMDD}.csv` (dựa trên campaign_start_date)

## Lưu ý

1. **Tự động tạo thư mục**: Framework tự động tạo các thư mục khi chạy lần đầu
2. **Làm sạch địa chỉ**: Địa chỉ hợp đồng được làm sạch (bỏ "0x", lowercase) khi tạo tên file
3. **Ngày tháng**: Dữ liệu được đánh dấu theo ngày tạo để tránh ghi đè
4. **Kích thước**: Dữ liệu cache có thể lớn, đặc biệt là dữ liệu gas lịch sử (30 ngày × 24 giờ)

## Xóa cache

Nếu muốn xóa toàn bộ cache và query lại từ đầu:
```bash
rm -rf data/pillar1_risk/* data/pillar2_gas/* data/pillar3_user/*
```

Hoặc xóa cache của một pillar cụ thể:
```bash
# Xóa cache Pillar 1
rm -rf data/pillar1_risk/*

# Xóa cache Pillar 2
rm -rf data/pillar2_gas/*

# Xóa cache Pillar 3
rm -rf data/pillar3_user/*
```

