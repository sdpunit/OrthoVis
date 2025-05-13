# Need revision 
class Patient:
  def __init__(self, name, age, CT, fluroscopy):
    self.name = name
    self.age = age
    self.CT = CT
    self.fluroscopy = fluroscopy

  
  @property
  def name(self):
    return self._name

  @name.setter
  def name(self, value):
    self._name = value.upper()
