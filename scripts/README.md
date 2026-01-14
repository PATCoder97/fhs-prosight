# Scripts Directory - FHS ProSight

Thư mục này chứa các utility scripts để quản lý Docker deployment và operations.

## Available Scripts

### 1. check-docker-env.sh
**Mục đích**: Kiểm tra môi trường trước khi build Docker images

**Cách dùng**:
```bash
./scripts/check-docker-env.sh
```

**Kiểm tra**:
- Docker và Docker Compose đã cài đặt
- Docker daemon đang chạy
- File .env tồn tại và có đầy đủ biến môi trường
- File firebase_credentials.json tồn tại
- Các Dockerfile và docker-compose.yml tồn tại
- Dung lượng ổ đĩa còn trống

### 2. deploy.sh
**Mục đích**: Deploy nhanh toàn bộ ứng dụng

**Cách dùng**:
```bash
./scripts/deploy.sh
```

**Các bước thực hiện**:
1. Pull code mới nhất từ Git
2. Stop containers hiện tại
3. Build Docker images (no cache)
4. Start services
5. Kiểm tra health status
6. Hiển thị thông tin containers

### 3. backup-db.sh
**Mục đích**: Backup database PostgreSQL

**Cách dùng**:
```bash
./scripts/backup-db.sh
```

**Tính năng**:
- Tạo backup file với timestamp
- Nén backup file (gzip)
- Tự động giữ lại 7 backups gần nhất
- Hiển thị kích thước file backup

**Output**: `backups/fhs_prosight_backup_YYYYMMDD_HHMMSS.sql.gz`

### 4. restore-db.sh
**Mục đích**: Restore database từ backup

**Cách dùng**:
```bash
./scripts/restore-db.sh backups/fhs_prosight_backup_20260114_120000.sql.gz
```

**Lưu ý**:
- Script sẽ hỏi xác nhận trước khi restore
- Tự động decompress file .gz nếu cần
- **CẢNH BÁO**: Sẽ overwrite database hiện tại!

### 5. health-monitor.sh
**Mục đích**: Giám sát health status của các services

**Cách dùng**:
```bash
# Mặc định check mỗi 30 giây
./scripts/health-monitor.sh

# Custom interval (60 giây)
./scripts/health-monitor.sh 60
```

**Giám sát**:
- Container status (running/stopped)
- HTTP health check endpoints
- Resource usage (CPU, Memory, Network)
- Alert khi có failures

**Dừng monitoring**: Press `Ctrl+C`

## Setup

Cấp quyền thực thi cho các scripts:

```bash
chmod +x scripts/*.sh
```

Hoặc từng file:

```bash
chmod +x scripts/check-docker-env.sh
chmod +x scripts/deploy.sh
chmod +x scripts/backup-db.sh
chmod +x scripts/restore-db.sh
chmod +x scripts/health-monitor.sh
```

## Workflow Recommendations

### Development

```bash
# 1. Kiểm tra môi trường
./scripts/check-docker-env.sh

# 2. Deploy
./scripts/deploy.sh

# 3. Monitor (optional)
./scripts/health-monitor.sh
```

### Production

```bash
# 1. Backup database trước khi deploy
./scripts/backup-db.sh

# 2. Deploy phiên bản mới
./scripts/deploy.sh

# 3. Monitor services
./scripts/health-monitor.sh 60
```

### Disaster Recovery

```bash
# List available backups
ls -lh backups/

# Restore from backup
./scripts/restore-db.sh backups/fhs_prosight_backup_YYYYMMDD_HHMMSS.sql.gz
```

## Environment Variables

Scripts sử dụng các biến môi trường từ file `.env`:

- `DB_HOST` - Database host
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password

## Troubleshooting

### Script không chạy được

```bash
# Kiểm tra quyền
ls -la scripts/

# Cấp quyền thực thi
chmod +x scripts/*.sh
```

### Backup/Restore lỗi

```bash
# Kiểm tra PostgreSQL client tools
which pg_dump
which psql

# Cài đặt nếu chưa có (Ubuntu/Debian)
sudo apt-get install postgresql-client

# Cài đặt nếu chưa có (macOS)
brew install postgresql
```

### Health monitor không hoạt động

```bash
# Kiểm tra curl
which curl

# Cài đặt curl (Ubuntu/Debian)
sudo apt-get install curl

# Kiểm tra Docker
docker ps
docker-compose ps
```

## Notes

- Tất cả scripts đều có error handling (`set -e`)
- Output có màu sắc để dễ đọc (Green/Yellow/Red)
- Backup files được tự động cleanup (giữ 7 bản gần nhất)
- Health monitor có threshold để phát hiện sự cố liên tục

---

**Tác giả**: TP75
**Cập nhật**: 2026-01-14
