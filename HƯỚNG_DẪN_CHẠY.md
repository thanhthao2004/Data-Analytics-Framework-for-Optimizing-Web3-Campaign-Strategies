# Hướng Dẫn Chạy Framework Phân Tích Chiến Dịch Web3

## Yêu cầu Trước khi Chạy

### 1. Cài đặt Python Dependencies

```bash
pip install -r requirements.txt
```

Hoặc nếu bạn dùng conda:
```bash
conda env create -f environment.yml  # (nếu có)
conda activate web3-analytics
pip install -r requirements.txt
```

### 2. Cấu hình Environment Variables

Tạo file `.env` ở thư mục gốc của project:

```bash
# .env file
ETHERSCAN_API_KEY=your_etherscan_api_key_here
GOOGLE_APPLICATION_CREDENTIALS_PATH=path/to/your/google-credentials.json
```

**Lấy API Keys:**
- **Etherscan API Key**: Đăng ký tại https://etherscan.io/apis (miễn phí)
- **Google Cloud Credentials**: 
  - Tạo Service Account trong Google Cloud Console
  - Download JSON credentials file
  - Đặt đường dẫn vào `GOOGLE_APPLICATION_CREDENTIALS_PATH`

### 3. Kiểm tra Cấu hình

Xem file `core/config.py` để đảm bảo các thiết lập đúng:
- `TARGET_CONTRACT_ADDRESS`: Địa chỉ hợp đồng cần phân tích
- `POTENTIAL_WALLET_LIST_PATH`: Đường dẫn file CSV chứa danh sách ví
- `CAMPAIGN_START_DATE`: Ngày bắt đầu chiến dịch (format: YYYY-MM-DD)

---

## ▶️ Cách Chạy Framework

### Cách 1: Chạy Phân Tích Đầy Đủ (Query BigQuery)

```bash
python run_analysis.py
```

**Điều này sẽ:**
- Query dữ liệu từ BigQuery (tốn chi phí)
- Phân tích 3 Pillars (Risk, Gas, User)
- Tạo khuyến nghị chiến lược
- Tạo visualizations (standard + executive dashboard + advanced)
- Lưu kết quả vào cache (`data/`)

**Thời gian chạy**: ~2-5 phút (tùy vào kích thước dữ liệu)

---

### Cách 2: Chạy với Cache (Tiết kiệm Chi phí)

**Bước 1:** Chạy lần đầu để tạo cache:
```bash
python run_analysis.py
```

**Bước 2:** Các lần sau, chỉ đọc từ cache:
```bash
python run_analysis.py --use-cache
```

**Lợi ích:**
- Không query BigQuery → Tiết kiệm chi phí
- Chạy nhanh hơn (vài giây)
- Có thể chạy offline

---

### Cách 3: Chạy Không Lưu Cache

```bash
python run_analysis.py --no-save-cache
```

**Dùng khi:** Bạn chỉ muốn test nhanh, không muốn lưu kết quả.

---

### Cách 4: Chỉ Đọc Cache, Không Lưu Gì Mới

```bash
python run_analysis.py --use-cache --no-save-cache
```

**Dùng khi:** Xem lại kết quả đã phân tích, không cần query mới.

---

### Xem Help

```bash
python run_analysis.py --help
```

---

## 📊 Output của Framework

### 1. Console Output

Framework sẽ in ra:
- Kết quả phân tích từng Pillar
- Độ chính xác mô hình ARIMA
- Khuyến nghị chiến lược
- Đường dẫn các file visualization đã tạo

### 2. Files Được Tạo

#### Cache Data (CSV format):
```
data/
├── pillar1_risk/
│   └── risk_{contract_address}.csv
├── pillar2_gas/
│   ├── historical/
│   │   └── gas_history_30d.csv
│   └── forecast/
│       └── gas_forecast_7d_{date}.csv
└── pillar3_user/
    ├── user_analysis_{date}.csv
    └── cohort/
        └── cohort_analysis_{date}.csv
```

#### Visualizations:
```
data/visualizations/
├── pillar1/           # Risk analysis charts
├── pillar2/           # Gas forecast charts
├── pillar3/           # User behavior charts
├── comparison/        # Before/after comparisons
├── advanced/          # Advanced professional charts
└── executive/         # Executive Dashboard (quan trọng nhất)
```

---

## 🔍 Ví Dụ Output

```
=======================================================
 Khởi tạo Framework Phân tích Chiến dịch Web3
=======================================================
[Connector] Đã kết nối thành công tới BigQuery.
 === BẮT ĐẦU CHẠY FRAMEWORK PHÂN TÍCH TỔNG HỢP === 

--- Bắt đầu Phân tích Pillar 1: Rủi ro Hợp đồng ---
[Pillar 1] Hoàn tất. Điểm rủi ro cuối cùng: 0.20

--- Bắt đầu Phân tích Pillar 2: Chi phí Gas ---
=== ĐỘ CHÍNH XÁC MÔ HÌNH ARIMA (Backtesting) ===
  • MAE: 2.3456 Gwei
  • RMSE: 3.1234 Gwei
  • MAPE: 5.67%
  • R²: 0.8234
  ĐỘ TIN CẬY DỰ BÁO: CAO (MAPE = 5.67%)

--- Bắt đầu Phân tích Pillar 3: Hành vi Người dùng ---
[Pillar 3] Phát hiện giờ vàng: 19:00 UTC

 === BÁO CÁO HỖ TRỢ QUYẾT ĐỊNH CHIẾN LƯỢC === 
[OK P1]: Điểm rủi ro hợp đồng thấp (0.20). An toàn để tiếp tục.
[THÔNG TIN P2]: Cửa sổ gas tối ưu bắt đầu lúc 2025-11-17 09:00:00+00:00 (UTC).
[TRADE-OFF P2 vs P3]: ĐỀ XUẤT: Chấp nhận chi phí gas cao hơn để triển khai lúc 19:00...

--- Tạo Visualizations ---
[Visualization] Đã lưu Pillar 1 chart: data/visualizations/pillar1/...
[Visualization] Đã lưu Pillar 2 chart: data/visualizations/pillar2/...
[Advanced Viz] Đã lưu Executive Dashboard: data/visualizations/executive/...

=======================================================
 Phân tích hoàn tất.
 Kết quả đã được lưu vào thư mục data/
 Visualizations đã được lưu vào data/visualizations/
=======================================================
```

---

## Troubleshooting

### Lỗi 1: Không kết nối được BigQuery

**Triệu chứng:**
```
[Connector] Lỗi kết nối BigQuery: ...
```

**Giải pháp:**
1. Kiểm tra `GOOGLE_APPLICATION_CREDENTIALS_PATH` trong `.env`
2. Đảm bảo file credentials JSON tồn tại và hợp lệ
3. Kiểm tra Service Account có quyền truy cập BigQuery
4. Hoặc dùng `--use-cache` để chạy offline

---

### Lỗi 2: Thiếu Etherscan API Key

**Triệu chứng:**
```
[Pillar 1-OS] Lỗi khi lấy mã nguồn...
```

**Giải pháp:**
1. Đăng ký API key tại https://etherscan.io/apis
2. Thêm vào `.env`: `ETHERSCAN_API_KEY=your_key_here`
3. Restart terminal/session

---

### Lỗi 3: Không tìm thấy file ví

**Triệu chứng:**
```
Không tìm thấy tệp danh sách ví tại: data/potential_wallets.csv
```

**Giải pháp:**
1. Tạo file `data/potential_wallets.csv` với cột `wallet_address`
2. Hoặc để trống (framework sẽ skip Sybil analysis)

**Format file:**
```csv
wallet_address
0x1234567890123456789012345678901234567890
0xabcdefabcdefabcdefabcdefabcdefabcdefabcd
```

---

### Lỗi 4: Lỗi Visualization (matplotlib/seaborn)

**Triệu chứng:**
```
Lỗi khi tạo visualizations: ...
```

**Giải pháp:**
```bash
pip install matplotlib seaborn --upgrade
```

Hoặc trên macOS:
```bash
pip install matplotlib seaborn --upgrade --user
```

---

## Tips & Best Practices

### 1. Lần đầu chạy
- Chạy `python run_analysis.py` để query BigQuery và tạo cache
- Kiểm tra output trong console
- Xem Executive Dashboard trong `data/visualizations/executive/`

### 2. Các lần sau
- Dùng `python run_analysis.py --use-cache` để tiết kiệm chi phí
- Chỉ query lại khi cần dữ liệu mới nhất

### 3. So sánh Trước/Sau
```python
# Lưu kết quả trước
previous_results = analysis_service.results.copy()

# Chạy phân tích sau khi có thay đổi
analysis_service.run_full_analysis(...)

# So sánh
comparison_path = analysis_service.compare_with_previous(
    previous_results=previous_results,
    save=True
)
```

### 4. Tùy chỉnh Cấu hình
- Sửa `core/config.py` để thay đổi contract address, campaign date
- Sửa `analysis/advanced_visualization.py` để tùy chỉnh colors/styles

---

## 📞 Hỗ Trợ

Nếu gặp vấn đề, kiểm tra:
1. ✅ Đã cài đặt đầy đủ dependencies (`pip install -r requirements.txt`)
2. ✅ File `.env` đã được tạo và cấu hình đúng
3. ✅ Google Cloud credentials hợp lệ
4. ✅ Etherscan API key hợp lệ
5. ✅ Kết nối internet (nếu query BigQuery)

---

## 🎯 Quick Start

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Tạo file .env với API keys
echo "ETHERSCAN_API_KEY=your_key" > .env
echo "GOOGLE_APPLICATION_CREDENTIALS_PATH=./google-credentials.json" >> .env

# 3. Chạy framework
python run_analysis.py

# 4. Xem kết quả
open data/visualizations/executive/
```

**Chúc bạn phân tích thành công! 🚀**

