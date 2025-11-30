# People Tracking Real-time

Dự án đếm người vào/ra thời gian thực sử dụng mô hình MobileNet SSD.

## Demo

![Demo](assets/output.gif)

## Tính năng

- Phát hiện và theo dõi người trong thời gian thực
- Đếm số người vào/ra tự động
- Hiển thị số người hiện tại trong khu vực giám sát
- Gửi cảnh báo email khi số người vượt ngưỡng cho phép
- Ghi log dữ liệu đếm vào file CSV
- Hỗ trợ camera IP hoặc video file
- Tối ưu hiệu suất với threading
- Scheduler tự động chạy theo lịch

## Yêu cầu

- Python 3.7+
- OpenCV với contrib modules
- NumPy, SciPy
- Schedule

## Cài đặt

### Windows

Tự động:
```bash
setup.bat
```

Thủ công:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux/Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Sử dụng

### Chạy với video file

Windows:
```bash
tracking.bat
```

Hoặc:
```bash
python people_counter.py -i utils/data/test.mov -o output.mp4
```

### Chạy với camera IP

1. Cấu hình URL camera trong `utils/config.json`:
```json
{
    "url": "rtsp://your-ip-camera-url"
}
```

2. Chạy:
```bash
python people_counter.py
```

### Chạy với webcam

```bash
python people_counter.py
```

### Tham số

| Tham số | Mô tả | Mặc định |
|---------|-------|----------|
| `-p, --prototxt` | Đường dẫn file prototxt | `models/MobileNetSSD_deploy.prototxt` |
| `-m, --model` | Đường dẫn file model | `models/MobileNetSSD_deploy.caffemodel` |
| `-i, --input` | Đường dẫn video file | Camera mặc định |
| `-o, --output` | Đường dẫn lưu video output | Không lưu |
| `-c, --confidence` | Ngưỡng confidence (0.0-1.0) | 0.25 |
| `-s, --skip-frames` | Số frame bỏ qua giữa các lần detect | 30 |

### Ví dụ

```bash
# Xử lý video với confidence cao hơn
python people_counter.py -i input.mp4 -o output.mp4 -c 0.5

# Xử lý video với tần suất detect cao hơn
python people_counter.py -i input.mp4 -o output.mp4 -s 15

# Chạy từ camera với tùy chọn tùy chỉnh
python people_counter.py -c 0.3 -s 30
```

## Cấu hình

Chỉnh sửa file `utils/config.json`:

```json
{
    "Email_Send": "sender@example.com",
    "Email_Receive": "receiver@example.com",
    "Email_Password": "your_password",
    "url": "rtsp://camera-url",
    "ALERT": true,
    "Threshold": 10,
    "Thread": true,
    "Log": true,
    "Scheduler": false,
    "Timer": false
}
```

**Các tham số:**
- `Email_Send`: Email người gửi
- `Email_Receive`: Email người nhận cảnh báo
- `Email_Password`: Mật khẩu email (nên dùng App Password)
- `url`: URL camera IP hoặc luồng video
- `ALERT`: Bật/tắt gửi cảnh báo email
- `Threshold`: Số người tối đa cho phép
- `Thread`: Sử dụng threading để tăng hiệu suất
- `Log`: Ghi log dữ liệu vào CSV
- `Scheduler`: Chạy theo lịch tự động
- `Timer`: Tự động dừng sau 8 giờ

## Dữ liệu Log

Khi bật tính năng Log, dữ liệu được ghi vào `utils/data/logs/counting_data.csv`:
- Move In: Số người vào
- In Time: Thời gian vào
- Move Out: Số người ra
- Out Time: Thời gian ra

## Cấu trúc dự án

```
people-tracking-realtime/
├── models/
│   ├── MobileNetSSD_deploy.prototxt
│   └── MobileNetSSD_deploy.caffemodel
├── tracker/
│   ├── centroidtracker.py
│   └── trackableobject.py
├── utils/
│   ├── config.json
│   ├── mailer.py
│   ├── thread.py
│   └── data/
│       └── test.mov
├── people_counter.py
├── requirements.txt
├── setup.bat
├── setup.sh
├── tracking.bat
└── README.md
```

## Xử lý lỗi

**Lỗi "Cannot find opencv":**
```bash
pip uninstall opencv-python
pip install opencv-contrib-python
```

**Lỗi encoding trên Windows:**
Chương trình đã tự động xử lý encoding UTF-8.

**Hiệu suất chậm:**
- Giảm `--skip-frames` (ví dụ: từ 30 xuống 15)
- Tăng `--confidence` để filter nhiều hơn
- Bật `Thread: true` trong config

## Lưu ý

- Đường line ngang giữa khung hình là "border prediction" để xác định vào/ra
- Người di chuyển từ dưới lên trên đường line = RA
- Người di chuyển từ trên xuống dưới đường line = VÀO
- Nhấn phím `q` để thoát chương trình
