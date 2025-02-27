from app import mongo
from datetime import datetime, time
import qrcode
import json
import os
from bson import ObjectId
import requests
from ..config import Config

class AppointmentService:
    def __init__(self):
        self.mongo = mongo
        self.tables = list(range(1, 11))  # 10 bàn từ 1-10
        self.telegram_bot_token = Config.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = Config.TELEGRAM_CHAT_ID
        
    def check_table_available(self, table_number, appointment_date, appointment_time):
        """Kiểm tra bàn có trống không"""
        # Convert string to datetime
        appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        
        # Kiểm tra xem bàn đã được đặt trong khoảng thời gian ±2 giờ chưa
        start_time = appointment_datetime.replace(hour=appointment_datetime.hour - 2)
        end_time = appointment_datetime.replace(hour=appointment_datetime.hour + 2)
        
        existing_appointment = self.mongo.db.appointments.find_one({
            "table_number": table_number,
            "appointment_datetime": {
                "$gte": start_time,
                "$lte": end_time
            },
            "status": {"$in": ["pending", "confirmed"]}
        })
        
        return existing_appointment is None

    def create_appointment(self, appointment_data):
        """Tạo lịch hẹn mới"""
        try:
            # Tạo appointment datetime
            appointment_date = datetime.strptime(appointment_data['appointment_date'], "%Y-%m-%d")
            
            # Xử lý time input một cách linh hoạt
            try:
                # Make sure we're parsing the time correctly
                time_str = appointment_data['appointment_time']
                # Ensure the time format is correct (HH:MM)
                if ':' in time_str:
                    hour, minute = map(int, time_str.split(':'))
                    if hour < 0 or hour > 23:
                        raise ValueError("hour must be in 0..23")
                    if minute < 0 or minute > 59:
                        raise ValueError("Minute must be in 0..59")
                    appointment_time = time(hour, minute)
                else:
                    raise ValueError("Invalid time format")
            except ValueError as e:
                # Log the specific error for debugging
                print(f"Time parsing error: {str(e)}")
                raise Exception(f"Invalid time format: {str(e)}")
            
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            
            # Kiểm tra thời gian đặt lịch phải sau thời gian hiện tại
            current_datetime = datetime.now()
            if appointment_datetime <= current_datetime:
                raise Exception("Appointment time must be after current time")
                
            # Validate dữ liệu
            if not self.check_table_available(
                appointment_data["table_number"],
                appointment_data["appointment_date"],
                f"{hour:02d}:{minute:02d}"  # Format time consistently
            ):
                raise Exception("Table is not available at this time")
            
            # Chuẩn bị dữ liệu để lưu
            appointment = {
                "customer_id": appointment_data["customer_id"],
                "table_number": appointment_data["table_number"],
                "appointment_datetime": appointment_datetime,
                "notes": appointment_data.get("notes", ""),
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Lưu vào database
            result = self.mongo.db.appointments.insert_one(appointment)
            
            # Tạo QR code
            qr_data = {
                "appointment_id": str(result.inserted_id),
                "customer_id": appointment["customer_id"],
                "table_number": appointment["table_number"],
                "appointment_datetime": appointment_datetime.strftime("%Y-%m-%d %H:%M"),
                "status": appointment["status"]
            }
            
            # Tạo QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Lưu QR code
            qr_folder = "static/qrcodes"
            os.makedirs(qr_folder, exist_ok=True)
            qr_path = f"{qr_folder}/appointment_{str(result.inserted_id)}.png"
            qr_image.save(qr_path)
            
            # Gửi thông báo Telegram khi tạo lịch hẹn mới
            try:
                # Lấy thông tin customer
                customer = self.mongo.db.customers.find_one({"_id": ObjectId(appointment_data["customer_id"])})
                if customer:
                    self.send_telegram_notification(customer, appointment, "New Appointment")
            except Exception as e:
                print(f"Error sending Telegram notification for new appointment: {str(e)}")
            
            return {
                "appointment_id": str(result.inserted_id),
                "qr_code_url": f"/static/qrcodes/appointment_{str(result.inserted_id)}.png"
            }

        except Exception as e:
            print(f"Error creating appointment: {str(e)}")
            raise e

    def get_appointment(self, appointment_id):
        """Lấy thông tin lịch hẹn"""
        try:
            appointment = self.mongo.db.appointments.find_one({"_id": ObjectId(appointment_id)})
            if appointment:
                appointment["_id"] = str(appointment["_id"])
                return appointment
            return None
        except Exception as e:
            print(f"Error getting appointment: {str(e)}")
            return None

    def get_appointments_by_customer_id(self, customer_id):
        """Lấy danh sách lịch hẹn của customer"""
        try:
            appointments = list(self.mongo.db.appointments.find({"customer_id": customer_id}))
            for appointment in appointments:
                appointment["_id"] = str(appointment["_id"])
            return appointments
        except Exception as e:
            print(f"Error getting appointments: {str(e)}")
            return []

    def send_telegram_notification(self, customer_data, appointment_data, notification_type="Check-in"):
        """Gửi thông báo đến Telegram"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                print("Telegram credentials not configured. Bot token:", bool(self.telegram_bot_token), "Chat ID:", bool(self.telegram_chat_id))
                return False

            # Format datetime correctly based on whether it's a datetime object or a string
            if isinstance(appointment_data['appointment_datetime'], datetime):
                appointment_time = appointment_data['appointment_datetime'].strftime('%Y-%m-%d %H:%M')
            else:
                appointment_time = appointment_data['appointment_datetime']

            # Create appropriate emoji and title based on notification type
            if notification_type == "Check-in":
                emoji = "✅"
                title = "Check-in"
            else:
                emoji = "🔔"
                title = "New Appointment"

            message = (
                f"{emoji} *{title}*\n\n"
                f"*Customer Information:*\n"
                f"Name: {customer_data.get('full_name', 'N/A')}\n"
                f"ID Number: {customer_data.get('id_number', 'N/A')}\n"
                f"Phone: {customer_data.get('phone', 'N/A')}\n\n"
                f"*Appointment Details:*\n"
                f"Table: {appointment_data.get('table_number', 'N/A')}\n"
                f"Date: {appointment_time}\n"
                f"Status: {appointment_data.get('status', 'N/A')}"
            )

            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            print(f"Sending Telegram notification to {self.telegram_chat_id}")
            response = requests.post(url, json=payload)
            
            if response.status_code != 200:
                print(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
            print(f"Telegram notification sent successfully: {response.status_code}")
            return True
            
        except Exception as e:
            print(f"Error sending Telegram notification: {str(e)}")
            return False

    def verify_appointment(self, appointment_id):
        """Xác thực lịch hẹn khi checkin"""
        try:
            appointment = self.mongo.db.appointments.find_one({"_id": ObjectId(appointment_id)})
            if not appointment:
                return False, "Appointment not found"
                
            # Kiểm tra thời gian
            now = datetime.utcnow()
            # appointment_time = appointment["appointment_datetime"]
            # time_diff = abs((now - appointment_time).total_seconds() / 3600)
            
            # if time_diff > 1:  # Cho phép check in trước/sau 1 giờ
            #     return False, "Invalid check-in time"
                
            # Lấy thông tin customer
            customer = self.mongo.db.customers.find_one({"_id": ObjectId(appointment["customer_id"])})
            
            # Cập nhật trạng thái
            self.mongo.db.appointments.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$set": {"status": "checked_in", "updated_at": now}}
            )
            
            # Gửi thông báo Telegram
            telegram_sent = False
            if customer:
                telegram_sent = self.send_telegram_notification(customer, appointment, "Check-in")
                print(f"Telegram notification sent: {telegram_sent}")
            else:
                print("Customer not found, cannot send Telegram notification")
            
            return True, "Check-in successful"
            
        except Exception as e:
            print(f"Error verifying appointment: {str(e)}")
            return False, str(e)

