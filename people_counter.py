# -*- coding: utf-8 -*-
from tracker.centroidtracker import CentroidTracker
from tracker.trackableobject import TrackableObject
from itertools import zip_longest
from utils.mailer import Mailer
from utils import thread
import numpy as np
import threading
import argparse
import datetime
import schedule
import logging
import time
import json
import csv
import cv2

# thời điểm bắt đầu chạy chương trình
start_time = time.time()

# cấu hình console encoding cho Windows
import sys
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

# cấu hình logger để hiển thị thông tin
logging.basicConfig(level = logging.INFO, format = "[INFO] %(message)s")
logger = logging.getLogger(__name__)
# đọc file cấu hình
with open("utils/config.json", "r") as file:
    config = json.load(file)

def parse_arguments():
	# hàm phân tích tham số dòng lệnh
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--prototxt", default="models/MobileNetSSD_deploy.prototxt",
        help="đường dẫn đến file prototxt của Caffe")
    ap.add_argument("-m", "--model", default="models/MobileNetSSD_deploy.caffemodel",
        help="đường dẫn đến mô hình đã huấn luyện của Caffe")
    ap.add_argument("-i", "--input", type=str,
        help="đường dẫn đến file video tùy chọn")
    ap.add_argument("-o", "--output", type=str,
        help="đường dẫn đến file video đầu ra")
    # độ tin cậy mặc định 0.25 (thấp hơn = phát hiện nhiều hơn)
    ap.add_argument("-c", "--confidence", type=float, default=0.25,
        help="xác suất tối thiểu để lọc các phát hiện yếu")
    ap.add_argument("-s", "--skip-frames", type=int, default=30,
        help="số khung hình bỏ qua giữa các lần phát hiện")
    args = vars(ap.parse_args())
    return args

def send_mail():
	# hàm gửi cảnh báo email
	Mailer().send(config["Email_Receive"])

def log_data(move_in, in_time, move_out, out_time):
	# hàm ghi dữ liệu đếm người
	data = [move_in, in_time, move_out, out_time]
	# chuyển vị dữ liệu để căn chỉnh các cột đúng cách
	export_data = zip_longest(*data, fillvalue = '')

	with open('utils/data/logs/counting_data.csv', 'w', newline = '') as myfile:
		wr = csv.writer(myfile, quoting = csv.QUOTE_ALL)
		if myfile.tell() == 0: # kiểm tra xem header đã tồn tại chưa
			wr.writerow(("Move In", "In Time", "Move Out", "Out Time"))
			wr.writerows(export_data)

def people_counter():
	# hàm chính của people_counter.py
	args = parse_arguments()
	# khởi tạo danh sách nhãn lớp mà MobileNet SSD đã được huấn luyện để phát hiện
	CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
		"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
		"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
		"sofa", "train", "tvmonitor"]

	# tải mô hình đã được serialize từ đĩa
	net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])

	# nếu không có đường dẫn video được cung cấp, lấy tham chiếu đến camera IP
	if not args.get("input", False):
		logger.info("Đang bắt đầu stream trực tiếp..")
		vs = cv2.VideoCapture(config["url"] if config["url"] else 0)
		time.sleep(2.0)

	# ngược lại, lấy tham chiếu đến file video
	else:
		logger.info("Đang bắt đầu video..")
		vs = cv2.VideoCapture(args["input"])

	# khởi tạo video writer (sẽ khởi tạo sau nếu cần)
	writer = None

	# khởi tạo kích thước khung hình (sẽ đặt ngay khi đọc khung hình đầu tiên)
	W = None
	H = None

	# khởi tạo centroid tracker và danh sách trackers, và dictionary để ánh xạ ID đối tượng với TrackableObject
	ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
	trackers = []
	trackableObjects = {}

	# khởi tạo tổng số khung hình đã xử lý và số đối tượng đã di chuyển lên hoặc xuống
	totalFrames = 0
	totalDown = 0
	totalUp = 0
	# khởi tạo danh sách rỗng để lưu dữ liệu đếm
	total = []
	move_out = []
	move_in =[]
	out_time = []
	in_time = []

	# bắt đầu đo tốc độ FPS
	fps_start = time.time()
	fps_frame_count = 0

	if config["Thread"]:
		vs = thread.ThreadingClass(config["url"])

	# lặp qua các khung hình từ stream video
	while True:
		# lấy khung hình tiếp theo và xử lý nếu đang đọc từ VideoCapture hoặc VideoStream
		_, frame = vs.read()

		# nếu đang xem video và không lấy được khung hình thì đã đến cuối video
		if args["input"] is not None and frame is None:
			break

		# resize khung hình để có chiều rộng tối đa 800 pixel để tăng hiệu suất
		h, w = frame.shape[:2]
		if w > 800:
			scale = 800 / w
			frame = cv2.resize(frame, (800, int(h * scale)))
		# Lưu ý: OpenCV tracker làm việc với frame BGR, không cần chuyển sang RGB

		# nếu kích thước khung hình trống, thiết lập chúng
		if W is None or H is None:
			(H, W) = frame.shape[:2]

		# nếu cần ghi video vào đĩa, khởi tạo writer
		if args["output"] is not None and writer is None:
			fourcc = cv2.VideoWriter_fourcc(*"mp4v")
			writer = cv2.VideoWriter(args["output"], fourcc, 30,
				(W, H), True)

		# khởi tạo trạng thái hiện tại và danh sách bounding box hình chữ nhật
		# trả về bởi (1) detector hoặc (2) correlation trackers
		status = "Waiting"
		rects = []

		# kiểm tra xem có nên chạy phương pháp phát hiện đối tượng tốn kém hơn
		# để hỗ trợ tracker không
		if totalFrames % args["skip_frames"] == 0:
			# đặt trạng thái và khởi tạo bộ trackers mới
			status = "Detecting"
			trackers = []

			# chuyển đổi khung hình thành blob và truyền qua mạng để nhận phát hiện
			blob = cv2.dnn.blobFromImage(frame, 0.007843, (W, H), 127.5)
			net.setInput(blob)
			detections = net.forward()

			# lặp qua các phát hiện
			for i in np.arange(0, detections.shape[2]):
				# trích xuất độ tin cậy (xác suất) liên quan đến dự đoán
				confidence = detections[0, 0, i, 2]

				# lọc các phát hiện yếu bằng cách yêu cầu độ tin cậy tối thiểu
				if confidence > args["confidence"]:
					# trích xuất chỉ số của nhãn lớp từ danh sách phát hiện
					idx = int(detections[0, 0, i, 1])

					# nếu nhãn lớp không phải là người, bỏ qua
					if CLASSES[idx] != "person":
						continue

					# tính toán tọa độ (x, y) của bounding box cho đối tượng
					box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
					(startX, startY, endX, endY) = box.astype("int")

					# tạo tracker OpenCV thay vì dlib
					# sử dụng KCF tracker (nhanh và hoạt động với opencv-python cơ bản)
					tracker = cv2.TrackerKCF_create()
					bbox = (startX, startY, endX - startX, endY - startY)
					tracker.init(frame, bbox)

					# thêm tracker vào danh sách để sử dụng trong các khung bỏ qua
					trackers.append(tracker)

		# ngược lại, sử dụng *trackers* thay vì *detectors* để đạt throughput cao hơn
		else:
			# lặp qua các trackers
			for tracker in trackers:
				# đặt trạng thái hệ thống là 'tracking' thay vì 'waiting' hoặc 'detecting'
				status = "Tracking"

				# cập nhật tracker và lấy vị trí đã cập nhật
				success, bbox = tracker.update(frame)
				
				if success:
					# giải nén bbox (x, y, width, height)
					x, y, w, h = bbox
					startX = int(x)
					startY = int(y)
					endX = int(x + w)
					endY = int(y + h)

					# thêm tọa độ bounding box vào danh sách hình chữ nhật
					rects.append((startX, startY, endX, endY))

		# vẽ đường ngang ở giữa khung hình - khi một đối tượng vượt qua đường này
		# ta sẽ xác định chúng đang di chuyển 'lên' hay 'xuống'
		cv2.line(frame, (0, H // 2), (W, H // 2), (0, 255, 0), 3)
		cv2.putText(frame, "-Prediction border - Entrance-", (10, H - 30),
			cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

		# sử dụng centroid tracker để liên kết (1) centroids cũ với (2) centroids mới
		objects = ct.update(rects)

		# lặp qua các đối tượng đang được theo dõi
		for (objectID, centroid) in objects.items():
			# kiểm tra xem đã có trackable object cho ID hiện tại chưa
			to = trackableObjects.get(objectID, None)

			# nếu chưa có trackable object, tạo mới
			if to is None:
				to = TrackableObject(objectID, centroid)

			# ngược lại, đã có trackable object nên có thể sử dụng để xác định hướng
			else:
				# sự khác biệt giữa tọa độ y của centroid *hiện tại* và trung bình
				# của *các centroid trước đó* sẽ cho biết hướng di chuyển
				# (âm cho 'lên', dương cho 'xuống')
				y = [c[1] for c in to.centroids]
				direction = centroid[1] - np.mean(y)
				to.centroids.append(centroid)

				# kiểm tra xem đối tượng đã được đếm chưa
				if not to.counted:
					# nếu hướng âm (đang di chuyển lên) VÀ centroid ở trên đường giữa, đếm là VÀO
					if direction < 0 and centroid[1] < H // 2:
						totalDown += 1
						date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
						move_in.append(totalDown)
						in_time.append(date_time)
						to.counted = True
						# tính tổng số người bên trong
						total = []
						total.append(len(move_in) - len(move_out))
						# nếu giới hạn người vượt quá ngưỡng, gửi cảnh báo email
						if sum(total) >= config["Threshold"]:
							cv2.putText(frame, "-ALERT: People limit exceeded-", (W // 2 - 150, 50),
								cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 3)
							if config["ALERT"]:
								logger.info("Đang gửi cảnh báo email..")
								email_thread = threading.Thread(target = send_mail)
								email_thread.daemon = True
								email_thread.start()
								logger.info("Đã gửi cảnh báo!")

					# nếu hướng dương (đang di chuyển xuống) VÀ centroid ở dưới
					# đường giữa, đếm là RA
					elif direction > 0 and centroid[1] > H // 2:
						totalUp += 1
						date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
						move_out.append(totalUp)
						out_time.append(date_time)
						to.counted = True

			# lưu trackable object vào dictionary
			trackableObjects[objectID] = to

			# chỉ vẽ ID và dot centroid cho mỗi đối tượng
			text = "ID {}".format(objectID)
			
			# vẽ nhãn ID
			cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
			# vẽ dot centroid
			cv2.circle(frame, (centroid[0], centroid[1]), 5, (255, 255, 255), -1)

		# tạo tuple thông tin hiển thị trên khung hình
		info_status = [
		("Enter", totalDown),
		("Exit", totalUp),
		("Status", status),
		]

		info_total = [
		("Total Inside", ', '.join(map(str, total))),
		]

		# hiển thị thông tin ở trên khung hình để dễ nhìn
		y_offset = 30
		for (i, (k, v)) in enumerate(info_status):
			text = "{}: {}".format(k, v)
			cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
			y_offset += 30

		# hiển thị thông tin tổng số người
		if info_total and info_total[0][1]:
			total_text = "{}: {}".format(info_total[0][0], info_total[0][1])
			cv2.putText(frame, total_text, (10, y_offset), 
				cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

		# kích hoạt ghi log đơn giản để lưu dữ liệu đếm
		if config["Log"]:
			log_data(move_in, in_time, move_out, out_time)

		# kiểm tra xem có ghi khung hình vào đĩa không
		if writer is not None:
			writer.write(frame)

		# hiển thị khung hình đầu ra
		cv2.imshow("Real-Time Monitoring/Analysis Window", frame)
		key = cv2.waitKey(1) & 0xFF
		# nếu nhấn phím 'q', thoát khỏi vòng lặp
		if key == ord("q"):
			break
		# tăng tổng số khung hình đã xử lý và cập nhật FPS counter
		totalFrames += 1
		fps_frame_count += 1

		# kích hoạt timer
		if config["Timer"]:
			# timer tự động để dừng stream trực tiếp (đặt 8 giờ/28800s)
			end_time = time.time()
			num_seconds = (end_time - start_time)
			if num_seconds > 28800:
				break

	# dừng timer và hiển thị thông tin FPS
	fps_elapsed = time.time() - fps_start
	logger.info("Thời gian thực thi: {:.2f}".format(fps_elapsed))
	logger.info("FPS xấp xỉ: {:.2f}".format(fps_frame_count / fps_elapsed if fps_elapsed > 0 else 0))

	# giải phóng thiết bị camera/tài nguyên
	if config["Thread"]:
		vs.release()

	# đóng tất cả cửa sổ
	cv2.destroyAllWindows()

# kích hoạt scheduler
if config["Scheduler"]:
	# chạy mỗi ngày (09:00 sáng)
	schedule.every().day.at("09:00").do(people_counter)
	while True:
		schedule.run_pending()
else:
	people_counter()
