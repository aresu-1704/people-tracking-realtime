# -*- coding: utf-8 -*-
# import các thư viện cần thiết
from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np

class CentroidTracker:
	def __init__(self, maxDisappeared=50, maxDistance=50):
		# khởi tạo ID đối tượng duy nhất tiếp theo cùng với hai dictionary
		# dùng để theo dõi ánh xạ ID đối tượng với centroid và số khung hình
		# liên tiếp nó bị đánh dấu là "biến mất", tương ứng
		self.nextObjectID = 0
		self.objects = OrderedDict()
		self.disappeared = OrderedDict()

		# lưu số khung hình liên tiếp tối đa một đối tượng được phép
		# bị đánh dấu là "biến mất" cho đến khi cần hủy đăng ký khỏi theo dõi
		self.maxDisappeared = maxDisappeared

		# lưu khoảng cách tối đa giữa các centroid để liên kết
		# một đối tượng -- nếu khoảng cách lớn hơn tối đa này
		# ta sẽ bắt đầu đánh dấu đối tượng là "biến mất"
		self.maxDistance = maxDistance

	def register(self, centroid):
		# khi đăng ký một đối tượng ta sử dụng ID đối tượng khả dụng tiếp theo
		# để lưu centroid
		self.objects[self.nextObjectID] = centroid
		self.disappeared[self.nextObjectID] = 0
		self.nextObjectID += 1

	def deregister(self, objectID):
		# để hủy đăng ký một ID đối tượng ta xóa ID khỏi cả hai dictionary tương ứng
		del self.objects[objectID]
		del self.disappeared[objectID]

	def update(self, rects):
		# kiểm tra xem danh sách bounding box hình chữ nhật đầu vào có trống không
		if len(rects) == 0:
			# lặp qua các đối tượng đang được theo dõi và đánh dấu chúng
			# là biến mất
			for objectID in list(self.disappeared.keys()):
				self.disappeared[objectID] += 1

				# nếu đã đạt số khung hình liên tiếp tối đa mà một đối tượng
				# bị đánh dấu là mất, hủy đăng ký
				if self.disappeared[objectID] > self.maxDisappeared:
					self.deregister(objectID)

			# trả về sớm vì không có centroids hoặc thông tin tracking
			# để cập nhật
			return self.objects

		# khởi tạo một mảng centroids đầu vào cho khung hình hiện tại
		inputCentroids = np.zeros((len(rects), 2), dtype="int")

		# lặp qua các bounding box hình chữ nhật
		for (i, (startX, startY, endX, endY)) in enumerate(rects):
			# sử dụng tọa độ bounding box để suy ra centroid
			cX = int((startX + endX) / 2.0)
			cY = int((startY + endY) / 2.0)
			inputCentroids[i] = (cX, cY)

		# nếu hiện tại không đang theo dõi đối tượng nào, lấy centroids đầu vào
		# và đăng ký từng cái
		if len(self.objects) == 0:
			for i in range(0, len(inputCentroids)):
				self.register(inputCentroids[i])

		# ngược lại, đang có theo dõi đối tượng nên cần cố gắng
		# khớp centroids đầu vào với centroids đối tượng hiện có
		else:
			# lấy tập ID đối tượng và centroids tương ứng
			objectIDs = list(self.objects.keys())
			objectCentroids = list(self.objects.values())

			# tính khoảng cách giữa mỗi cặp centroids đối tượng
			# và centroids đầu vào, tương ứng -- mục tiêu của ta
			# sẽ là khớp một centroid đầu vào với một centroid đối tượng hiện có
			D = dist.cdist(np.array(objectCentroids), inputCentroids)

			# để thực hiện khớp này ta phải (1) tìm giá trị nhỏ nhất
			# trong mỗi hàng và sau đó (2) sắp xếp chỉ số hàng
			# dựa trên giá trị tối thiểu của chúng để hàng có giá trị nhỏ nhất
			# ở *đầu* danh sách chỉ số
			rows = D.min(axis=1).argsort()

			# tiếp theo, thực hiện quá trình tương tự trên các cột bằng cách
			# tìm giá trị nhỏ nhất trong mỗi cột và sắp xếp
			# sử dụng danh sách chỉ số hàng đã tính trước đó
			cols = D.argmin(axis=1)[rows]

			# để xác định có cần cập nhật, đăng ký,
			# hoặc hủy đăng ký một đối tượng không ta cần theo dõi những
			# chỉ số hàng và cột mà ta đã kiểm tra
			usedRows = set()
			usedCols = set()

			# lặp qua kết hợp của các tuple chỉ số (hàng, cột)
			for (row, col) in zip(rows, cols):
				# nếu đã kiểm tra giá trị hàng hoặc cột trước đó, bỏ qua
				if row in usedRows or col in usedCols:
					continue

				# nếu khoảng cách giữa centroids lớn hơn
				# khoảng cách tối đa, không liên kết hai centroids
				# với cùng một đối tượng
				if D[row, col] > self.maxDistance:
					continue

				# ngược lại, lấy ID đối tượng cho hàng hiện tại,
				# đặt centroid mới và reset bộ đếm biến mất
				objectID = objectIDs[row]
				self.objects[objectID] = inputCentroids[col]
				self.disappeared[objectID] = 0

				# đánh dấu ta đã kiểm tra mỗi chỉ số hàng và cột, tương ứng
				usedRows.add(row)
				usedCols.add(col)

			# tính cả chỉ số hàng và cột mà ta CHƯA kiểm tra
			unusedRows = set(range(0, D.shape[0])).difference(usedRows)
			unusedCols = set(range(0, D.shape[1])).difference(usedCols)

			# trong trường hợp số centroids đối tượng
			# bằng hoặc lớn hơn số centroids đầu vào
			# ta cần kiểm tra xem một số đối tượng này
			# có tiềm năng biến mất không
			if D.shape[0] >= D.shape[1]:
				# lặp qua các chỉ số hàng chưa dùng
				for row in unusedRows:
					# lấy ID đối tượng cho chỉ số hàng
					# tương ứng và tăng bộ đếm biến mất
					objectID = objectIDs[row]
					self.disappeared[objectID] += 1

					# kiểm tra xem số khung hình liên tiếp
					# đối tượng bị đánh dấu "biến mất"
					# có xứng đáng hủy đăng ký không
					if self.disappeared[objectID] > self.maxDisappeared:
						self.deregister(objectID)

			# ngược lại, nếu số centroids đầu vào lớn hơn
			# số centroids đối tượng hiện có ta cần
			# đăng ký mỗi centroid đầu vào mới như một đối tượng có thể theo dõi
			else:
				for col in unusedCols:
					self.register(inputCentroids[col])

		# trả về tập các đối tượng có thể theo dõi
		return self.objects
