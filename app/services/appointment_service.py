from app import mongo
from datetime import datetime
import qrcode
import json
import os
from bson import ObjectId

class AppointmentService:
    def __init__(self):
        self.mongo = mongo
        self.tables = list(range(1, 11))  # 10 bàn từ 1-10
        
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
            # Validate dữ liệu
            if not self.check_table_available(
                appointment_data["table_number"],
                appointment_data["appointment_date"],
                appointment_data["appointment_time"]
            ):
                raise Exception("Table is not available at this time")

            # Tạo appointment datetime
            appointment_datetime = datetime.strptime(
                f"{appointment_data['appointment_date']} {appointment_data['appointment_time']}", 
                "%Y-%m-%d %H:%M"
            )
            
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

    def verify_appointment(self, appointment_id):
        """Xác thực lịch hẹn khi checkin"""
        try:
            appointment = self.mongo.db.appointments.find_one({"_id": ObjectId(appointment_id)})
            if not appointment:
                return False, "Appointment not found"
                
            # Kiểm tra thời gian
            now = datetime.utcnow()
            appointment_time = appointment["appointment_datetime"]
            time_diff = abs((now - appointment_time).total_seconds() / 3600)
            
            if time_diff > 1:  # Cho phép check in trước/sau 1 giờ
                return False, "Invalid check-in time"
                
            # Cập nhật trạng thái
            self.mongo.db.appointments.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$set": {"status": "checked_in", "updated_at": now}}
            )
            
            return True, "Check-in successful"
            
        except Exception as e:
            print(f"Error verifying appointment: {str(e)}")
            return False, str(e)

