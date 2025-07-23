from __future__ import annotations
from abc import ABC, abstractmethod


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
    _state = None

    @staticmethod
    def get_instance():
        if SingletonPatient._instance is None:
            SingletonPatient._instance = SingletonPatient()
            SingletonPatient._patient = Patient("", 0, "", "", "")
        return SingletonPatient._instance
    
    @property
    def patient(self):
      return self._patient
  

class Context:
    """
    The Context defines the interface of interest to clients. It also maintains
    a reference to an instance of a State subclass, which represents the current
    state of the Context.
    """

    _singleton_data = None
    # _name = None
    # _description = None
    """
    A reference to the current state of the Context.
    """

    def __init__(self, state: DataState, data: SingletonPatient) -> None:
        self._singleton_data = data
        self.transition_to(state)
        # self._name = patient.name
        # self._description = description

    def transition_to(self, state: DataState):
        """
        The Context allows changing the State object at runtime.
        """

        print(f"Context: Transition to {type(state).__name__}")
        self._singleton_data._state = state
        self._singleton_data._state.context = self

    """
    The Context delegates part of its behavior to the current State object.
    """

    def request_import(self, path: str):
        self._singleton_data._state.handle_import(path)

    def request_process(self):
        self._singleton_data._state.handle_process()

    def request_save(self):
        self._singleton_data._state.handle_save()



class DataState(ABC):
    """
    The base State class declares methods that all Concrete State should
    implement and also provides a backreference to the Context object,
    associated with the State. This backreference can be used by States to
    transition the Context to another State.
    """

    @property
    def context(self) -> Context:
        return self._context

    @context.setter
    def context(self, context: Context) -> None:
        self._context = context

    @abstractmethod
    def handle_import(self) -> None:
        pass
    
    @abstractmethod
    def handle_process(self) -> None:
        pass
    
    @abstractmethod
    def handle_save(self) -> None:
        pass


"""
Concrete States implement various behaviors, associated with a state of the
Context.
"""

class RawState(DataState):
    def handle_import(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_process(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_save(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

class SegmentState(DataState):
    def handle_import(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_process(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_save(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

class CalibrationState(DataState):
    def handle_import(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_process(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_save(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

class RegistrationState(DataState):
    def handle_import(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_process(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_save(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

class ReferenceSysState(DataState):
    def handle_import(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_process(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_save(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

class MotionState(DataState):
    def handle_import(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_process(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_save(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

class VisualState(DataState):
    def handle_import(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_process(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_save(self) -> None:
        print("RawState wants to change the state of the context.")
        self.context.transition_to(SegmentState())


# if __name__ == "__main__":
#     # The client code.
#     Singleton_instance = SingletonPatient.get_instance()
#     context = Context(RawState(), Singleton_instance)
#     context.handle_import_import()
#     context.handle_import_import()
#     context.handle_import_import()
#     context.handle_import_import()