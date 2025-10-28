# -*- coding: utf-8 -*-
import smtplib
import json

# khởi tạo cấu hình tính năng
with open("utils/config.json", "r") as file:
    config = json.load(file)

class Mailer:
    """ Lớp để kích hoạt chức năng cảnh báo email. """

    def __init__(self):
        self.email = config["Email_Send"]
        self.password = config["Email_Password"]
        self.port = 465
        self.server = smtplib.SMTP_SSL('smtp.gmail.com', self.port)

    def send(self, mail):
        self.server = smtplib.SMTP_SSL('smtp.gmail.com', self.port)
        self.server.login(self.email, self.password)
        # tin nhắn để gửi
        SUBJECT = 'CẢNH BÁO!'
        TEXT = f'Giới hạn người trong tòa nhà của bạn đã vượt quá!'
        message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)
        # gửi email
        self.server.sendmail(self.email, mail, message)
        self.server.quit()
