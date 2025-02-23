from flask import Blueprint, request, jsonify
from datetime import datetime
from app import mongo
from app.services.appointment_service import AppointmentService
appointment_bp = Blueprint("appointment", __name__)
appointment_service = AppointmentService()

@appointment_bp.route("/create", methods=["POST"])
def create_appointment():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        customer_id = data.get("customer_id")
        if not customer_id:
            return jsonify({
                "status": "error",
                "message": "Customer ID is required"
            }), 400
        
        appointment_data = {
            "customer_id": customer_id,
            "appointment_date": data.get("appointment_date"),
            "appointment_time": data.get("appointment_time"),
            "appointment_status": data.get("appointment_status"),
            "appointment_table": data.get("appointment_table"),
            "appointment_note": data.get("appointment_note"),
        }

        if appointment_data.appointment_time < datetime.now():
            return jsonify({
                "status": "error",
                "message": "Appointment time cannot be in the past"
            }), 400
        
        appointment_service.create_appointment(appointment_data)

        return jsonify({
            "status": "success",
            "message": "Appointment created successfully",
            "appointment_id": str(appointment_data.inserted_id)
        }), 201


    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@appointment_bp.route("/get", methods=["GET"])
def get_appointment():
    pass


@appointment_bp.route("/update", methods=["PUT"])
def update_appointment():
    pass

@appointment_bp.route("/delete", methods=["DELETE"])
def delete_appointment():
    pass
