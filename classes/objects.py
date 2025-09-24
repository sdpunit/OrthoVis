from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
import os

def copy_directory(source_folder: str, destination_folder: str):  
    """Copy directory safely, preserving original files"""
    try:
        import shutil
        
        # Ensure destination parent directory exists
        os.makedirs(os.path.dirname(destination_folder), exist_ok=True)
        
        # Use copytree to copy the entire directory structure
        if os.path.exists(destination_folder):
            # If destination exists, remove it first to avoid conflicts
            shutil.rmtree(destination_folder)
        
        shutil.copytree(source_folder, destination_folder)
        print(f"Directory copied successfully: {source_folder} -> {destination_folder}")
        
        # Verify the original still exists
        if not os.path.exists(source_folder):
            raise Exception(f"ERROR: Original directory was deleted! {source_folder}")
        
    except Exception as e:
        print(f"Error copying directory: {e}")
        raise e


class Patient:
    def __init__(self, name: str, description: str, CT: str, fluoro: str, caligrid: str):
        self.name = name
        self.description = description
        self.CT = CT
        self.fluoro = fluoro
        self.caligrid = caligrid
        self._seg_masks_dir = None  # Added for segmentation masks directory
    

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
    def seg_masks_dir(self):
        return self._seg_masks_dir

    @seg_masks_dir.setter
    def seg_masks_dir(self, value):
        self._seg_masks_dir = value

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
            SingletonPatient._patient = Patient("", "", "", "", "")
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

        # Check if the sate is not raw
        if not isinstance(state, RawState):

            current_dir = Path(__file__).resolve().parent
            parent_dir = current_dir.parent
            patient = self._singleton_data._patient
            name = patient.name
            folder = parent_dir / "Projects" / name

            json_path = folder / "data.json"

            # Keep the other fields as they are
            # Load the existing JSON from a file
            with open(json_path, "r") as f:
                data = json.load(f)

            # Update like a normal dictionary
            data["state"] = self.request_string()


            # Update the state in metadata data.json
            with open(os.path.join(folder, "data.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)



    """
    The Context delegates part of its behavior to the current State object.
    """

    def request_process(self, arg: Any = None) -> bool:
        """Request processing with custom ROI"""
        return self._singleton_data._state.handle_process(arg)

    def request_save(self, patient: SingletonPatient) -> str:
        return self._singleton_data._state.handle_save(patient)
    
    def request_string(self) -> str:
        return self._singleton_data._state.handle_to_string()




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
    def handle_process(self, arg: Any = None) -> bool:
        pass

    @abstractmethod
    def handle_save(self, patient: SingletonPatient) -> str:
        pass

    @abstractmethod
    def handle_to_string(self) -> str:
        pass




"""
Concrete States implement various behaviors, associated with a state of the
Context.
"""


class RawState(DataState):

    def handle_process(self, arg: Any = None) -> bool:
        """Handle segmentation in RawState with custom ROI"""
        try:
            from seg.totalseg import run_complete_segmentation
            
            # Validate custom ROI
            if not arg or len(arg) == 0:
                print("RawState: Custom ROI is empty - segmentation cannot proceed")
                return False
            
            patient_instance = self.context._singleton_data._patient
            ct_dir = patient_instance.CT
            seg_dir = patient_instance.seg_masks_dir
            
            if not ct_dir or not seg_dir:
                print("RawState: Missing CT or segmentation directory")
                return False
            
            print(f"RawState: Running segmentation on {ct_dir}")
            print(f"RawState: Output directory {seg_dir}")
            print(f"RawState: Custom ROI: {arg}")
            
            success = run_complete_segmentation(ct_dir, seg_dir, arg)
            
            if success:
                print("RawState: Segmentation completed successfully")
                # Transition to next state after successful segmentation
                self.context.transition_to(SegmentState())
            else:
                print("RawState: Segmentation failed")
            
            return success
            
        except Exception as e:
            print(f"RawState: Error during segmentation: {e}")
            import traceback
            traceback.print_exc()
            return False


    def handle_save(self, patient: SingletonPatient) -> str:
        print("RawState wants to save the context to local space.")
        patient_instance = patient._patient
        # Retrieve the fields of the patient
        name = patient_instance._name
        desc = patient_instance._description
        ct = patient_instance._CT
        fluoro = patient_instance.fluoro
        caligrid = patient_instance.caligrid

        # Extract the last folder name from the CT and fluoro paths
        # ct_last = os.path.basename(os.path.normpath(ct))
        # fluoro_last = os.path.basename(os.path.normpath(fluoro))
        # caligrid_last = os.path.basename(os.path.normpath(caligrid))

        # Turns State object into its string representation
        state = patient._state.handle_to_string()

        # Create the Projects folder with the name
        # Append the last folder names extracted from the step above 
        current_dir = Path(__file__).resolve().parent
        parent_dir = current_dir.parent
        folder = parent_dir / "Projects" / name

        CT_folder = folder / "CT"
        fluoro_folder = folder / "fluoro"
        caligrid_folder = folder / "caligrid"


        # Create the directories with those folder names
        folder.mkdir(parents=True, exist_ok=True)


        # Cast the paths to str
        CT_folder = str(CT_folder)
        fluoro_folder = str(fluoro_folder)
        caligrid_folder = str(caligrid_folder)


        # Copy the CT, fluoro and caligrid paths to the Projects folder (don't move to preserve originals)
        copy_directory(ct, CT_folder)
        
        # Only copy fluoro and caligrid if paths are provided and exist
        if fluoro and os.path.exists(fluoro):
            copy_directory(fluoro, fluoro_folder)
        else:
            print(f"Skipping fluoro copy - path empty or doesn't exist: {fluoro}")
            
        if caligrid and os.path.exists(caligrid):
            copy_directory(caligrid, caligrid_folder)
        else:
            print(f"Skipping caligrid copy - path empty or doesn't exist: {caligrid}")

        # Update the path fields of the Singleton object
        patient_instance._CT = CT_folder
        patient_instance._fluoro = fluoro_folder
        patient_instance._caligrid = caligrid_folder
        

        # Create masks folder and store in patient
        masks_folder = folder / "seg_masks"
        masks_folder.mkdir(parents=True, exist_ok=True)
        patient_instance.seg_masks_dir = str(masks_folder)

        data = {
            "name": name,
            "description": desc,
            "state": state,
            "CT": CT_folder,
            "fluoro": fluoro_folder,
            "caligrid": caligrid_folder,
            "seg_masks_dir": str(masks_folder)
        }
        # Save the metadata as data.json
        with open(os.path.join(folder, "data.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return masks_folder

    def handle_to_string(self) -> str:
        return "RawState"



class SegmentState(DataState):

    def handle_process(self, arg: Any = None) -> bool:
        print("SegmentState: Already segmented - no additional processing needed")
        self.context.transition_to(CalibrationState())
        return True
 
    def handle_save(self, patient: SingletonPatient) -> str:
        print("SegmentState wants to change the state of the context.")

    def handle_to_string(self) -> str:
        return "SegmentState"


class CalibrationState(DataState):

    def handle_process(self, arg: Any = None) -> bool:
        self.context.transition_to(RegistrationState())
        return True

    def handle_save(self, patient: SingletonPatient) -> str:
        print("CalibrationState wants to change the state of the context.")

    def handle_to_string(self) -> str:
        return "CalibrationState"


class RegistrationState(DataState):

    def handle_process(self, arg: Any = None) -> bool:
        self.context.transition_to(ReferenceSysState())
        return True

    def handle_save(self, patient: SingletonPatient) -> str:
        print("RegistrationState wants to change the state of the context.")
    
    def handle_to_string(self) -> str:
        return "RegistrationState"


class ReferenceSysState(DataState):

    def handle_process(self, arg: Any = None) -> bool:
        self.context.transition_to(MotionState())
        return True

    def handle_save(self, patient: SingletonPatient) -> str:
        print("ReferenceSysState wants to change the state of the context.")

    def handle_to_string(self) -> str:
        return "ReferenceSysState"


class MotionState(DataState):

    def handle_process(self, arg: Any = None) -> bool:
        self.context.transition_to(VisualState())
        return True

    def handle_save(self, patient: SingletonPatient) -> str:
        print("MotionState wants to change the state of the context.")

    def handle_to_string(self) -> str:
        return "MotionState"



class VisualState(DataState):

    def handle_process(self, arg: Any = None) -> bool:
        return True

    def handle_save(self, patient: SingletonPatient) -> str:
        print("VisualState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

    def handle_to_string(self) -> str:
        return "VisualState"


def initialize_project(name: str, description: str, ct_path: str, fluoro_path: str, caligrid_path: str):
    """
    Initialize a new project with the given parameters.
    
    Args:
        name: Project name
        description: Project description
        ct_path: Path to CT data
        fluoro_path: Path to fluoroscopy data
        caligrid_path: Path to calibration grid data
    
    Returns:
        Context: The initialized context object
    """
    # Get the singleton instance
    singleton = SingletonPatient.get_instance()
    
    # Update patient data
    patient = singleton.patient
    patient.name = name
    patient.description = description
    patient.CT = ct_path
    patient.fluoro = fluoro_path
    patient.caligrid = caligrid_path
    
    # Create context with RawState (for new projects)
    context = Context(RawState(), singleton)
    
    print(f"Project initialized: {name}")
    print(f"CT: {ct_path}")
    print(f"Fluoro: {fluoro_path}")
    print(f"Caligrid: {caligrid_path}")
    
    return context



class StateFactory:
    @staticmethod
    def get_state(state: str) -> DataState:
        if state == "RawState":
            return RawState()
        
        elif state == "SegmentState":
            return SegmentState()
        
        elif state == "CalibrationState":
            return CalibrationState()
        
        elif state == "RegistrationState":
            return RegistrationState()
        
        elif state == "ReferenceSysState":
            return ReferenceSysState()
        
        elif state == "MotionState":
            return MotionState()
            
        else:
            return VisualState()


# if __name__ == "__main__":
#     # The client code.
#     Singleton_instance = SingletonPatient.get_instance()
#     context = Context(RawState(), Singleton_instance)
#     context.handle_import_import()
#     context.handle_import_import()
#     context.handle_import_import()
#     context.handle_import_import()