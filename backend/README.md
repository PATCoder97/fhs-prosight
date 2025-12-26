# Backend Setup Guide

## Prerequisites
- Python 3.11 hoặc cao hơn
- pip (package manager)

---

## Windows

### 1. Tạo môi trường ảo (Virtual Environment)
```bash
py -m venv venv
```

### 2. Kích hoạt môi trường ảo
```bash
.\venv\Scripts\Activate
```

Sau khi kích hoạt, terminal sẽ hiển thị `(venv)` ở đầu dòng.

### 3. Cài đặt các thư viện
```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng
```bash
uvicorn app.main:app --reload --port 8001
```

Ứng dụng sẽ chạy tại: `http://localhost:8001`

### 5. Dừng ứng dụng
Nhấn `Ctrl + C` trong terminal

### 6. Thoát khỏi môi trường ảo
```bash
deactivate
```

---

## Ubuntu / Linux / macOS

### 1. Tạo môi trường ảo (Virtual Environment)
```bash
python3.11 -m venv venv
```

Hoặc nếu bạn dùng `python3`:
```bash
python3 -m venv venv
```

### 2. Kích hoạt môi trường ảo
```bash
source venv/bin/activate
```

Sau khi kích hoạt, terminal sẽ hiển thị `(venv)` ở đầu dòng.

### 3. Cài đặt các thư viện
```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng
```bash
uvicorn app.main:app --reload --port 8001
```

Ứng dụng sẽ chạy tại: `http://localhost:8001`

### 5. Dừng ứng dụng
Nhấn `Ctrl + C` trong terminal

### 6. Thoát khỏi môi trường ảo
```bash
deactivate
```

---

## Lưu ý chung
- Luôn kích hoạt virtual environment trước khi cài đặt hoặc chạy ứng dụng
- Thư mục `venv/` không nên commit vào version control (đã được ignore bởi `.gitignore`)
- Để cài thêm thư viện, hãy sử dụng: `pip install <package-name>`
