# Java Backend

Backend Spring Boot này làm cầu nối giữa React và Python mining engine.

Chức năng hiện có:

- `POST /api/models/train`: gọi Python train model
- `GET /api/dashboard/summary`: đọc `training_summary.json`
- `POST /api/predictions`: gửi dữ liệu khách hàng sang Python để dự đoán
- tự động ghi MySQL:
  - bảng `customers`
  - bảng `predictions`
  - bảng `training_runs`

Các file chính:

- `pom.xml`: cấu hình Maven
- `src/main/java/.../controller`: REST API
- `src/main/java/.../service`: gọi Python và đọc artifact
- `src/main/java/.../entity`: entity JPA
- `src/main/java/.../repository`: repository JPA
- `src/main/resources/application.yml`: đường dẫn tích hợp với thư mục `python`

Luồng tích hợp:

1. React gọi API Spring Boot
2. Spring Boot gọi `python/app.py`
3. Python train hoặc predict
4. Spring Boot trả kết quả JSON cho React

MySQL mặc định:

- host: `localhost`
- port: `3306`
- database: `BTL_data_mining`
- username: `root`
- password: `123456`

Spring Boot dùng `createDatabaseIfNotExist=true` và `ddl-auto=update`, nên sẽ tự tạo database nếu chưa có và tự tạo/cập nhật bảng.
