# -*- coding: utf-8 -*-
class TrackableObject:
	def __init__(self, objectID, centroid):
		# lưu ID đối tượng, sau đó khởi tạo danh sách centroids
		# sử dụng centroid hiện tại
		self.objectID = objectID
		self.centroids = [centroid]

		# khởi tạo boolean dùng để chỉ thị đối tượng đã
		# được đếm chưa
		self.counted = False
