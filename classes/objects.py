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