# -*- coding: utf-8 -*-
import cv2, threading, queue

class ThreadingClass:
  # khởi tạo lớp threading
  def __init__(self, name):
    self.cap = cv2.VideoCapture(name)
	  # định nghĩa queue và thread trống
    self.q = queue.Queue()
    t = threading.Thread(target=self._reader)
    t.daemon = True
    t.start()

  # đọc các khung hình ngay khi chúng có sẵn
  # phương pháp này loại bỏ buffer nội bộ của OpenCV và giảm độ trễ khung hình
  def _reader(self):
    while True:
      ret, frame = self.cap.read() # đọc các khung hình và ---
      if not ret:
        break
      if not self.q.empty():
        try:
          self.q.get_nowait()
        except queue.Empty:
          pass
      self.q.put(frame) # --- lưu chúng vào queue (thay vì buffer)

  def read(self):
    return self.q.get() # lấy khung hình từ queue từng cái một

  def release(self):
    return self.cap.release() # giải phóng tài nguyên phần cứng
