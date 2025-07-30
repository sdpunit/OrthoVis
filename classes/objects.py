from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
import os
import SimpleITK as sitk


class Patient:
    def __init__(self, name: str, description: str, CT: str):
        self.name = name
        self.description = description
        st_path = os.path.abspath(CT)
        if not os.path.exists(st_path):
            raise FileNotFoundError(f"❌ path dose not exist: {st_path}")

        # 路径拼接
        se1_path = os.path.join(st_path, "SE000001")
        se3_path = os.path.join(st_path, "SE000003")

        # 检查 CT 和 fluoroscopy 是否存在
        if not os.path.exists(se1_path):
            raise FileNotFoundError(f"❌ Fluoroscopy path does not exist: {se1_path}")
        if not os.path.exists(se3_path):
            raise FileNotFoundError(f"❌ CT path does not exist: {se3_path}")

        # 加载 fluoroscopy (SE000001)
        images = [sitk.ReadImage(f) for f in sorted([os.path.join(se1_path, f) for f in os.listdir(se1_path)])] 
        self.fluoroscopy = images if len(images) > 1 else images[0]
        print(f"✅ loading fluoroscopy data (SE000001)")

        # 加载 CT (SE000003)
        self.CT = self._load_series(se3_path,True)
        print(f"✅ loading CT data (SE000003)")

    def _load_series(self, ct_source, is_ct: bool = False):
        
        """
        if is_ct:
            # For CT, we can read a series of images
            reader = sitk.ImageSeriesReader()
            reader.SetFileNames(series_path)
            return reader.Execute()
        else:
            # For fluoroscopy, we can read multiple images or a single image
            images = [sitk.ReadImage(f) for f in series_path]
            return images if len(images) > 1 else images[0]
        """

        if os.path.isdir(ct_source):
            reader = sitk.ImageSeriesReader()
            series_ids = reader.GetGDCMSeriesIDs(ct_source)
            if not series_ids:
                raise RuntimeError(f"No DICOM series found in {ct_source}")
            # Pick the first series
            file_names = reader.GetGDCMSeriesFileNames(ct_source, series_ids[0])
            reader.SetFileNames(file_names)
            return reader.Execute()
        else:
            return sitk.ReadImage(ct_source)
    

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

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
        return "Name: " + self.name + "\n"+ "Description: " + self.description + "\n CT: " + str(self.CT) + "\n Flurocopy: " + str(
            self.fluoroscopy)


class SingletonPatient:
    _instance = None
    _patient = None
    _state = None

    @staticmethod
    def get_instance(name: str = "", description: str = "", CT: str = "") -> SingletonPatient:
        if SingletonPatient._instance is None:
            SingletonPatient._instance = SingletonPatient()
            SingletonPatient._patient = Patient(name, description, CT)
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

    def request_save(self, patient: SingletonPatient):
        self._singleton_data._state.handle_save(patient)
    
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
    def handle_save(self, patient: SingletonPatient) -> None:
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

    def handle_save(self, patient: SingletonPatient) -> None:
        print("RawState wants to save the context to local space.")
        name = patient._patient._name
        desc = patient._patient._description
        state = patient._state.handle_to_string()

        current_dir = Path(__file__).resolve().parent
        parent_dir = current_dir.parent
        folder = parent_dir / "Projects" / name
        folder.mkdir(parents=True, exist_ok=True)
        data = {
            "name": name,
            "description": desc,
            "state": state,
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