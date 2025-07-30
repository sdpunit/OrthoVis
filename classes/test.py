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
        "age": context._singleton_data.patient.age,
        "state":context._singleton_data.state.handle_to_string(),
    }
    with open(os.path.join(folder, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    #Save CT
    CT_num_slices = context._singleton_data.patient.CT.GetDepth()
    CT_folder = folder / "CT"
    CT_folder.mkdir(parents=True, exist_ok=True)
    for i in range(CT_num_slices):
        slice_i = context._singleton_data.patient.CT[:, :, i]
        filename = f"IN{i+1:06d}.dcm"

        filepath = os.path.join( CT_folder, filename)
        sitk.WriteImage(slice_i, filepath)
    print(f"✅ all CT slices be saved")
    print(f"✅ all segmentedCT slices be saved")

    # Save fluoroscopy
    fluoroscopy_num_slices = context._singleton_data.patient.fluoroscopy.GetDepth()
    for i in range(fluoroscopy_num_slices):
        slice_i = context._singleton_data.patient.fluoroscopy[:, :, i]
        filename = f"SE{i:06d}.dcm"
        filepath = os.path.join(parent_dir / "Projects" / file_name / "fluoroscopy", filename)
        sitk.WriteImage(slice_i, filepath)
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
    age = data["age"]
    state = data["state"]
    switcher = {
        "RawState": RawState(),
        # Add other states here as needed
    }
    state_instance = switcher[state]
    if state == "RawState":
        ct_path = os.path.join(file_path, "CT")
        return loading_project(Name=name, Age=age, ct_path=ct_path, state=state_instance)
    else:
        ct_path = os.path.join(file_path, "segmentCT")
        return loading_project(Name=name, Age=age, ct_path=os.path, state = state_instance)

def loading_project(Name: str = "", Age: int = 0, ct_path: str = "", state : DataState = RawState()) -> Context:
    """Initialize a new patient and set the initial state."""
    patient = SingletonPatient.get_instance(Name, Age, ct_path)
    context = Context(state, patient)
    return context

def initialize_project(name:str , age : int, CT_path: str, fluoro_path: str = "") -> Context:
    """
    Initialize a new patient and set the initial state.
    :param name: name of the patient
    :param age: age of the patient
    :param CT_path: path to the CT image
    :param fluoro_path: path to the fluoroscopy image
    :param segmented_path: path to the segmented CT image
    :return: Context object with the initialized patient and state
    """
    patient = SingletonPatient.get_instance(name, age, CT_path, fluoro_path)
    context = Context(RawState(), patient)
    return context
if __name__ == '__main__':
    # Example usage of the functions
    # Initialize a new patient and context
    #context = initialize_project("Pench", 24, "/Users/apple/PycharmProjects/OrthoVis/classes/Data/DICOM/P0000001/ST000001/SE000003")
    #Test for simple save function
    #save_patient_data_to_file(context,"PROJECT_1")
    context = read_patient_data_from_file("/Users/apple/PycharmProjects/OrthoVis/Projects/PROJECT_1")

    print(context._singleton_data.patient.name)
    print(context._singleton_data.patient.age)
    print(context._singleton_data.state.state_name)
    print(context._singleton_data.patient.CT)


