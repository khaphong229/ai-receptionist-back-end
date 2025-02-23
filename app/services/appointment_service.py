from app import mongo

class AppointmentService:
    def __init__(self):
        self.mongo = mongo
    
    def checkHasTable(self, appointment_data):
        pass

    def create_appointment(self, appointment_data):
        try:
            self.mongo.db.appointments.insert_one(appointment_data)
            return True
        except Exception as e:
            print(f"Error creating appointment: {str(e)}")
            return False

