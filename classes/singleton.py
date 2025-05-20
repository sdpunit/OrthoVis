# Need revision 
class Patient:
  def __init__(self, name : str, age : int, CT : str, fluroscopy : str, segmentedCT : str):
    self.name = name
    self.age = age
    self.CT = CT
    self.fluroscopy = fluroscopy
    self.segmentedCT = segmentedCT
  
  @property
  def name(self):
    return self._name

  @name.setter
  def name(self, value):
    self._name = value.upper()

  @property
  def age(self):
    return self._age

  @age.setter
  def age(self, value):
    self._age = value

  @property
  def CT(self):
    return self._CT

  @CT.setter
  def CT(self, value):
    self._CT = value

  @property
  def fluroscopy(self):
    return self._fluroscopy 

  @fluroscopy.setter
  def fluroscopy(self, value):
    self._fluroscopy = value

  @property
  def segmentedCT(self):
    return self._segmentedCT 

  @segmentedCT.setter
  def segmentedCT(self, value):
    self._segmentedCT = value

  def to_string(self):
    return "Name: "+self.name+"\n Age: "+str(self.age) + "\n CT: "+self.CT+"\n Flurocopy: "+self.fluroscopy


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
# if __name__ == "__main__":
#     singletonPatient_instance = SingletonPatient.get_instance()
#     patient = singletonPatient_instance.patient
#     patient.name = "Test"
#     patient.age = 30
#     patient.CT = "CT"
#     patient.fluroscopy = "Fluoro"
#     patient.segmentedCT = "SegmentedCT"

#     # Tests
#     assert patient.name == "TEST"
#     assert patient.age == 30
#     assert patient.CT == "CT"
#     assert patient.fluroscopy == "Fluoro"
#     assert patient.segmentedCT =="SegmentedCT"

#     singletonPatient_instance2 = SingletonPatient.get_instance()

#     assert id(singletonPatient_instance) == id(singletonPatient_instance2)

#     print(patient.to_string())
