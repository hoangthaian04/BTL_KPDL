# Airflow Workflow

Thư mục này bổ sung phần orchestration theo yêu cầu đề bài cho hệ thống `BTL_KPDL`.

## DAG hiện có

- `telco_churn_training_pipeline`
- chạy theo lịch `02:00` mỗi ngày
- kiểm tra dataset `Telco_customer_churn.xlsx`
- so sánh `sha256` với lần chạy trước
- chỉ retrain khi dữ liệu thay đổi, hoặc khi trigger với `{"force_retrain": true}`
- gọi lại pipeline hiện có: `python/app.py --data <dataset> train`
- tự quét thư mục `python/incoming_data/` để nhập các file CSV/XLSX mới trước khi kiểm tra dataset
- xác thực các artifact sau train
- lưu manifest chạy vào `airflow/state/`

## Artifact được kiểm tra

- `python/artifacts/training_summary.json`
- `python/artifacts/metrics.csv`
- `python/artifacts/high_risk_customers.csv`
- `python/artifacts/dashboard.html`
- `python/artifacts/best_model.pkl`
- `python/artifacts/charts/*.png`

## Chạy bằng Docker

Repo này đã có sẵn:

- `docker-compose.airflow.yml`
- `airflow/Dockerfile`
- `docker-compose.yml` cho full stack `mysql + backend + react`

Từ thư mục gốc `BTL_KPDL`, chạy:

```bash
docker compose -f docker-compose.airflow.yml up airflow-init
docker compose -f docker-compose.airflow.yml up -d
```

Sau khi chạy:

- Airflow UI: `http://localhost:8088`
- tài khoản mặc định: `admin / admin`

Stack Docker gồm:

- `postgres`: metadata database cho Airflow
- `airflow-init`: khởi tạo DB và tạo user admin
- `airflow-webserver`: giao diện Airflow
- `airflow-scheduler`: scheduler chạy DAG

Image Airflow đã được build kèm dependency của pipeline Python trong `python/requirements.txt`, nên DAG có thể gọi trực tiếp pipeline train hiện tại.

## Chạy full stack ứng dụng

Nếu muốn chạy luôn hệ thống chính bằng Docker:

```bash
docker compose up --build -d
```

Sau khi chạy:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8080`
- MySQL: `localhost:3306`

Trong stack này, backend container đã được cài sẵn Python và copy thư mục `python/`, nên backend có thể gọi trực tiếp `python/app.py` để train và predict.

## Trigger thủ công bằng Docker

```bash
docker compose -f docker-compose.airflow.yml exec airflow-webserver airflow dags trigger telco_churn_training_pipeline --conf "{\"force_retrain\": true}"
```

## Tự động nạp dữ liệu mới

Nếu muốn hệ thống tự nhận file mới, chỉ cần thả file `csv/xlsx/xlsm` vào:

```bash
python/incoming_data/
```

Ở lần chạy DAG kế tiếp, Airflow sẽ:

- import các file này vào `Telco_customer_churn.xlsx`
- chuyển file đã xử lý sang `python/incoming_data/processed/`
- kiểm tra lại hash dataset
- retrain nếu dataset thực sự đã thay đổi

## Dừng và dọn

```bash
docker compose -f docker-compose.airflow.yml down
```

Xóa luôn volume metadata:

```bash
docker compose -f docker-compose.airflow.yml down -v
```

## Chạy không dùng Docker

Airflow chạy ổn định hơn trên Linux/WSL/Docker. Với máy Windows, nên dùng WSL2 hoặc Docker thay vì chạy native.

Ví dụ nhanh:

```bash
pip install -r airflow/requirements.txt
set AIRFLOW_HOME=%CD%\airflow\.airflow
airflow db migrate
airflow standalone
```

Thiết lập thêm nếu cần:

- DAG folder: `BTL_KPDL/airflow/dags`
- biến môi trường tùy chọn: `MINING_PYTHON_EXECUTABLE`

Ví dụ:

```bash
set MINING_PYTHON_EXECUTABLE=python
```

## Ghi chú tích hợp

- DAG này không thay thế Java backend hay React frontend.
- Nó điều phối lại pipeline Python hiện có để phục vụ yêu cầu retrain định kỳ, retrain khi dữ liệu thay đổi và lưu log các lần chạy.
