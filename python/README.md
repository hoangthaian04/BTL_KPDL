# Python Mining Engine

Thư mục này chứa phần mining chạy được ngay:

- `app.py`: entrypoint CLI
- `mining_system/data_io.py`: nạp dữ liệu CSV/XLSX
- `mining_system/preprocessing.py`: làm sạch dữ liệu, tạo feature, encoding, scaling
- `mining_system/training.py`: train, SMOTE thủ công, so sánh mô hình, lưu artifact
- `mining_system/prediction.py`: dự đoán khách hàng mới
- `mining_system/reporting.py`: sinh biểu đồ và dashboard HTML
- `artifacts/`: model, metrics, dashboard, danh sách khách hàng rủi ro cao

Lệnh chạy:

```powershell
python python/app.py train
python python/app.py report
python python/app.py predict --sample-index 0
```
