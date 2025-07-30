from classes.objects import SingletonPatient, RawState, Context, DataState
import os
import json
import SimpleITK as sitk
from pathlib import Path


def save_patient_data_to_file(context, file_name):
    """
    Save the patient data to a file.
    :param patient: SingletonPatient instance
    :param file_name: name to the file where data will be saved
    """
    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    folder = parent_dir / "Projects"/ file_name
    folder.mkdir(parents=True, exist_ok=True)
    data = {
        "name": context._singleton_data.patient.name,
        "description": context._singleton_data.patient.description,
        "state":context._singleton_data.state.handle_to_string(),
    }
    with open(os.path.join(folder, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    #Save CT
    CT_num_slices = context._singleton_data.patient.CT.GetDepth()
    CT_folder = folder / "SE000003"
    CT_folder.mkdir(parents=True, exist_ok=True)
    for i in range(CT_num_slices):
        slice_i = context._singleton_data.patient.CT[:, :, i]
        filename = f"IN{i+1:06d}.dcm"

        filepath = os.path.join( CT_folder, filename)
        sitk.WriteImage(slice_i, filepath)
    print(f"✅ all CT slices be saved")
    print(f"✅ all segmentedCT slices be saved")

    # Save fluoroscopy
    fluoro = context._singleton_data.patient.fluoroscopy

    if isinstance(fluoro, list):
        for i, slice_i in enumerate(fluoro):
            filename = f"IN{i+1:06d}.dcm"
            filepath = os.path.join(parent_dir, "Projects", file_name, "SE000001", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            sitk.WriteImage(slice_i, filepath)
    else:
        filename = "IN000001.dcm"
        filepath = os.path.join(parent_dir, "Projects", file_name, "SE000001", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        sitk.WriteImage(fluoro, filepath)
    print(f"✅ all fluoroscopy slices be saved")




def read_patient_data_from_file(file_path):
    """
    Read patient data from a file.
    :param file_name: name of the file to read data from
    :return: dictionary with patient data
    """
    with open(os.path.join(file_path, "data.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    name = data["name"]
    description = data["description"]
    state = data["state"]
    switcher = {
        "RawState": RawState(),
        # Add other states here as needed
    }
    state_instance = switcher[state]
    ct_path = os.path.join(file_path)
    return loading_project(Name=name, Description=description, ct_path=ct_path, state=state_instance)

def loading_project(Name: str = "", Description: str = "", ct_path: str = "", state : DataState = RawState()) -> Context:
    """Initialize a new patient and set the initial state."""
    patient = SingletonPatient.get_instance(Name, ct_path)
    context = Context(state, patient)
    return context

def initialize_project(name:str , description:str, CT_path: str, fluoro_path: str = "") -> Context:
    """
    Initialize a new patient and set the initial state.
    :param name: name of the patient
    :param CT_path: path to the CT image
    :param fluoro_path: path to the fluoroscopy image
    :param segmented_path: path to the segmented CT image
    :return: Context object with the initialized patient and state
    """
    patient = SingletonPatient.get_instance(name, description, CT_path)
    context = Context(RawState(), patient)
    return context

if __name__ == '__main__':
    # Example usage of the functions
    # Initialize a new patient and context
    #context = initialize_project("Pench", 24, "/Users/apple/PycharmProjects/OrthoVis/classes/Data/DICOM/P0000001/ST000001")
    #Test for simple save function
    #save_patient_data_to_file(context,"PROJECT_1")
    context = read_patient_data_from_file("/Users/apple/PycharmProjects/OrthoVis/Projects/PROJECT_1")

    print(context._singleton_data.patient.name)
    print(context._singleton_data.patient.description)
    print(context._singleton_data.state.handle_to_string())
    print(context._singleton_data.patient.CT)


