from classes.objects import SingletonPatient, RawState, Context
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
        "name": context.patient.name,
        "age": context.patient.age,
        "state":context.state.state_name,
    }
    with open(os.path.join(folder, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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


def loading_project(Name: str = "", Age: int = 0, ct_path: str = "", fluoro_path: str = "", segmented_path: str = "",) -> Context:
    """Initialize a new patient and set the initial state."""
    patient = SingletonPatient.get_instance()
    patient.patient.name = Name
    patient.patient.age = Age
    context = Context(RawState(), patient)
    return context


