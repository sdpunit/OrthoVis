from objects import Patient

class SingletonPatient:
    _instance = None
    _patient = None

    @staticmethod
    def get_instance():
        if SingletonPatient._instance is None:
            SingletonPatient._instance = SingletonPatient()
            SingletonPatient._patient = Patient("", 0, "", "", "")
        return SingletonPatient._instance
    
    @property
    def patient(self):
      return self._patient



# Usage
if __name__ == "__main__":
    SingletonPatient_instance = SingletonPatient.get_instance()
    patient = SingletonPatient_instance.patient
    patient.name = "Test"
    patient.age = 30
    patient.CT = "CT"
    patient.fluroscopy = "Fluoro"
    patient.segmentedCT = "SegmentedCT"

    print(patient.to_string())