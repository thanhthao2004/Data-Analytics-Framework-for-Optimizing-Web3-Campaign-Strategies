# Hướng dẫn Visualization - Web3 Campaign Strategy Framework

## Tổng quan

Framework cung cấp **2 cấp độ visualization**:

1. **Standard Visualizations** (`visualization.py`): Các biểu đồ cơ bản cho từng Pillar
2. **Advanced Visualizations** (`advanced_visualization.py`): Các biểu đồ chuyên nghiệp dành cho stakeholders và decision-makers

---

## 📊 Standard Visualizations

### 1. Pillar 1 - Risk Analysis
**File**: `data/visualizations/pillar1/risk_analysis_{address}_{timestamp}.png`

**Nội dung**:
- Risk Score Breakdown: Phân tích đóng góp của Internal Risk (0.4) vs Dependency Risk (0.6)
- Risk Metrics Summary: Tổng hợp các metrics chính (Final Score, Internal, Dependency, Issues)

**Khi nào sử dụng**: Khi cần hiểu chi tiết về rủi ro hợp đồng

---

### 2. Pillar 2 - Gas Forecast
**File**: `data/visualizations/pillar2/gas_forecast_{timestamp}.png`

**Nội dung**:
- Gas Price Forecast: Dự báo 7 ngày với confidence interval
- Model Accuracy Metrics: MAE, RMSE, MAPE, R²
- Model Fit Metrics: AIC, BIC, Log Likelihood
- Reliability Indicators: Đánh giá độ tin cậy của mô hình

**Khi nào sử dụng**: Khi cần đánh giá độ chính xác mô hình và cửa sổ gas tối ưu

---

### 3. Pillar 3 - User Behavior
**File**: `data/visualizations/pillar3/user_analysis_{date}_{timestamp}.png`

**Nội dung**:
- Peak Activity Hour: Giờ hoạt động cao điểm của người dùng (0-23h UTC)
- Sybil Clusters: Phân tích các cụm nghi vấn
- Cohort Retention Analysis: Tỷ lệ giữ chân người dùng (Day 1, 7, 30)

**Khi nào sử dụng**: Khi cần hiểu hành vi người dùng và chất lượng user base

---

### 4. Before/After Comparison
**File**: `data/visualizations/comparison/comparison_{timestamp}.png`

**Nội dung**:
- So sánh Risk Score trước và sau
- So sánh Gas Price trước và sau
- So sánh Peak Activity Hour trước và sau
- Summary của các thay đổi

**Khi nào sử dụng**: Khi cần đánh giá hiệu quả của các thay đổi chiến lược

---

## 🎯 Advanced Visualizations (Professional)

### 1. Executive Dashboard ⭐ **QUAN TRỌNG NHẤT**
**File**: `data/visualizations/executive/executive_dashboard_{timestamp}.png`

**Đây là biểu đồ quan trọng nhất** cho stakeholders và decision-makers.

**Layout**:
- **Top Row (KPIs)**:
  - Risk Score Gauge: Speedometer-style gauge với thresholds
  - Estimated Gas Price Card
  - Peak Activity Hour Card
  - Overall Recommendation Card
  
- **Middle Section**:
  - Risk Waterfall Breakdown: Chi tiết các thành phần risk
  - Gas Forecast Timeline: Với optimal window highlighted
  - Dependency Network Graph: Visualize các dependencies
  
- **Bottom Section**:
  - User Engagement Analysis: Peak activity + Cohort retention
  - Cost-Benefit Matrix: Gas Cost vs User Activity
  - Strategic Insights: Tóm tắt các khuyến nghị quan trọng

**Khi nào sử dụng**: 
- **Báo cáo cho C-level executives**
- **Presentation cho investors**
- **Strategic planning meetings**
- **Documentation cho compliance/audit**

---

### 2. Trade-off Analysis
**File**: `data/visualizations/advanced/tradeoff_analysis_{timestamp}.png`

**Nội dung**:
- **Pareto Frontier**: Tìm các điểm optimal giữa Gas Cost và User Engagement
- **3D Trade-off Surface**: Mối quan hệ 3 chiều (Hour, Day, Optimality Score)

**Khi nào sử dụng**:
- Khi cần quyết định trade-off giữa chi phí và ROI
- Phân tích multi-objective optimization
- Tìm điểm cân bằng tối ưu

---

### 3. Risk Heatmap
**File**: `data/visualizations/advanced/risk_heatmap_{address}_{timestamp}.png`

**Nội dung**:
- **Risk Matrix**: Severity vs Likelihood matrix (5x5)
- **Risk Timeline**: Evolution của risk over time (nếu có historical data)

**Khi nào sử dụng**:
- Đánh giá rủi ro tổng hợp
- So sánh với industry standards
- Risk assessment reports

---

## 🚀 Cách sử dụng

### Tạo Standard Visualizations

```python
from analysis.analysis_service import AnalysisService

# Sau khi chạy phân tích
analysis_service.run_full_analysis(...)

# Tạo visualizations
paths = analysis_service.visualize_results(
    contract_address="0x...",
    campaign_start_date="2025-06-23",
    save=True
)
```

### Tạo Executive Dashboard

```python
# Tạo Executive Dashboard (quan trọng nhất)
dashboard_path = analysis_service.create_executive_dashboard(
    contract_address="0x...",
    campaign_start_date="2025-06-23",
    save=True
)
```

### Tạo Advanced Visualizations

```python
# Tạo tất cả advanced visualizations
advanced_paths = analysis_service.create_advanced_visualizations(
    contract_address="0x...",
    save=True
)
```

### So sánh Trước/Sau

```python
# Lưu kết quả trước
previous_results = analysis_service.results.copy()

# Chạy phân tích lại sau khi có thay đổi
analysis_service.run_full_analysis(...)

# So sánh
comparison_path = analysis_service.compare_with_previous(
    previous_results=previous_results,
    save=True
)
```

---

## 💡 Best Practices

### Cho Executive Reports:
1. **Luôn sử dụng Executive Dashboard** - đây là tool chính
2. Kèm theo **Risk Heatmap** nếu có concerns về bảo mật
3. Thêm **Trade-off Analysis** nếu cần quyết định về timing

### Cho Technical Teams:
1. Sử dụng **Standard Visualizations** cho từng Pillar
2. Focus vào **Model Accuracy Metrics** trong Pillar 2
3. Xem **Cohort Analysis** chi tiết trong Pillar 3

### Cho Strategic Planning:
1. **Executive Dashboard** cho overview
2. **Trade-off Analysis** cho optimization
3. **Before/After Comparison** để track improvements

---

## 📁 Cấu trúc Thư mục

```
data/visualizations/
├── pillar1/           # Risk analysis charts
├── pillar2/           # Gas forecast charts
├── pillar3/           # User behavior charts
├── comparison/        # Before/after comparisons
├── advanced/          # Advanced professional charts
└── executive/         # Executive dashboards (⭐ quan trọng nhất)
```

---

## 🎨 Design Principles

Các visualizations được thiết kế dựa trên:

1. **Clarity**: Thông tin rõ ràng, dễ hiểu
2. **Professional**: Style nhất quán, phù hợp cho báo cáo
3. **Insightful**: Tự động highlight các insights quan trọng
4. **Actionable**: Hỗ trợ quyết định chiến lược

---

## 📝 Notes

- Tất cả charts được lưu ở **300 DPI** - chất lượng cao cho printing
- Format: PNG với transparent background (nếu cần)
- Timestamp tự động để track version history
- Có thể customize colors và styles trong `advanced_visualization.py`

