from objects import Patient

class SingletonPatient:
    _instance = None
    _patient = Patient("Test", 30, "CT", "Fluro")

    @staticmethod
    def get_instance():
        if SingletonPatient._instance is None:
            SingletonPatient._instance = SingletonPatient()
        return SingletonPatient._instance

# Usage
if __name__ == "__main__":
    SingletonPatient_instance = SingletonPatient.get_instance()