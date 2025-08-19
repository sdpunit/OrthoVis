from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
import os
import shutil

def move_directory(source_folder : str, destination_folder: str):  
    try:
        # Move the folder
        shutil.move(source_folder, destination_folder)
        print(f"Folder '{source_folder}' moved successfully to '{destination_folder}'")
    except FileNotFoundError:
        print(f"Error: Source folder '{source_folder}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


class Patient:
    def __init__(self, name: str, description: str, CT: str, fluoro: str, caligrid: str, mask: str):
        self.name = name
        self.description = description
        self.CT = CT
        self.fluoro = fluoro
        self.caligrid = caligrid
        self.mask = mask
    

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
    def fluoro(self):
        return self._fluoro

    @fluoro.setter
    def fluoro(self, value):
        self._fluoro = value

    @property
    def caligrid(self):
        return self._caligrid

    @caligrid.setter
    def caligrid(self, value):
        self._caligrid = value

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, value):
        self._mask = value

    def to_string(self):
        return "Name: " + self.name + "\n"+ "Description: " + self.description + "\n CT: " + str(self.CT) + "\n Flurocopy: " + str(
            self.fluoro)


class SingletonPatient:
    _instance = None
    _patient = None
    _state = None

    @staticmethod
    def get_instance() -> SingletonPatient:
        if SingletonPatient._instance is None:
            SingletonPatient._instance = SingletonPatient()
            SingletonPatient._patient = Patient("", "", "", "", "", "")
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
        patient_instance = patient._patient
        # Retrieve the fields of the patient
        name = patient_instance._name
        desc = patient_instance._description
        ct = patient_instance._CT
        fluoro = patient_instance.fluoro
        caligrid = patient_instance.caligrid

        # Extract the last folder name from the CT and fluoro paths
        ct_last = os.path.basename(os.path.normpath(ct))
        fluoro_last = os.path.basename(os.path.normpath(fluoro))
        caligrid_last = os.path.basename(os.path.normpath(caligrid))

        # Turns State object into its string representation
        state = patient._state.handle_to_string()

        # Create the Projects folder with the name
        # Append the last folder names extracted from the step above 
        current_dir = Path(__file__).resolve().parent
        parent_dir = current_dir.parent
        folder = parent_dir / "Projects" / name

        CT_folder = folder / ct_last
        fluoro_folder = folder / fluoro_last
        caligrid_folder = folder / caligrid_last


        # Create the directories with those folder names
        folder.mkdir(parents=True, exist_ok=True)

        #add masks file:
        masks_folder = folder / "seg-masks"
        masks_folder.mkdir(parents=True, exist_ok=True)

        # Cast the paths to str
        CT_folder = str(CT_folder)
        fluoro_folder = str(fluoro_folder)
        caligrid_folder = str(caligrid_folder)
        masks_folder = str(masks_folder)


        # Move the CT, fluoro and caligrid paths to the Projects folder
        move_directory(ct, folder)
        move_directory(fluoro, folder)
        move_directory(caligrid, folder)

        # Update the path fields of the Singleton object
        patient_instance._CT = CT_folder
        patient_instance._fluoro = fluoro_folder
        patient_instance._caligrid = caligrid_folder
        patient_instance._mask = masks_folder
        

        data = {
            "name": name,
            "description": desc,
            "state": state,
            "CT": CT_folder,
            "fluoro": fluoro_folder,
            "caligrid": caligrid_folder,
            "mask": masks_folder,
        }
        # Save the metadata as data.json
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