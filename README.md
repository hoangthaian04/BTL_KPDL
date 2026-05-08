# BTL_KPDL

Hệ thống mining dự đoán `customer churn` cho bài tập lớn khai phá dữ liệu.

Project gồm 4 phần:

- `python/`: pipeline tiền xử lý, train model, predict, sinh artifact
- `java/`: Spring Boot backend, gọi Python và lưu MySQL
- `react/`: dashboard hiển thị metric, chart, predict và import dữ liệu
- `airflow/`: retrain theo lịch, kiểm tra thay đổi dataset, tự nạp file mới

## Chức năng chính

- train nhiều model và chọn model tốt nhất
- dùng SMOTE để cân bằng tập train
- predict một khách hàng mới
- import file dữ liệu mới vào dataset gốc
- xuất danh sách khách hàng:
  - cần chăm sóc: `0.5 < probability < 0.8`
  - nguy cơ cao: `probability >= 0.8`
- retrain thủ công trên giao diện
- retrain theo lịch bằng Airflow
- auto-ingest dữ liệu mới từ `python/incoming_data/`

## Yêu cầu

- Docker Desktop
- Git

Không cần cài riêng Java, Python, Node nếu chạy bằng Docker.

## Chạy nhanh toàn hệ thống

Từ thư mục gốc repo:

```bash
docker compose up --build -d
```

Sau khi chạy:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8081`
- Airflow: `http://localhost:8088`
- MySQL trên máy host: `localhost:3307`

Tài khoản Airflow mặc định:

- username: `admin`
- password: `admin`

## Dừng hệ thống

```bash
docker compose down
```

Xóa luôn volume database:

```bash
docker compose down -v
```

## Luồng demo đề xuất

1. Mở frontend tại `http://localhost:5173`
2. Xem dashboard metric, chart, danh sách risk
3. Dùng `Predict One Customer` để dự đoán khách mới
4. Dùng `Import New Dataset File` để thêm file dữ liệu mới vào dataset gốc
5. Bấm `Retrain model` để train lại ngay
6. Mở Airflow tại `http://localhost:8088` để xem DAG retrain theo lịch

## Dataset và artifact

Dataset gốc dùng để train:

- `Telco_customer_churn.xlsx`

File này đang được ignore khỏi Git nên không được đẩy lên repo.

Artifact sau train nằm ở:

- `python/artifacts/training_summary.json`
- `python/artifacts/metrics.csv`
- `python/artifacts/high_risk_customers.csv`
- `python/artifacts/high_risk_customers.xlsx`
- `python/artifacts/care_customers.csv`
- `python/artifacts/care_customers.xlsx`
- `python/artifacts/dashboard.html`
- `python/artifacts/charts/`

## Import dữ liệu mới

Có 2 cách đưa dữ liệu mới vào dataset gốc:

1. Qua giao diện:
   - dùng panel `Import New Dataset File`
   - chấp nhận `csv`, `xlsx`, `xlsm`

2. Qua Airflow auto-ingest:
   - thả file vào `python/incoming_data/`
   - ở lần chạy DAG kế tiếp, Airflow sẽ:
     - nhập file vào dataset gốc
     - chuyển file đã xử lý sang `python/incoming_data/processed/`
     - kiểm tra lại hash dataset
     - retrain nếu dữ liệu thay đổi

## Retrain model

Có 2 cơ chế retrain:

1. Thủ công trên giao diện
   - luôn train ngay khi bấm nút

2. Theo lịch bằng Airflow
   - DAG: `telco_churn_training_pipeline`
   - mặc định kiểm tra dataset có đổi không rồi mới train
   - có thể trigger thủ công trong Airflow

Trigger DAG bằng CLI:

```bash
docker compose exec airflow-webserver airflow dags trigger telco_churn_training_pipeline
```

Force retrain:

```bash
docker compose exec airflow-webserver airflow dags trigger telco_churn_training_pipeline --conf "{\"force_retrain\": true}"
```

## Ghi chú Airflow

Airflow chạy trong cùng `docker-compose.yml` với các service:

- `postgres`
- `airflow-init`
- `airflow-webserver`
- `airflow-scheduler`

URL truy cập:

- `http://localhost:8088`

Tài khoản mặc định:

- username: `admin`
- password: `admin`

Nếu `docker compose up --build -d` xong mà không mở được Airflow, chạy lần lượt:

```bash
docker compose ps
docker compose logs airflow-init
docker compose logs airflow-webserver
docker compose logs airflow-scheduler
```

Ý nghĩa:

- `airflow-init`: kiểm tra DB migrate và tạo user `admin`
- `airflow-webserver`: kiểm tra web UI có lên không
- `airflow-scheduler`: kiểm tra scheduler có nhận DAG không

Nếu cần khởi động lại riêng Airflow:

```bash
docker compose restart airflow-init airflow-webserver airflow-scheduler
```

Nếu vẫn lỗi, dừng rồi chạy lại toàn bộ:

```bash
docker compose down
docker compose up --build -d
```

Nếu nghi ngờ lỗi volume hoặc metadata cũ:

```bash
docker compose down -v
docker compose up --build -d
```

Nếu chỉ muốn bật lại Airflow sau khi stack đã chạy:

```bash
docker compose up -d postgres airflow-init airflow-webserver airflow-scheduler
```

Kiểm tra DAG trong container:

```bash
docker compose exec airflow-webserver airflow dags list
```

Kiểm tra user đã được tạo chưa:

```bash
docker compose exec airflow-webserver airflow users list
```

## Cấu trúc thư mục

- `docker-compose.yml`: chạy full stack
- `docker-compose.airflow.yml`: stack Airflow riêng
- `python/`: mining engine
- `java/`: backend
- `react/`: frontend
- `airflow/`: DAG và cấu hình Airflow

## Ghi chú

- Backend hiện gọi Python trực tiếp bằng subprocess, nên container backend đã cài sẵn Python.
- Khách hàng vừa predict sẽ được thêm vào dataset gốc dưới dạng bản ghi chưa có nhãn churn.
- SMOTE chỉ áp dụng trên tập train trong bộ nhớ, không làm thay đổi dataset gốc.
- Nếu đổi code liên quan backend/frontend/python, nên chạy lại:

```bash
docker compose up --build -d
```

## README thành phần

- [python/README.md](./python/README.md)
- [java/README.md](./java/README.md)
- [react/README.md](./react/README.md)
- [airflow/README.md](./airflow/README.md)
