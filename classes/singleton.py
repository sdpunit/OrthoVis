from objects import Patient

class SingletonPatient:
    _instance = None
    _patient = None

    @staticmethod
    def get_instance(name: str, age: int, CT=None, fluroscopy=None, segmentedCT=None):
        if SingletonPatient._instance is None:
            SingletonPatient._instance = SingletonPatient()
            SingletonPatient._patient = Patient(name=name, age=age, CT=CT, fluroscopy=fluroscopy, segmentedCT= segmentedCT)
        return SingletonPatient._instance

    def set_CT(self, CT):
        self._patient.CT = CT
        return True
    def set_fluroscopy(self, fluroscopy):
        self._patient.fluroscopy = fluroscopy
        return True
# Usage
if __name__ == "__main__":
    SingletonPatient_instance = SingletonPatient.get_instance("Test",30)