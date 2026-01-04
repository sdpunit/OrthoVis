import os


def find_dicom_directory(self, base_dir):
    """Find directory containing DICOM files"""
    if contains_dicom(base_dir):
        return base_dir
        
    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and contains_dicom(item_path):
                return item_path
    except Exception as e:
        print(f"Error searching for DICOM files: {e}")
        
    return None

def contains_dicom(directory: str) -> bool:
    try:
        return any('.' not in f or f.endswith('.dcm') for f in os.listdir(directory))
    except:
        return False
