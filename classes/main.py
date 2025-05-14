import classes
import SimpleITK as sitk
import os
import pickle

from classes.singleton import SingletonPatient
from classes.states import Context


def initialize(ct_dir, fluoro_dir) -> classes.states.Context:
    # Create a new singleton patient
    patient = classes.singleton.SingletonPatient.get_instance("name",age=30)
    # Create a new context with the patient
    context = classes.states.Context(classes.states.HomePageState(patient))
    # loading the CT and fluoroscopy images
    ct_image = load_ct(ct_dir)
    fluoro_image = load_ct(fluoro_dir)
    # Set the CT and fluroscopy images
    patient.set_CT(ct_image)
    patient.set_fluroscopy(fluoro_image)
    return context

def save_context(context: Context, folder="saved_context"):
    """
    Save the current context and patient data to a specified folder.
    :param context:
    :param folder:
    :return:
    """

    os.makedirs(folder, exist_ok=True)
    patient = context._singleton_patient._patient

    # loading image path
    ct_path = os.path.join(folder, "ct.nii.gz")
    fluoro_path = os.path.join(folder, "fluoro.nii.gz")
    segmented_path = os.path.join(folder, "segmented.nii.gz")

    # save images
    if patient.CT: sitk.WriteImage(patient.CT, ct_path)
    if patient.fluroscopy: sitk.WriteImage(patient.fluroscopy, fluoro_path)
    if patient.segmentedCT: sitk.WriteImage(patient.segmentedCT, segmented_path)

    # save matadata
    metadata = {
        "state_class": context._state.__class__.__name__,
        "description": context._description,
        "name": patient.name,
        "age": patient.age,
        "ct_path": ct_path if patient.CT else None,
        "fluoro_path": fluoro_path if patient.fluroscopy else None,
        "segmented_path": segmented_path if patient.segmentedCT else None
    }

    with open(os.path.join(folder, "context.pkl"), "wb") as f:
        pickle.dump(metadata, f)

    print(f"[✅] Context + Patient saved to {folder}")
    return
def load_context(folder="saved_context") -> Context:
    """
    Load the context and patient data from a specified folder.
    :param folder:
    :return: context
    """
    with open(os.path.join(folder, "context.pkl"), "rb") as f:
        data = pickle.load(f)

    # loading image
    ct = sitk.ReadImage(data["ct_path"]) if data["ct_path"] else None
    fluoro = sitk.ReadImage(data["fluoro_path"]) if data["fluoro_path"] else None
    segmented = sitk.ReadImage(data["segmented_path"]) if data["segmented_path"] else None

    # set singleton patient
    singleton_patient = SingletonPatient.get_instance(
        name=data["name"],
        age=data["age"],
        CT=ct,
        fluroscopy=fluoro,
        segmentedCT=segmented
    )

    # loading state class
    state_class = globals()[data["state_class"]]
    state_instance = state_class()


    # loading context
    context = Context(state=state_instance, patient=singleton_patient, data["description"])
    return context


def load_ct(ct_source: str) -> sitk.Image:
    """Load either a NIfTI file or a DICOM series folder into a SimpleITK Image."""
    if os.path.isdir(ct_source):
        reader = sitk.ImageSeriesReader()
        series_ids = reader.GetGDCMSeriesIDs(ct_source)
        if not series_ids:
            raise RuntimeError(f"No DICOM series found in {ct_source}")
        # pick the first series
        file_names = reader.GetGDCMSeriesFileNames(ct_source, series_ids[0])
        reader.SetFileNames(file_names)
        return reader.Execute()
    else:
        return sitk.ReadImage(ct_source)