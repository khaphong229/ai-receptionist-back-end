from flask import Blueprint, request, jsonify
from datetime import datetime
from app import mongo
from app.services.appointment_service import AppointmentService
from bson import ObjectId

appointment_bp = Blueprint("appointment", __name__)
appointment_service = AppointmentService()

@appointment_bp.route("/create", methods=["POST"])
def create_appointment():
    """API tạo lịch hẹn mới"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        required_fields = ["customer_id", "appointment_date", "appointment_time", "table_number"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"{field} is required"
                }), 400

        # Validate date format
        try:
            datetime.strptime(data["appointment_date"], "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid date format. Use YYYY-MM-DD for date"
            }), 400

        # Validate table number
        if not 1 <= int(data["table_number"]) <= 10:
            return jsonify({
                "status": "error",
                "message": "Invalid table number. Must be between 1 and 10"
            }), 400

        # Create appointment
        result = appointment_service.create_appointment(data)

        return jsonify({
            "status": "success",
            "message": "Appointment created successfully",
            "data": result
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@appointment_bp.route("/verify", methods=["POST", "GET"])
def verify_appointment():
    """API xác thực lịch hẹn khi checkin"""
    try:
        # Xử lý cả GET và POST request
        if request.method == "GET":
            appointment_id = request.args.get("appointment_id")
        else:
            data = request.get_json()
            appointment_id = data.get("appointment_id") if data else None
        
        if not appointment_id:
            return jsonify({
                "status": "error",
                "message": "Appointment ID is required"
            }), 400

        success, message = appointment_service.verify_appointment(appointment_id)
        
        if success:
            return jsonify({
                "status": "success",
                "message": message
            })
        else:
            return jsonify({
                "status": "error",
                "message": message
            }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@appointment_bp.route("/get/<appointment_id>", methods=["GET"])
def get_appointment(appointment_id):
    """API lấy thông tin lịch hẹn"""
    try:
        appointment = appointment_service.get_appointment(appointment_id)
        
        if appointment:
            return jsonify({
                "status": "success",
                "data": appointment
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Appointment not found"
            }), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@appointment_bp.route("/update", methods=["PUT"])
def update_appointment():
    pass

@appointment_bp.route("/delete", methods=["DELETE"])
def delete_appointment():
    pass

@appointment_bp.route("/customer/<customer_id>/appointments", methods=["GET"])
def get_customer_appointments(customer_id):
    """API lấy danh sách lịch hẹn của customer"""
    try:
        appointments = appointment_service.get_appointments_by_customer_id(customer_id)
        
        return jsonify({
            "status": "success",
            "data": appointments
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
