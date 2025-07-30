from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
import os
import SimpleITK as sitk


class Patient:
    def __init__(self, name: str, age: int, CT: str, fluoroscopy: str):
        self.name = name
        self.age = age
        file_names = sorted([os.path.join(CT, f) for f in os.listdir(CT)])
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(file_names)
        ct_image = reader.Execute()
        self.CT = ct_image
        if fluoroscopy == "":
            self.fluoroscopy = sitk.Image()
        else:
            file_names = sorted([os.path.join(fluoroscopy, f) for f in os.listdir(fluoroscopy)])
            reader = sitk.ImageSeriesReader()
            reader.SetFileNames(file_names)
            fluoroscopy_image = reader.Execute()
            self.fluoroscopy = fluoroscopy_image


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
    def fluoroscopy(self):
        return self._fluoroscopy

    @fluoroscopy.setter
    def fluoroscopy(self, value):
        self._fluoroscopy = value

    def to_string(self):
        return "Name: " + self.name + "\n Age: " + str(self.age) + "\n CT: " + str(self.CT) + "\n Flurocopy: " + str(
            self.fluoroscopy)


class SingletonPatient:
    _instance = None
    _patient = None
    _state = None

    @staticmethod
    def get_instance(name: str = "", age: int = 0, CT: str = "", fluroscopy: str = "") -> SingletonPatient:
        if SingletonPatient._instance is None:
            SingletonPatient._instance = SingletonPatient()
            SingletonPatient._patient = Patient(name, age, CT, fluroscopy)
        return SingletonPatient._instance

    @property
    def patient(self):
        return self._patient

    @property
    def state(self):
        return self._state


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
    
    def request_string(self):
        self._singleton_data._state.handle_to_string()


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

    @abstractmethod
    def handle_to_string(self) -> None:
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

    def handle_save(self, context: Context) -> None:
        print("RawState wants to save the context to local space.")
        current_dir = Path(__file__).resolve().parent
        parent_dir = current_dir.parent
        folder = parent_dir / "Projects" / context.patient.name
        folder.mkdir(parents=True, exist_ok=True)
        data = {
            "name": context._singleton_data._patient._name,
            "age": context._singleton_data._patient._age,
            "state": context._state.handle_to_string(),
        }
        with open(os.path.join(folder, "data.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def handle_to_string(self) -> str:
        return "RawState"


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

    def handle_to_string(self) -> str:
        return "SegmentState"


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

    def handle_to_string(self) -> str:
        return "CalibrationState"


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
    
    def handle_to_string(self) -> str:
        return "RegistrationState"


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

    def handle_to_string(self) -> str:
        return "ReferenceSysState"


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

    def handle_to_string(self) -> str:
        return "MotionState"


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

    def handle_to_string(self) -> str:
        return "VisualState"

# if __name__ == "__main__":
#     # The client code.
#     Singleton_instance = SingletonPatient.get_instance()
#     context = Context(RawState(), Singleton_instance)
#     context.handle_import_import()
#     context.handle_import_import()
#     context.handle_import_import()
#     context.handle_import_import()