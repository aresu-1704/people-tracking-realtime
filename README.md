# People Tracking Real-time

Dự án đếm người vào/ra thời gian thực sử dụng mô hình học sâu MobileNet SSD với khả năng theo dõi và phân tích chuyển động.

## 📹 Video Demo

Video output mẫu có trong file `output.mp4` trong thư mục gốc của dự án.

## 🎯 Tính năng chính

- ✅ Phát hiện và theo dõi người trong thời gian thực
- ✅ Đếm số người vào/ra tự động
- ✅ Hiển thị số người hiện tại trong khu vực giám sát
- ✅ Gửi cảnh báo email khi số người vượt ngưỡng cho phép
- ✅ Ghi log dữ liệu đếm vào file CSV
- ✅ Hỗ trợ camera IP hoặc video file
- ✅ Tối ưu hiệu suất với threading
- ✅ Scheduler tự động chạy theo lịch

## 📋 Yêu cầu hệ thống

- Python 3.7 trở lên
- OpenCV với contrib modules
- NumPy, SciPy
- Schedule

## 🚀 Cài đặt

### Windows

1. **Tự động (Khuyến nghị):**
   ```bash
   setup.bat
   ```
   Tập lệnh này sẽ tự động tạo môi trường ảo và cài đặt các dependency.

2. **Thủ công:**
   ```bash
   # Tạo môi trường ảo
   python -m venv .venv
   
   # Kích hoạt môi trường ảo
   .venv\Scripts\activate
   
   # Cài đặt dependencies
   pip install -r requirements.txt
   ```

### Linux/Mac

```bash
# Tạo và kích hoạt môi trường ảo
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

## 💻 Sử dụng

### Chạy với video file (Windows)

Sử dụng file batch có sẵn:
```bash
tracking.bat
```

Hoặc chạy trực tiếp với Python:
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

2. Chạy chương trình:
```bash
python people_counter.py
```

### Chạy với webcam

```bash
python people_counter.py
```

### Các tham số

| Tham số | Mô tả | Mặc định |
|---------|-------|----------|
| `-p, --prototxt` | Đường dẫn đến file prototxt | `models/MobileNetSSD_deploy.prototxt` |
| `-m, --model` | Đường dẫn đến file model | `models/MobileNetSSD_deploy.caffemodel` |
| `-i, --input` | Đường dẫn đến video file (tùy chọn) | Camera mặc định |
| `-o, --output` | Đường dẫn lưu video output | Không lưu |
| `-c, --confidence` | Ngưỡng confidence (0.0-1.0) | 0.25 |
| `-s, --skip-frames` | Số frame bỏ qua giữa các lần detect | 30 |
| `q` | Nhấn phím 'q' để thoát | - |

### Ví dụ sử dụng

```bash
# Xử lý video với confidence cao hơn
python people_counter.py -i input.mp4 -o output.mp4 -c 0.5

# Xử lý video với tần suất detect cao hơn
python people_counter.py -i input.mp4 -o output.mp4 -s 15

# Chạy từ camera với các tùy chọn tùy chỉnh
python people_counter.py -c 0.3 -s 30
```

## ⚙️ Cấu hình

Chỉnh sửa file `utils/config.json` để cấu hình:

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

### Các tham số cấu hình

- **Email_Send**: Email người gửi
- **Email_Receive**: Email người nhận cảnh báo
- **Email_Password**: Mật khẩu email (nên sử dụng App Password)
- **url**: URL camera IP hoặc luồng video
- **ALERT**: Bật/tắt gửi cảnh báo email (`true`/`false`)
- **Threshold**: Số người tối đa cho phép (trigger cảnh báo)
- **Thread**: Sử dụng threading để tăng hiệu suất (`true`/`false`)
- **Log**: Ghi log dữ liệu vào CSV (`true`/`false`)
- **Scheduler**: Chạy theo lịch tự động (`true`/`false`)
- **Timer**: Tự động dừng sau 8 giờ (`true`/`false`)

## 📊 Dữ liệu Log

Khi bật tính năng Log, dữ liệu sẽ được ghi vào file `utils/data/logs/counting_data.csv` với các cột:
- Move In: Số người vào
- In Time: Thời gian vào
- Move Out: Số người ra
- Out Time: Thời gian ra

## 📁 Cấu trúc dự án

```
people-tracking-realtime/
├── models/                          # Mô hình MobileNet SSD
│   ├── MobileNetSSD_deploy.prototxt
│   └── MobileNetSSD_deploy.caffemodel
├── tracker/                         # Module theo dõi
│   ├── centroidtracker.py
│   └── trackableobject.py
├── utils/                           # Utilities
│   ├── config.json                 # File cấu hình
│   ├── mailer.py                   # Module gửi email
│   ├── thread.py                    # Module threading
│   └── data/
│       └── test.mov               # Video mẫu
├── people_counter.py               # File chính
├── requirements.txt                # Dependencies
├── setup.bat                       # Script cài đặt Windows
├── setup.sh                        # Script cài đặt Linux/Mac
├── tracking.bat                    # Script chạy demo
├── output.mp4                      # Video output mẫu
└── README.md                       # File hướng dẫn này
```

## 🔧 Xử lý lỗi

### Lỗi "Cannot find opencv"

```bash
pip uninstall opencv-python
pip install opencv-contrib-python
```

### Lỗi encoding trên Windows

Chương trình đã tự động xử lý encoding UTF-8 trên Windows.

### Hiệu suất chậm

- Giảm `--skip-frames` xuống (ví dụ: từ 30 xuống 15)
- Tăng `--confidence` lên để filter nhiều hơn
- Bật `Thread: true` trong config

## 📝 Lưu ý

- Đường line ngang giữa khung hình là "border prediction" để xác định vào/ra
- Người di chuyển từ dưới lên trên đường line = **RA**
- Người di chuyển từ trên xuống dưới đường line = **VÀO**
- Nhấn phím `q` để thoát chương trình bất cứ lúc nào

## 📄 License

Dự án này sử dụng mã nguồn mở.

## 👤 Tác giả

Dự án phát triển cho mục đích giám sát và phân tích lưu lượng người.

---

**Chúc bạn sử dụng thành công!** 🎉
